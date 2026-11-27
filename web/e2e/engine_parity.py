# SPDX-License-Identifier: AGPL-3.0-or-later
"""The browser engine (web/lib/engine, Swiss Ephemeris as WebAssembly) against the
Python engine behind the API (M3.5: "results equal the API's").

    python web/e2e/engine_parity.py [--random N]

Cases: the golden charts, random births (1800-2100, latitudes within +/-60) and a
birth stepped every 7 seconds over 40 minutes, as the slider does. Every field of
/v1/chart (all 23 vargas) and the running Vimshottari periods must agree: signs,
houses, vargas, nakshatras, names and lords exactly; longitudes, speeds and Julian
days within 1e-9 (degrees or days); period dates within a millisecond.
Needs Node 22.6 or newer (runs the TypeScript directly).
"""

from __future__ import annotations

import argparse
import json
import random
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tests" / "golden"))

from jyotishnet_api.main import _iso  # noqa: E402
from jyotishnet_engine import DEFAULT_CONFIG, BirthData, build_chart  # noqa: E402
from jyotishnet_engine.boundaries import boundary_map  # noqa: E402
from jyotishnet_engine.constants import ALL_VARGAS  # noqa: E402
from jyotishnet_engine.dasha import running, vimshottari  # noqa: E402

FLOAT_TOL = 1e-9
MS = 1.0 / 86400000


def cases(n_random: int) -> list[tuple[str, BirthData, float]]:
    from jhora_parser import load_all
    out = []
    for c in load_all():
        if abs(c.latitude) > 66:
            continue
        b = BirthData(c.local, c.latitude, c.longitude, utc_offset_hours=c.utc_offset_hours,
                      altitude_m=c.altitude_m)
        out.append((f"golden {c.name}", b, b.jd_ut() + 365.25 * 30))
    rnd = random.Random(20261127)
    for i in range(n_random):
        local = datetime(1800, 1, 1) + timedelta(seconds=rnd.randrange(0, 300 * 365 * 86400))
        b = BirthData(local, round(rnd.uniform(-60, 60), 4), round(rnd.uniform(-180, 180), 4),
                      utc_offset_hours=rnd.choice([0, 5.5, -5, 9, 1, -3.5, 5.75, 8]),
                      altitude_m=rnd.choice([0, 0, 250, 1600]))
        out.append((f"random {i}", b, b.jd_ut() + rnd.uniform(-1, 110) * 365.25))
    base = BirthData(datetime(1985, 7, 21, 5, 40, 0), 19.076, 72.8777, utc_offset_hours=5.5)
    for k in range(0, 40 * 60, 7):
        b = base.shifted(k / 60)
        out.append((f"sweep +{k}s", b, b.jd_ut() + 12000))
    return out


def birth_json(b: BirthData) -> dict:
    return {"local_datetime": b.local_datetime.isoformat(), "latitude": b.latitude,
            "longitude": b.longitude, "utc_offset_hours": b.utc_offset_hours,
            "altitude_m": b.altitude_m}


def compare(a, b, path: str, errors: list[str]) -> None:
    if isinstance(a, dict) and isinstance(b, dict):
        if set(a) != set(b):
            errors.append(f"{path}: keys {sorted(set(a) ^ set(b))}")
        for k in set(a) & set(b):
            compare(a[k], b[k], f"{path}.{k}", errors)
    elif isinstance(a, list) and isinstance(b, list):
        if len(a) != len(b):
            errors.append(f"{path}: length {len(a)} != {len(b)}")
        for i, (x, y) in enumerate(zip(a, b)):
            compare(x, y, f"{path}[{i}]", errors)
    elif isinstance(a, float) or isinstance(b, float):
        if not (isinstance(a, (int, float)) and isinstance(b, (int, float))
                and abs(a - b) <= FLOAT_TOL * max(1.0, abs(a) / 1e6)):
            errors.append(f"{path}: {a!r} != {b!r}")
    elif a != b:
        errors.append(f"{path}: {a!r} != {b!r}")


def iso_close(a: str, b: str) -> bool:
    ta = datetime.fromisoformat(a)
    tb = datetime.fromisoformat(b)
    return abs((ta - tb).total_seconds()) <= 0.001


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--random", type=int, default=300)
    args = ap.parse_args()
    cs = cases(args.random)
    payload = [{"birth": birth_json(b), "vargas": ALL_VARGAS, "at_jd": at} for _, b, at in cs]
    # The ribbon's boundary scan (2 h window, 10 s steps), as the web app calls it.
    scanned = set(range(0, len(cs), max(1, len(cs) // 12)))
    for i in scanned:
        payload[i]["bounds"] = [120, 10, [1, 9 if i % 2 else 60]]
    proc = subprocess.run(
        ["node", "--disable-warning=MODULE_TYPELESS_PACKAGE_JSON", str(ROOT / "web/lib/engine/cli.ts")],
        input=json.dumps(payload), capture_output=True, text=True, check=True)
    results = json.loads(proc.stdout)

    failures = 0
    compared_changes = 0
    for i, ((name, b, at), got) in enumerate(zip(cs, results)):
        errors: list[str] = []
        if "error" in got:
            errors.append(got["error"])
        else:
            c = build_chart(b, DEFAULT_CONFIG, ALL_VARGAS)
            want = json.loads(json.dumps(c.to_dict()))
            want["sunrise_utc"] = _iso(c.sunrise_jd)
            want["warnings"] = []
            compare(got["chart"], want, "chart", errors)
            periods = vimshottari(c.grahas["Mo"].longitude, c.jd_ut, DEFAULT_CONFIG, levels=3)
            run = [{"lord": p.lord, "level": p.level, "start": _iso(p.start_jd), "end": _iso(p.end_jd)}
                   for p in running(periods, at)]
            mine = got["running"]
            if [(p["lord"], p["level"]) for p in mine] != [(p["lord"], p["level"]) for p in run]:
                errors.append(f"running: {mine} != {run}")
            else:
                for x, y in zip(mine, run):
                    if not (iso_close(x["start"], y["start"]) and iso_close(x["end"], y["end"])):
                        errors.append(f"running dates: {x} != {y}")
        if i in scanned and "changes" in got:
            window, step, vs = payload[i]["bounds"]
            ch, _ = boundary_map(b, window, step, cfg=DEFAULT_CONFIG, vargas=vs)
            want_ch = [{"key": c.key, "offset_min": round(c.offset_min, 4), "before": c.before,
                        "after": c.after, "utc": _iso(c.jd_ut)} for c in ch]
            want_ch = json.loads(json.dumps(want_ch))
            mine_ch = [{k: v for k, v in c.items() if k != "utc"} for c in got["changes"]]
            if mine_ch != [{k: v for k, v in c.items() if k != "utc"} for c in want_ch]:
                errors.append(f"boundaries: {len(mine_ch)} changes != {len(want_ch)}")
            elif not all(iso_close(x["utc"], y["utc"]) for x, y in zip(got["changes"], want_ch)):
                errors.append("boundaries: times differ")
            compared_changes += len(mine_ch)
        if errors:
            failures += 1
            print(f"FAIL {name}: " + "; ".join(errors[:6]) + (f" (+{len(errors) - 6})" if len(errors) > 6 else ""))
    print(f"{len(cs) - failures}/{len(cs)} cases equal ({len(scanned)} boundary scans, {compared_changes} changes)")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())

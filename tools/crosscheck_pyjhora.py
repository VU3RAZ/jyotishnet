# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Rahul Sathe
"""Cross-check JyotishNet Layer 0 against PyJHora on random charts.

PyJHora (AGPL-3.0) is used only as an external test oracle, never imported by
the engine. Install it in a separate environment:

    python -m venv --system-site-packages .venv-oracle
    .venv-oracle/bin/pip install --no-deps pyjhora
    .venv-oracle/bin/pip install pytz numpy python-dateutil requests geopy \
        timezonefinder geocoder reverse_geocode img2pdf

Run:
    .venv-oracle/bin/python tools/crosscheck_pyjhora.py --charts 500

Reports disagreement per varga and per point. A disagreement within
`--edge-tol` degrees of a division boundary is counted separately, because
sub-arcsecond ephemeris differences can legitimately flip a sign there.
"""

from __future__ import annotations

import argparse
import contextlib
import io
import os
import random
import sys
from collections import Counter
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from jyotishnet_engine import BirthData, NodeType, SchoolConfig, build_chart  # noqa: E402
from jyotishnet_engine.constants import GRAHAS, SHODASHAVARGA  # noqa: E402

with contextlib.redirect_stdout(io.StringIO()):
    from jhora import utils  # noqa: E402
    from jhora.horoscope.chart import charts  # noqa: E402
    from jhora.panchanga import drik  # noqa: E402

drik.set_ayanamsa_mode("LAHIRI")

CITIES = [
    ("New Delhi", 28.61, 77.21), ("Mumbai", 19.08, 72.88), ("Chennai", 13.08, 80.27),
    ("Kolkata", 22.57, 88.36), ("Bengaluru", 12.97, 77.59), ("Srinagar", 34.08, 74.80),
    ("Guwahati", 26.14, 91.74), ("Thiruvananthapuram", 8.52, 76.94),
]


def near_edge(lon: float, n: int, tol: float) -> bool:
    if n == 30:
        within = lon % 30
        edges = [0, 5, 10, 12, 18, 20, 25, 30]
        return any(abs(within - e) < tol for e in edges)
    size = 30.0 / n
    r = (lon % 30) % size
    return r < tol or size - r < tol


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--charts", type=int, default=200)
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--edge-tol", type=float, default=0.002)
    ap.add_argument("--nodes", choices=["mean", "true"], default="true",
                    help="PyJHora defaults to true nodes; the engine defaults to mean")
    args = ap.parse_args()
    # PyJHora uses true (geometric) positions: FLG_TRUEPOS.
    cfg = SchoolConfig(node_type=NodeType(args.nodes), true_positions=True)
    drik.set_planet_list(set_rahu_ketu_as_true_nodes=(args.nodes == "true"))
    rng = random.Random(args.seed)

    hard = Counter()
    edge = Counter()
    checks = 0
    examples = []
    for _ in range(args.charts):
        name, lat, lon = rng.choice(CITIES)
        dt = datetime(rng.randint(1900, 2030), rng.randint(1, 12), rng.randint(1, 28),
                      rng.randint(0, 23), rng.randint(0, 59), rng.randint(0, 59))
        ours = build_chart(BirthData(dt, lat, lon, utc_offset_hours=5.5), cfg, vargas=SHODASHAVARGA)
        place = drik.Place(name, lat, lon, 5.5)
        jd = utils.julian_day_number((dt.year, dt.month, dt.day), (dt.hour, dt.minute, dt.second))
        for n in SHODASHAVARGA:
            with contextlib.redirect_stdout(io.StringIO()):
                # D2: PyJHora method 1 = Uma-Shambhu (parivritti, even signs reversed),
                # the engine's and Jagannatha Hora's default.
                theirs = charts.divisional_chart(jd, place, n, chart_method=1 if n == 2 else None)
            for item in theirs:
                key, (sign, _) = item[0], item[1]
                code = "La" if key == "L" else GRAHAS[key]
                point = ours.lagna if code == "La" else ours.grahas[code]
                mine = point.vargas[n]
                checks += 1
                if mine != sign:
                    bucket = edge if near_edge(point.longitude, n, args.edge_tol) else hard
                    bucket[(n, code)] += 1
                    if bucket is hard and len(examples) < 10:
                        examples.append((dt.isoformat(), name, n, code, round(point.longitude, 5), mine, sign))

    print(f"checked {checks} placements across {args.charts} charts")
    print(f"hard mismatches: {sum(hard.values())}   near-boundary mismatches: {sum(edge.values())}")
    for (n, code), k in sorted(hard.items()):
        print(f"  D{n:<3} {code}: {k}")
    for e in examples:
        print("  example:", e)
    return 1 if hard else 0


if __name__ == "__main__":
    raise SystemExit(main())

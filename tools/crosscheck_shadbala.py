# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Rahul Sathe
"""Cross-check the Shadbala components where PyJHora 5.x follows BPHS.

Strictly checked: Uchcha, Tribhaga and Naisargika bala, and Paksha bala when
PyJHora's value lies inside BPHS's 0-60 range (0-120 for the Moon).

Reported, not checked (observed in PyJHora 5.0.6):
- Dig bala: PyJHora often returns 120 minus the BPHS value (above the 60 maximum).
- Paksha bala: for a waning Moon PyJHora returns negative or >60 values.
- Drik bala: depends on benefic/malefic classification of Moon and Mercury,
  which differs between the two; reported for information.
- Cheshta: PyJHora's function fails, and it sets Sun/Moon cheshta to 0.
- Vara/Hora/Abda/Masa: PyJHora's weekday lord differs from the civil weekday.
- Ayana: PyJHora uses kranti tables; the engine uses ephemeris declination.
"""

from __future__ import annotations

import argparse
import contextlib
import io
import os
import random
import sys
from collections import Counter

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from jyotishnet_engine import NodeType, SchoolConfig, build_chart  # noqa: E402
from jyotishnet_engine.ephemeris import previous_sunrise, sun_event_after  # noqa: E402
from jyotishnet_engine.shadbala import PLANETS7, ShadbalaOptions, shadbala  # noqa: E402
from sampling import add_arguments, sample  # noqa: E402

with contextlib.redirect_stdout(io.StringIO()):
    from jhora import utils  # noqa: E402
    from jhora.horoscope.chart import charts  # noqa: E402
    from jhora.horoscope.chart import strength as st  # noqa: E402
    from jhora.panchanga import drik  # noqa: E402

drik.set_ayanamsa_mode("LAHIRI")
drik.set_planet_list(set_rahu_ketu_as_true_nodes=True)
CFG = SchoolConfig(node_type=NodeType.TRUE, true_positions=True)
# PyJHora treats the Moon as benefic when waxing; the engine's default follows
# Jagannatha Hora's Ashtami rule. Compare like with like.
OPTS = ShadbalaOptions(moon_benefic="waxing")
TOL = 0.1
# Sunrise and sunset differ between the programs by seconds (more at high
# latitudes), so a birth this close to a third of the day or night is noise.
TRIBHAGA_EDGE_MIN = 3.0


def tribhaga_margin_minutes(b) -> float:
    """Minutes from the birth to the nearest boundary between thirds of the day or night."""
    jd = b.jd_ut()
    rise = previous_sunrise(jd, b.latitude, b.longitude, b.altitude_m, CFG)
    sset = sun_event_after(rise, b.latitude, b.longitude, b.altitude_m, CFG, "set")
    nxt = sun_event_after(rise + 0.01, b.latitude, b.longitude, b.altitude_m, CFG, "rise")
    a, z = (rise, sset) if jd < sset else (sset, nxt)
    return min(abs(jd - (a + (z - a) * k / 3)) for k in range(4)) * 1440


def main() -> int:
    ap = argparse.ArgumentParser()
    add_arguments(ap, charts=100, seed=5)
    args = ap.parse_args()
    rng = random.Random(args.seed)
    bad = Counter()
    info = Counter()
    out_of_range = Counter()
    near_edge = Counter()
    n = 0
    for _ in range(args.charts):
        smp = sample(rng, args.sample, years=(1950, 2030))
        b = smp.birth()
        ours = shadbala(build_chart(b, CFG, [1, 2, 3, 7, 9, 12, 30]), b, CFG, OPTS)
        place = drik.Place("x", smp.lat, smp.lon, smp.tz)
        jd = utils.julian_day_number(smp.ymd(), smp.hms())
        tribhaga_edge = tribhaga_margin_minutes(b) < TRIBHAGA_EDGE_MIN
        with contextlib.redirect_stdout(io.StringIO()):
            theirs = {
                "uchcha": st._uchcha_bala(charts.rasi_chart(jd, place)),
                "paksha": st._paksha_bala(jd, place),
                "tribhaga": st._tribhaga_bala(jd, place),
                "naisargika": st._naisargika_bala(),
                "drik": st._drik_bala(jd, place),
                "dig": st._dig_bala(jd, place),
            }
        n += 1
        for i, p in enumerate(PLANETS7):
            s = ours[p]
            mine = {"uchcha": s.sthana["uchcha"], "paksha": s.kala["paksha"],
                    "tribhaga": s.kala["tribhaga"], "naisargika": s.naisargika,
                    "drik": s.drik, "dig": s.dig}
            for k, v in mine.items():
                t = theirs[k][i]
                hi = 120 if (k == "paksha" and p == "Mo") else 60
                if k in ("dig", "paksha") and not (-1e-9 <= t <= hi + 1e-9):
                    out_of_range[k] += 1
                    continue
                if abs(v - t) <= TOL:
                    continue
                # Mercury's benefic/malefic status is a school choice: informational.
                if k in ("dig", "drik") or (k == "paksha" and p == "Me"):
                    info[(k, p)] += 1
                elif k == "tribhaga" and tribhaga_edge:
                    near_edge[k] += 1
                else:
                    bad[(k, p)] += 1
                assert (k == "paksha" or 0 <= v <= hi or k == "drik"), (k, p, v)
    print(f"charts: {n}")
    print(f"PyJHora values outside BPHS range (skipped): {dict(out_of_range)}")
    print(f"births within {TRIBHAGA_EDGE_MIN:g} min of a tribhaga boundary (skipped): {dict(near_edge)}")
    print(f"informational differences (dig, drik, Mercury paksha): {sum(info.values())}")
    print(f"strict mismatches beyond {TOL} virupa:")
    for k, v in sorted(bad.items()):
        print("  ", k, v)
    if not bad:
        print("  none")
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())

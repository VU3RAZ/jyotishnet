# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Rahul Sathe
"""Compare Ashtottari (and later other) dashas with PyJHora on random charts.

Checks the sequence of maha and antar lords and their start dates. Run in the
PyJHora environment (see crosscheck_pyjhora.py).
"""

from __future__ import annotations

import argparse
import contextlib
import io
import os
import random
import sys
from datetime import datetime, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from jyotishnet_engine import BirthData, SchoolConfig, build_chart  # noqa: E402
from jyotishnet_engine.dasha import ashtottari  # noqa: E402

with contextlib.redirect_stdout(io.StringIO()):
    from jhora import const, utils  # noqa: E402
    from jhora.horoscope.dhasa.graha import ashtottari as j_ash  # noqa: E402
    from jhora.panchanga import drik  # noqa: E402

drik.set_ayanamsa_mode("LAHIRI")
PID = {0: "Su", 1: "Mo", 2: "Ma", 3: "Me", 4: "Ju", 5: "Ve", 6: "Sa", 7: "Ra", 8: "Ke"}


def flatten(periods):
    for md in periods:
        for ad in md.children:
            yield (md.lord, ad.lord), ad.start_jd


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--charts", type=int, default=100)
    ap.add_argument("--seed", type=int, default=5)
    ap.add_argument("--tol-days", type=float, default=2.0)
    ap.add_argument("--year", default="solar", choices=["solar", "fixed"])
    args = ap.parse_args()
    rng = random.Random(args.seed)
    cfg = SchoolConfig(dasha_year_mode=args.year, dasha_year_days=365.256363)
    worst, seq_bad, n = 0.0, 0, 0
    for _ in range(args.charts):
        dt = datetime(rng.randint(1900, 2030), rng.randint(1, 12), rng.randint(1, 28),
                      rng.randint(0, 23), rng.randint(0, 59))
        lat, lon, tz = 28.61, 77.21, 5.5
        c = build_chart(BirthData(dt, lat, lon, utc_offset_hours=tz), cfg, [1])
        ours = list(flatten(ashtottari(c.grahas["Mo"].longitude, c.jd_ut, cfg, levels=2)))
        with contextlib.redirect_stdout(io.StringIO()):
            rows = j_ash.get_dhasa_antardhasa((dt.year, dt.month, dt.day), (dt.hour, dt.minute, 0),
                                              drik.Place("x", lat, lon, tz),
                                              return_exact_bounds=True)
        theirs = [((PID[r[0][0]], PID[r[0][1]]), r[1] - tz / 24.0) for r in rows]
        # Align on the first common (maha, antar) key.
        keys = [k for k, _ in theirs]
        try:
            off = keys.index(ours[0][0])
        except ValueError:
            seq_bad += 1
            continue
        for (ko, jo), (kt, jt) in zip(ours, theirs[off:]):
            n += 1
            if ko != kt:
                seq_bad += 1
                break
            worst = max(worst, abs(jo - jt))
    print(f"Ashtottari: {args.charts} charts, {n} antardashas compared, "
          f"sequence mismatches {seq_bad}, worst start difference {worst:.3f} days")
    return 0 if seq_bad == 0 and worst <= args.tol_days else 1


if __name__ == "__main__":
    raise SystemExit(main())

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
from datetime import timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from jyotishnet_engine import SchoolConfig, build_chart  # noqa: E402
from jyotishnet_engine.dasha import ashtottari  # noqa: E402
from jyotishnet_engine.jaimini import chara_dasha, stronger_co_lord  # noqa: E402
from sampling import add_arguments, sample  # noqa: E402

with contextlib.redirect_stdout(io.StringIO()):
    from jhora import const, utils  # noqa: E402
    from jhora.horoscope.dhasa.graha import ashtottari as j_ash  # noqa: E402
    from jhora.horoscope.dhasa.raasi import chara as j_chara  # noqa: E402
    from jhora.panchanga import drik  # noqa: E402

drik.set_ayanamsa_mode("LAHIRI")
drik.set_planet_list(set_rahu_ketu_as_true_nodes=False)
PID = {0: "Su", 1: "Mo", 2: "Ma", 3: "Me", 4: "Ju", 5: "Ve", 6: "Sa", 7: "Ra", 8: "Ke"}


def flatten(periods):
    for md in periods:
        for ad in md.children:
            yield (md.lord, ad.lord), ad.start_jd


def main() -> int:
    ap = argparse.ArgumentParser()
    add_arguments(ap, charts=100, seed=5)
    ap.add_argument("--tol-days", type=float, default=2.0)
    ap.add_argument("--year", default="solar", choices=["solar", "fixed"])
    args = ap.parse_args()
    rng = random.Random(args.seed)
    cfg = SchoolConfig(dasha_year_mode=args.year, dasha_year_days=365.256363)
    worst, seq_bad, n = 0.0, 0, 0
    for _ in range(args.charts):
        s = sample(rng, args.sample)
        dt, lat, lon, tz = s.local, s.lat, s.lon, s.tz
        c = build_chart(s.birth(), cfg, [1])
        ours = list(flatten(ashtottari(c.grahas["Mo"].longitude, c.jd_ut, cfg, levels=2)))
        with contextlib.redirect_stdout(io.StringIO()):
            rows = j_ash.get_dhasa_antardhasa((dt.year, dt.month, dt.day), (dt.hour, dt.minute, dt.second),
                                              drik.Place("x", lat, lon, tz),
                                              return_exact_bounds=True)
        theirs = [((PID[r[0][0]], PID[r[0][1]]), r[1] - tz / 24.0) for r in rows]
        # Align on the first of our periods that PyJHora also lists at about the
        # same time. With the Moon on a nakshatra boundary one list can start with
        # a dasha that has almost no balance left while the other starts with the
        # next; matching by key alone then lands a whole 108-year cycle away.
        start = next(((j, i) for j, (ko, jo) in enumerate(ours[:16])
                      for i, (kt, jt) in enumerate(theirs) if ko == kt and abs(jo - jt) < 30), None)
        if start is None:
            seq_bad += 1
            continue
        first, off = start
        ours = ours[first:]
        for (ko, jo), (kt, jt) in zip(ours, theirs[off:]):
            n += 1
            if ko != kt:
                seq_bad += 1
                break
            worst = max(worst, abs(jo - jt))
    print(f"Ashtottari: {args.charts} charts, {n} antardashas compared, "
          f"sequence mismatches {seq_bad}, worst start difference {worst:.3f} days")
    ok = seq_bad == 0 and worst <= args.tol_days

    # Chara dasha (K. N. Rao), first cycle, with K. N. Rao's book rules as PyJHora
    # (our default follows JHora 8.0 instead; see DECISIONS #3).
    from dataclasses import replace
    knrao_cfg = replace(cfg, chara_exaltation_adjust=True, chara_co_lord_rule="knrao")
    rng = random.Random(args.seed + 1)
    md_bad, ad_bad, colord_charts, n_md = 0, 0, 0, 0
    worst = 0.0
    for _ in range(args.charts):
        s = sample(rng, args.sample)
        dt, lat, lon, tz = s.local, s.lat, s.lon, s.tz
        c = build_chart(s.birth(), cfg, [1])
        signs = {k: p.sign for k, p in c.grahas.items()}
        degs = {k: p.longitude for k, p in c.grahas.items()}
        ours = chara_dasha(c.lagna.sign, signs, degs, c.jd_ut, knrao_cfg, cycles=1)
        with contextlib.redirect_stdout(io.StringIO()):
            rows = j_chara.get_dhasa_antardhasa((dt.year, dt.month, dt.day), (dt.hour, dt.minute, dt.second),
                                                drik.Place("x", lat, lon, tz),
                                                chara_method=const.CHARA_TYPE.KN_RAO,
                                                return_exact_bounds=True)
        theirs_md, seen = [], set()
        for r in rows:
            if r[0][0] not in seen:
                seen.add(r[0][0])
                theirs_md.append((r[0][0], r[3] if False else None))
        # Maha lengths from their antardasha rows: sum per maha sign.
        lengths = {}
        for r in rows:
            lengths[r[0][0]] = lengths.get(r[0][0], 0.0) + r[3]
        theirs = [(s, round(lengths[s], 6)) for s, _ in theirs_md]
        mine = [(int(p.lord), p.end_years - p.start_years) for p in ours]
        uses_colord = any(s in (7, 10) for s, _ in mine)
        chart_bad = False
        for (so, yo), (st, yt) in zip(mine, theirs):
            n_md += 1
            if so != st or abs(yo - yt) > 1e-3:
                md_bad += 1
                chart_bad = True
        colord_charts += chart_bad and uses_colord
        for md, (st, _) in zip(ours, theirs):
            want = [r[0][1] for r in rows if r[0][0] == st]
            if [int(ch.lord) for ch in md.children] != want:
                ad_bad += 1
        for md in ours:
            r0 = next(r for r in rows if r[0][0] == int(md.lord))
            worst = max(worst, abs(md.start_jd - (r0[1] - tz / 24.0)))
    print(f"Chara (K. N. Rao): {args.charts} charts, {n_md} mahadashas, "
          f"length/sign mismatches {md_bad}, "
          f"antardasha order mismatches {ad_bad}, worst maha start difference {worst:.2f} days")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())

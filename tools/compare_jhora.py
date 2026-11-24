# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Rahul Sathe
"""Compare the engine with the Jagannatha Hora golden charts under candidate settings.

    python tools/compare_jhora.py
"""

from __future__ import annotations

import os
import sys
from itertools import product

ROOT = os.path.join(os.path.dirname(__file__), "..")
sys.path.insert(0, os.path.join(ROOT, "src"))
sys.path.insert(0, os.path.join(ROOT, "tests", "golden"))

from jhora_parser import load_all  # noqa: E402

from jyotishnet_engine import BirthData, NodeType, SchoolConfig, build_chart  # noqa: E402
from jyotishnet_engine.config import Ayanamsa, SunriseMode  # noqa: E402
from jyotishnet_engine.timeutil import jd_to_datetime  # noqa: E402
from jyotishnet_engine.dasha import vimshottari  # noqa: E402

CHARTS = load_all()
PLANETS = ["Su", "Mo", "Ma", "Me", "Ju", "Ve", "Sa"]


def arcdiff(a: float, b: float) -> float:
    return abs((a - b + 180) % 360 - 180) * 3600


def birth(c) -> BirthData:
    return BirthData(c.local, c.latitude, c.longitude, utc_offset_hours=c.utc_offset_hours,
                     altitude_m=c.altitude_m)


def positions_report() -> None:
    print("== Positions (max |diff| in arc-seconds over 8 charts)")
    for ay, node, truepos in product([Ayanamsa.LAHIRI, Ayanamsa.TRUE_CHITRA],
                                     [NodeType.MEAN, NodeType.TRUE], [False, True]):
        cfg = SchoolConfig(ayanamsa=ay, node_type=node, true_positions=truepos)
        worst = {"ayan": 0.0, "La": 0.0, "planets": 0.0, "nodes": 0.0}
        for c in CHARTS:
            ch = build_chart(birth(c), cfg, [1, 9])
            worst["ayan"] = max(worst["ayan"], abs(ch.ayanamsa - c.ayanamsa) * 3600)
            worst["La"] = max(worst["La"], arcdiff(ch.lagna.longitude, c.longitudes["La"]))
            for p in PLANETS:
                worst["planets"] = max(worst["planets"], arcdiff(ch.grahas[p].longitude, c.longitudes[p]))
            worst["nodes"] = max(worst["nodes"], arcdiff(ch.grahas["Ra"].longitude, c.longitudes["Ra"]))
        print(f"  {ay.value:12} nodes={node.value:4} truepos={truepos!s:5}  "
              + "  ".join(f"{k}={v:8.1f}" for k, v in worst.items()))


def special_report(cfg: SchoolConfig) -> None:
    print("== Special lagnas (max |diff| in arc-minutes), per sunrise mode")
    for mode in SunriseMode:
        cfg2 = SchoolConfig(**{**cfg.__dict__, "sunrise": mode})
        worst = {k: 0.0 for k in ("BL", "HL", "GL", "PP")}
        for c in CHARTS:
            ch = build_chart(birth(c), cfg2, [1])
            for k in worst:
                worst[k] = max(worst[k], arcdiff(ch.special[k].longitude, c.longitudes[k]) / 60)
        print(f"  {mode.value:28} " + "  ".join(f"{k}={v:8.2f}'" for k, v in worst.items()))


def navamsa_report(cfg: SchoolConfig) -> None:
    bad = 0
    total = 0
    for c in CHARTS:
        ch = build_chart(birth(c), cfg, [9])
        pts = {"La": ch.lagna, **ch.grahas}
        for k, p in pts.items():
            total += 1
            bad += p.vargas[9] != c.navamsa[k]
    print(f"== Navamsa signs: {total - bad}/{total} match")


def dasha_report(cfg_base: SchoolConfig) -> None:
    print("== Vimshottari antardasha start dates (max |diff| in days), per year length")
    for days in (360.0, 365.25, 365.2422, 365.25636):
        cfg = SchoolConfig(**{**cfg_base.__dict__, "dasha_year_days": days})
        worst = 0.0
        for c in CHARTS:
            ch = build_chart(birth(c), cfg, [1])
            mds = vimshottari(ch.grahas["Mo"].longitude, ch.jd_ut, cfg, levels=2)
            ours = [(md.lord, ad.lord, jd_to_datetime(ad.start_jd + c.utc_offset_hours / 24).date())
                    for md in mds for ad in md.children]
            for want in c.vimshottari:
                got = next((g for g in ours if g[0] == want[0] and g[1] == want[1]
                            and abs((g[2] - want[2]).days) < 400), None)
                if got is None:
                    worst = float("inf")
                    continue
                worst = max(worst, abs((got[2] - want[2]).days))
        print(f"  year = {days:9.5f} days: {worst}")


if __name__ == "__main__":
    positions_report()
    base = SchoolConfig(ayanamsa=Ayanamsa.LAHIRI, node_type=NodeType.MEAN)
    special_report(base)
    navamsa_report(base)
    dasha_report(base)

# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Rahul Sathe
"""Cross-check Ashtakavarga (BAV, SAV, reductions, Shodhya pinda) against PyJHora.

Same setup as tools/crosscheck_pyjhora.py (PyJHora in a separate environment).
    .venv-oracle/bin/python tools/crosscheck_ashtakavarga.py --charts 300
"""

from __future__ import annotations

import argparse
import contextlib
import copy
import io
import os
import random
import sys
from collections import Counter
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from jyotishnet_engine import BirthData, NodeType, SchoolConfig, build_chart  # noqa: E402
from jyotishnet_engine.ashtakavarga import PLANETS7, ashtakavarga  # noqa: E402

with contextlib.redirect_stdout(io.StringIO()):
    from jhora import const, utils  # noqa: E402
    from jhora.horoscope.chart import ashtakavarga as jav  # noqa: E402
    from jhora.horoscope.chart import charts  # noqa: E402
    from jhora.panchanga import drik  # noqa: E402

drik.set_ayanamsa_mode("LAHIRI")
drik.set_planet_list(set_rahu_ketu_as_true_nodes=True)
CFG = SchoolConfig(node_type=NodeType.TRUE, true_positions=True)
CITIES = [(28.61, 77.21), (19.08, 72.88), (13.08, 80.27), (22.57, 88.36), (34.08, 74.80)]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--charts", type=int, default=200)
    ap.add_argument("--seed", type=int, default=3)
    args = ap.parse_args()
    rng = random.Random(args.seed)
    virgo = const.ashtakavarga_rasimana_multipliers[5] if hasattr(const, "ashtakavarga_rasimana_multipliers") else 5

    bad = Counter()
    examples = []
    for _ in range(args.charts):
        lat, lon = rng.choice(CITIES)
        dt = datetime(rng.randint(1900, 2030), rng.randint(1, 12), rng.randint(1, 28),
                      rng.randint(0, 23), rng.randint(0, 59))
        ours = ashtakavarga(build_chart(BirthData(dt, lat, lon, utc_offset_hours=5.5), CFG, [1]),
                            variant="pvr", virgo_multiplier=virgo, occupancy="all")
        place = drik.Place("x", lat, lon, 5.5)
        jd = utils.julian_day_number((dt.year, dt.month, dt.day), (dt.hour, dt.minute, 0))
        with contextlib.redirect_stdout(io.StringIO()):
            pp = charts.divisional_chart(jd, place, 1)
            h2p = utils.get_house_planet_list_from_planet_positions(pp)
            # PyJHora's reductions modify their input lists in place: pass copies.
            bav, sav, _ = jav.get_ashtaka_varga(h2p)
            bav, sav = copy.deepcopy(bav), list(sav)
            trik = jav._trikona_sodhana(copy.deepcopy(bav))
            eka = jav._ekadhipatya_sodhana(copy.deepcopy(trik), h2p)
            _, _, shod = jav.sodhaya_pindas(copy.deepcopy(bav), h2p)
        for i, g in enumerate(PLANETS7):
            for name, mine, theirs in (("bav", ours.bav[g], bav[i]), ("trikona", ours.bav_trikona[g], trik[i]),
                                       ("ekadhipatya", ours.bav_reduced[g], eka[i])):
                if list(mine) != list(theirs):
                    bad[(name, g)] += 1
                    if len(examples) < 6:
                        examples.append((name, g, dt.isoformat(), mine, list(theirs)))
            if ours.shodhya_pinda[g] != shod[i]:
                bad[("shodhya", g)] += 1
        if ours.sav != list(sav):
            bad[("sav", "-")] += 1

    print(f"charts: {args.charts}; mismatching (component, graha) counts:")
    for k, v in sorted(bad.items()):
        print("  ", k, v)
    for e in examples:
        print("  example:", e)
    if not bad:
        print("  none: all components match")
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())

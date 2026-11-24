# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Rahul Sathe
"""Compare yoga detection with PyJHora (PVR Narasimha Rao's definitions) on random charts.

Reports agreement per yoga. Disagreement usually means a different textual
definition, which is listed in the rule's notes after review; it is not a test
failure by itself. Run in the PyJHora environment (see crosscheck_pyjhora.py).
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
from jyotishnet_engine.yogas import find_yogas, load_rules  # noqa: E402

with contextlib.redirect_stdout(io.StringIO()):
    from jhora import utils  # noqa: E402
    from jhora.horoscope.chart import charts  # noqa: E402
    from jhora.horoscope.chart import yoga as jy  # noqa: E402
    from jhora.panchanga import drik  # noqa: E402

drik.set_ayanamsa_mode("LAHIRI")
drik.set_planet_list(set_rahu_ketu_as_true_nodes=True)
CFG = SchoolConfig(node_type=NodeType.TRUE, true_positions=True)

MAP = {
    "vesi": "vesi", "vosi": "vosi", "ubhayachari": "ubhayachara", "budha_aditya": "nipuna",
    "sunapha": "sunaphaa", "anapha": "anaphaa", "durudhara": "duradhara",
    "kemadruma": "kemadruma", "chandra_mangala": "chandra_mangala", "adhi": "adhi",
    "gajakesari": "gaja_kesari", "ruchaka": "ruchaka", "bhadra": "bhadra", "hamsa": "hamsa",
    "malavya": "maalavya", "sasa": "sasa", "rajju": "rajju", "musala": "musala", "nala": "nala",
    "mala": "maalaa", "sarpa": "sarpa", "gada": "gadaa", "shakata_akriti": "sakata",
    "vihaga": "vihaga", "shringataka": "sringaataka", "hala": "hala", "kamala": "kamala",
    "vapi": "vaapi", "vallaki": "veenaa", "damini": "daama", "pasha": "paasa",
    "kedara": "kedaara", "shoola": "soola", "amala": "amala", "parvata": "parvata",
    "kahala": "kaahala", "lakshmi": "lakshmi", "saraswati": "saraswathi",
}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--charts", type=int, default=300)
    ap.add_argument("--seed", type=int, default=21)
    args = ap.parse_args()
    rng = random.Random(args.seed)
    rules = load_rules()
    agree, ours_only, theirs_only = Counter(), Counter(), Counter()
    for _ in range(args.charts):
        dt = datetime(rng.randint(1900, 2030), rng.randint(1, 12), rng.randint(1, 28),
                      rng.randint(0, 23), rng.randint(0, 59))
        lat, lon = 28.61, 77.21
        found = {y.id: (y.present and not y.cancelled)
                 for y in find_yogas(build_chart(BirthData(dt, lat, lon, utc_offset_hours=5.5), CFG, [1]),
                                     rules, include_absent=True)}
        jd = utils.julian_day_number((dt.year, dt.month, dt.day), (dt.hour, dt.minute, 0))
        with contextlib.redirect_stdout(io.StringIO()):
            pp = charts.rasi_chart(jd, drik.Place("x", lat, lon, 5.5))
            for ours, theirs in MAP.items():
                t = bool(getattr(jy, f"{theirs}_yoga_from_planet_positions")(pp))
                o = found[ours]
                if o == t:
                    agree[ours] += 1
                elif o:
                    ours_only[ours] += 1
                else:
                    theirs_only[ours] += 1
    print(f"{'yoga':18} agree  ours-only  pyjhora-only   (of {args.charts} charts)")
    for k in MAP:
        print(f"{k:18} {agree[k]:5}  {ours_only[k]:9}  {theirs_only[k]:12}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

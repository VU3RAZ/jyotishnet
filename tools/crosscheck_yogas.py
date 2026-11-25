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

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from jyotishnet_engine import NodeType, SchoolConfig, build_chart  # noqa: E402
from jyotishnet_engine.yogas import YogaOptions, find_yogas, load_rules  # noqa: E402
from sampling import add_arguments, sample  # noqa: E402

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

# PyJHora arguments that pick the same textual variant as our rule: Lakshmi with a
# kendra or trikona is B. V. Raman's reading, PyJHora's method 2.
THEIRS_KW = {"lakshmi": {"method": 2}}


def main() -> int:
    ap = argparse.ArgumentParser()
    add_arguments(ap, charts=300, seed=21)
    ap.add_argument("--strong-lord", default="dignity", choices=["dignity", "shadbala"])
    ap.add_argument("--gajakesari", default="bphs", choices=["bphs", "phaladeepika"])
    args = ap.parse_args()
    opts = YogaOptions(args.strong_lord, args.gajakesari)
    rng = random.Random(args.seed)
    rules = load_rules()
    agree, ours_only, theirs_only = Counter(), Counter(), Counter()
    for _ in range(args.charts):
        s = sample(rng, args.sample)
        found = {y.id: (y.present and not y.cancelled)
                 for y in find_yogas(build_chart(s.birth(), CFG, [1]), rules, include_absent=True,
                                     options=opts, birth=s.birth(), cfg=CFG)}
        jd = utils.julian_day_number(s.ymd(), s.hms())
        with contextlib.redirect_stdout(io.StringIO()):
            pp = charts.rasi_chart(jd, drik.Place("x", s.lat, s.lon, s.tz))
            for ours, theirs in MAP.items():
                t = bool(getattr(jy, f"{theirs}_yoga_from_planet_positions")(pp, **THEIRS_KW.get(ours, {})))
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

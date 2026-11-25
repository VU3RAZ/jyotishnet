# SPDX-License-Identifier: AGPL-3.0-or-later
"""Jaimini rasi dashas against Jagannatha Hora 8.0 (Dasas tab > Rasi dasas, default
settings; tests/golden/jhora_rasi_dashas/, made by tools/import_jhora_rasi_dashas.py):
19 dashas per golden chart, the mahadasha list and the antardashas of the first two
mahadashas.

Signs and their order must match exactly. Start times (local, as JHora prints them)
within 5 s up to 2016; later dates within 5 s + 1.5 s per year after 2016, which
covers JHora's larger future Delta T (decision #22: about 48 s in 2050 and 125 s in
2100; the dasha dates move with it). Sudasa uses JHora's own Sree Lagna (exported
to 1"; ours differs by up to the special-lagna tolerance of tests/test_jhora_upagrahas.py)
and allows for that rounding: 0.5" in the Sree Lagna moves the first dasa's end by
up to 146 s per year of its length.
"""

import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent / "golden"))
from jhora_parser import parse  # noqa: E402

from jyotishnet_engine import BirthData, DEFAULT_CONFIG, build_chart  # noqa: E402
from jyotishnet_engine.jaimini import chara_dasha  # noqa: E402
from jyotishnet_engine.jaimini_jhora import RASI_DASHAS, rasi_dasha  # noqa: E402
from jyotishnet_engine.timeutil import jd_to_datetime  # noqa: E402

SIGNS = "Ar Ta Ge Cn Le Vi Li Sc Sg Cp Aq Pi".split()
GOLDEN = Path(__file__).parent / "golden"
FILES = sorted((GOLDEN / "jhora_rasi_dashas").glob("*.json"))
NAMES = sorted([*RASI_DASHAS, "chara_knrao"])
_cache: dict = {}


def _setup(name: str):
    if name not in _cache:
        c = parse(GOLDEN / "jhora" / f"{name}.txt")
        ch = build_chart(BirthData(c.local, c.latitude, c.longitude,
                                   utc_offset_hours=c.utc_offset_hours,
                                   altitude_m=c.altitude_m), DEFAULT_CONFIG, [1])
        _cache[name] = (c, ch, json.loads((GOLDEN / "jhora_rasi_dashas" / f"{name}.json").read_text()))
    return _cache[name]


def _periods(dasha: str, c, ch):
    if dasha == "chara_knrao":
        return chara_dasha(ch.lagna.sign, {k: g.sign for k, g in ch.grahas.items()},
                           {k: g.longitude for k, g in ch.grahas.items()}, ch.jd_ut,
                           DEFAULT_CONFIG)
    extra = {"SL": c.longitudes["SL"]} if dasha == "sudasa" else None
    return rasi_dasha(dasha, ch, DEFAULT_CONFIG, points=extra)


def _limit(when: datetime, slack: float) -> float:
    return 5 + slack + max(0, when.year - 2016) * 1.5


@pytest.mark.parametrize("dasha", NAMES)
@pytest.mark.parametrize("path", FILES, ids=[p.stem for p in FILES])
def test_rasi_dasha(path, dasha):
    c, ch, golden = _setup(path.stem)
    if dasha not in golden:
        pytest.skip("held in tests/golden/pending (see tests/golden/README.md)")
    g = golden[dasha]
    per = _periods(dasha, c, ch)
    local = lambda jd: jd_to_datetime(jd).replace(tzinfo=None) + timedelta(hours=c.utc_offset_hours)
    theirs = [(SIGNS.index(s), datetime.strptime(t, "%Y-%m-%d %H:%M:%S")) for s, t in g["md"]]
    mine = [(int(p.lord), local(p.start_jd)) for p in per][:len(theirs)]
    assert [SIGNS[s] for s, _ in mine] == [SIGNS[s] for s, _ in theirs]
    slack = 0.0
    if dasha == "sudasa":
        slack = 146 * (per[0].end_years - per[0].start_years)
    for (s, a), (_, b) in zip(mine, theirs):
        assert abs((a - b).total_seconds()) <= _limit(b, slack), (SIGNS[s], a, b)
    for k, ad in enumerate(g["ad"]):
        md = per[k]
        assert SIGNS[int(md.lord)] == ad["md"]
        assert [SIGNS[int(a.lord)] for a in md.children] == [s for s, _ in ad["rows"]]
        for a, (_, t) in zip(md.children, ad["rows"]):
            b = datetime.strptime(t, "%Y-%m-%d %H:%M:%S")
            assert abs((local(a.start_jd) - b).total_seconds()) <= _limit(b, slack), (ad["md"], t)

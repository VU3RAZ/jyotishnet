# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Rahul Sathe
"""Jaimini rasi drishti, co-lords and K. N. Rao's Chara dasha (signs 0 = Aries)."""

import pytest

from jyotishnet_engine.config import SchoolConfig
from jyotishnet_engine.jaimini import (
    chara_dasha, chara_years, rasi_drishti, stronger_co_lord)

FIXED = SchoolConfig(dasha_year_mode="fixed", dasha_year_days=365.25)


def test_rasi_drishti():
    assert rasi_drishti(0) == {4, 7, 10}           # Aries: Le, Sc, Aq (not Ta)
    assert rasi_drishti(1) == {3, 6, 9}            # Taurus: Cn, Li, Cp (not Ar)
    assert rasi_drishti(2) == {5, 8, 11}           # Gemini: other duals
    for s in range(12):                            # aspects are mutual
        for t in rasi_drishti(s):
            assert s in rasi_drishti(t)


def _chart(**signs):
    base = {"Su": 0, "Mo": 1, "Ma": 2, "Me": 3, "Ju": 4, "Ve": 5, "Sa": 6, "Ra": 9, "Ke": 3}
    base.update(signs)
    degs = {k: s * 30 + 15.0 for k, s in base.items()}
    return base, degs


def test_co_lord_other_occupies():
    signs, degs = _chart(Sa=10, Ra=2, Ke=8)
    assert stronger_co_lord(10, signs, degs, 0) == ("Ra", "other lord occupies the sign")


def test_co_lord_more_company():
    signs, degs = _chart(Sa=4, Ra=6, Ke=0)          # Saturn joins Jupiter in Leo; Rahu alone in Libra
    lord, why = stronger_co_lord(10, signs, degs, 11)
    assert lord == "Sa" and why == "more planets in its sign"


def test_co_lord_degrees_with_reversed_nodes():
    # Saturn alone in Leo at 15 deg, Rahu alone in Scorpio at 20 deg (= 10 deg advanced).
    signs = {"Su": 0, "Mo": 0, "Ma": 0, "Me": 0, "Ju": 0, "Ve": 0, "Sa": 4, "Ra": 7, "Ke": 1}
    degs = {k: s * 30 + 5.0 for k, s in signs.items()}
    degs["Sa"], degs["Ra"], degs["Ke"] = 4 * 30 + 15.0, 7 * 30 + 20.0, 1 * 30 + 20.0
    lord, why = stronger_co_lord(10, signs, degs, 0)
    assert (lord, why) == ("Sa", "more advanced in its sign")


def test_chara_years_debilitated_lord():
    # Aries (savya), Mars in Cancer: count Ar..Cn = 4, minus 1 = 3; debilitated -> 2.
    signs, degs = _chart(Ma=3)
    assert chara_years(0, signs, degs, 0) == 2


def test_chara_years_rules():
    signs, degs = _chart(Ve=1)                       # Venus in Taurus (own) -> 12 for Taurus
    assert chara_years(1, signs, degs, 0) == 12
    signs, degs = _chart(Mo=3)                       # Cancer is apasavya; Moon there -> 12
    assert chara_years(3, signs, degs, 0) == 12
    signs, degs = _chart(Su=0)                       # Leo apasavya: count back Le..Ar = 5 -> 4, Sun exalted -> 5
    assert chara_years(4, signs, degs, 0) == 5
    signs, degs = _chart(Me=5)                       # Gemini savya: Ge..Vi = 4 -> 3, Mercury exalted -> 4
    assert chara_years(2, signs, degs, 0) == 4


def test_chara_dasha_structure():
    signs, degs = _chart()
    # Aries lagna; 9th is Sagittarius (savya) -> forward.
    ps = chara_dasha(0, signs, degs, 2451545.0, FIXED, cycles=2)
    first12 = [int(p.lord) for p in ps[:12]]
    assert first12 == list(range(12))
    total1 = sum(p.end_years - p.start_years for p in ps[:12])
    total2 = sum(p.end_years - p.start_years for p in ps[12:])
    assert total1 + total2 == pytest.approx(12 * 12)
    for md in ps:
        assert int(md.children[-1].lord) == int(md.lord)            # ends with its own sign
        assert len(md.children) == 12
    # Cancer lagna: 9th is Pisces (apasavya) -> backward.
    ps = chara_dasha(3, signs, degs, 2451545.0, FIXED, cycles=1)
    assert [int(p.lord) for p in ps[:3]] == [3, 2, 1]
    assert ps[0].start_jd == pytest.approx(2451545.0)


def test_chara_karakas_match_jhora():
    """Eight chara karakas against the labels in JHora's body table (55 golden charts)."""
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent / "golden"))
    from jhora_parser import load_all

    from jyotishnet_engine.jaimini import chara_karakas
    charts = load_all()
    assert len(charts) == 55
    for c in charts:
        lons = {p: c.longitudes[p] for p in ("Su", "Mo", "Ma", "Me", "Ju", "Ve", "Sa", "Ra")}
        assert chara_karakas(lons) == c.karakas, c.name


def test_chara_karakas_seven():
    from jyotishnet_engine.jaimini import chara_karakas
    lons = {"Su": 29, "Mo": 1, "Ma": 2, "Me": 3, "Ju": 4, "Ve": 5, "Sa": 6, "Ra": 0.5}
    k = chara_karakas(lons, 7)
    assert k["AK"] == "Su" and k["DK"] == "Mo" and k["PiK"] == "Me"
    assert k["PK"] == k["MK"] == "Ju"                  # BPHS 32: MK also signifies children
    assert chara_karakas(lons)["AK"] == "Ra"           # Rahu at 0.5 counts as 29.5


def _dm(d: int, m: float = 30) -> float:
    return d + m / 60


# P. V. R. Narasimha Rao, "Parasara's Teachings on Chara Karakas" (2008), examples 1, 2,
# 3, 7, 8 and 12 with the degrees he prints (Rahu as he counts him, 30 deg minus his
# degree; whole degrees given as mid-degree). Our own positions for examples 2, 7 and
# 8 differ from his by 1-4' on the close calls.
PVR_KARAKA_EXAMPLES = [
    ({"Mo": _dm(26, 56), "Ve": _dm(26, 9), "Ma": _dm(21), "Me": _dm(16), "Ju": _dm(12, 54),
      "Ra": _dm(12, 28), "Su": _dm(8), "Sa": _dm(4)},
     "AK Mo AmK Ve BK Ma MK Me PK Ju GK Su DK Sa"),                       # PiK empty
    ({"Ra": _dm(27), "Mo": _dm(22, 19), "Ma": _dm(22, 18), "Me": _dm(15), "Ju": _dm(14),
      "Sa": _dm(13), "Ve": _dm(9), "Su": _dm(6)},
     "AK Ra BK Mo MK Me PiK Ju PK Sa GK Ve DK Su"),                       # AmK empty
    ({"Su": _dm(29), "Mo": _dm(17), "Sa": _dm(13), "Me": _dm(11), "Ve": _dm(7), "Ma": _dm(6),
      "Ju": _dm(4), "Ra": _dm(13)},
     "AK Su AmK Mo BK Sa MK Me PK Me PiK Ve GK Ma DK Ju"),                 # seven
    ({"Mo": _dm(29), "Ve": _dm(16), "Ra": _dm(15), "Ju": _dm(14, 10), "Sa": _dm(14, 4),
      "Me": _dm(11), "Ma": _dm(3), "Su": _dm(2)},
     "AK Mo AmK Ve BK Ra PiK Ju PK Me GK Ma DK Su"),                       # MK empty
    ({"Sa": _dm(23, 30), "Me": _dm(23, 27), "Ju": _dm(21), "Ra": _dm(13), "Ve": _dm(8),
      "Mo": _dm(5, 39), "Ma": _dm(5, 25), "Su": _dm(0)},
     "AK Sa AmK Me BK Ju MK Ra PiK Ve GK Mo DK Su"),                       # PK empty
    ({"Ve": _dm(28), "Ju": _dm(25), "Mo": _dm(23), "Su": _dm(20), "Me": _dm(16, 43),
      "Ma": _dm(16, 13), "Ra": _dm(3, 29), "Sa": _dm(3, 25)},
     "AK Ve AmK Ju BK Mo MK Su PK Me DK Ra"),                              # PiK, GK empty
]


@pytest.mark.parametrize("degrees,want", PVR_KARAKA_EXAMPLES)
def test_chara_karakas_parasara_pvr(degrees, want):
    from jyotishnet_engine.jaimini import chara_karakas
    lons = {p: (30 - d if p == "Ra" else d) for p, d in degrees.items()}
    w = want.split()
    assert chara_karakas(lons, "parasara") == dict(zip(w[::2], w[1::2]))

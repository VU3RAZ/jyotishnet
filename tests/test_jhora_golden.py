# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Rahul Sathe
"""Golden tests against Jagannatha Hora exports (tests/golden/jhora/*.txt).

JHora settings these confirm: Lahiri ayanamsa, mean nodes, true (geometric)
planet positions, sunrise at the disc centre without refraction, PVR's
Ashtakavarga variant, solar-year Vimshottari.
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent / "golden"))
from jhora_parser import load_all  # noqa: E402

from jyotishnet_engine import BirthData, DEFAULT_CONFIG, build_chart, vimshottari  # noqa: E402
from jyotishnet_engine.ashtakavarga import PLANETS7, ashtakavarga  # noqa: E402
from jyotishnet_engine.shadbala import shadbala  # noqa: E402
from jyotishnet_engine.timeutil import jd_to_datetime  # noqa: E402
from jyotishnet_engine.vimshopaka import vimshopaka  # noqa: E402

CHARTS = load_all()
IDS = [c.name for c in CHARTS]


def arcsec(a: float, b: float) -> float:
    return abs((a - b + 180) % 360 - 180) * 3600


@pytest.fixture(scope="module", params=CHARTS, ids=IDS)
def pair(request):
    c = request.param
    b = BirthData(c.local, c.latitude, c.longitude, utc_offset_hours=c.utc_offset_hours,
                  altitude_m=c.altitude_m)
    return c, b, build_chart(b, DEFAULT_CONFIG)


def test_ayanamsa(pair):
    c, _, ch = pair
    assert abs(ch.ayanamsa - c.ayanamsa) * 3600 < 1.0


def test_planets(pair):
    c, _, ch = pair
    for p in PLANETS7:
        assert arcsec(ch.grahas[p].longitude, c.longitudes[p]) < 5, p
    assert arcsec(ch.grahas["Ra"].longitude, c.longitudes["Ra"]) < 1
    assert arcsec(ch.grahas["Ke"].longitude, c.longitudes["Ke"]) < 1


def test_lagna(pair):
    c, _, ch = pair
    assert arcsec(ch.lagna.longitude, c.longitudes["La"]) < 30


def test_retrograde_flags(pair):
    c, _, ch = pair
    for p in ("Ma", "Me", "Ju", "Ve", "Sa"):
        assert ch.grahas[p].retrograde == c.retrograde[p], p


def test_special_lagnas(pair):
    # Our sunrise falls about 1 second before JHora's, which shows up in proportion
    # to each lagna's speed (Pranapada moves one sign every 6 minutes).
    c, _, ch = pair
    limits = {"BL": 0.5, "HL": 1.0, "GL": 3.0, "PP": 10.0}   # arc-minutes
    for k, lim in limits.items():
        assert arcsec(ch.special[k].longitude, c.longitudes[k]) / 60 < lim, k


def test_navamsa(pair):
    c, _, ch = pair
    pts = {"La": ch.lagna, **ch.grahas}
    for k, p in pts.items():
        assert p.vargas[9] == c.navamsa[k], k


def test_ashtakavarga_and_pindas(pair):
    c, _, ch = pair
    av = ashtakavarga(ch)
    for p in PLANETS7:
        assert av.bav[p] == c.bav[p], p
        assert (av.shodhya_pinda[p], av.rasi_pinda[p], av.graha_pinda[p]) == c.pindas[p], p


def test_vimshottari(pair):
    c, _, ch = pair
    mds = vimshottari(ch.grahas["Mo"].longitude, ch.jd_ut, DEFAULT_CONFIG, levels=2)
    ours = [(m.lord, a.lord, jd_to_datetime(a.start_jd + c.utc_offset_hours / 24).date())
            for m in mds for a in m.children]
    for md, ad, start in c.vimshottari:
        best = min((g for g in ours if (g[0], g[1]) == (md, ad)), key=lambda g: abs((g[2] - start).days))
        assert abs((best[2] - start).days) <= 1, (md, ad, start, best[2])


@pytest.mark.xfail(reason="Totals differ from JHora only by Cheshta bala (astronomical, decision "
                          "#16) plus small Ayana (#13) and Yuddha (BPHS) differences; every other "
                          "component matches (tests/test_jhora_shadbala.py)", strict=False)
def test_shadbala_totals(pair):
    c, b, ch = pair
    sb = shadbala(ch, b, DEFAULT_CONFIG)
    for p in PLANETS7:
        assert abs(sb[p].total - c.shadbala[p]) < 5, p


def test_vimshopaka(pair):
    """All four schemes for the nine grahas; JHora prints two decimals."""
    c, _, ch = pair
    ours = vimshopaka(ch, DEFAULT_CONFIG)
    assert set(c.vimshopaka) == set(ours)
    for p, schemes in c.vimshopaka.items():
        for s, v in schemes.items():
            assert abs(ours[p][s] - v) <= 0.006, (p, s, ours[p][s], v)

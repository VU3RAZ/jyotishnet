# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Rahul Sathe
import math

from hypothesis import given, strategies as st

from jyotishnet_engine.constants import SHODASHAVARGA
from jyotishnet_engine.vargas import is_vargottama, varga_longitude, varga_sign

lons = st.floats(min_value=0, max_value=359.999999, allow_nan=False)


@given(lons)
def test_every_varga_returns_a_sign(lon):
    for n in SHODASHAVARGA:
        assert 0 <= varga_sign(lon, n) <= 11


@given(lons)
def test_d1_is_the_sign(lon):
    assert varga_sign(lon, 1) == int(lon // 30)


@given(lons)
def test_navamsa_matches_continuous_formula(lon):
    # Movable/fixed/dual rule is equivalent to counting navamsas from Aries.
    assert varga_sign(lon, 9) == math.floor(lon * 9 / 30) % 12


@given(lons)
def test_varga_longitude_lands_in_varga_sign(lon):
    for n in SHODASHAVARGA:
        assert int(varga_longitude(lon, n) // 30) == varga_sign(lon, n)


def test_drekkana_aries():
    assert [varga_sign(x, 3) for x in (5, 15, 25)] == [0, 4, 8]


def test_hora_parashari():
    assert varga_sign(5, 2) == 4      # Aries (odd), first half: Sun's hora, Leo
    assert varga_sign(20, 2) == 3     # Aries, second half: Cancer
    assert varga_sign(35, 2) == 3     # Taurus (even), first half: Cancer
    assert varga_sign(50, 2) == 4


def test_trimsamsa_parts():
    # Odd sign (Aries): Mars, Saturn, Jupiter, Mercury, Venus.
    assert [varga_sign(x, 30) for x in (2, 7, 15, 20, 27)] == [0, 10, 8, 2, 6]
    # Even sign (Taurus): Venus, Mercury, Jupiter, Saturn, Mars.
    assert [varga_sign(30 + x, 30) for x in (2, 7, 15, 22, 27)] == [1, 5, 11, 9, 7]


def test_dasamsa_even_sign_starts_from_ninth():
    assert varga_sign(30.1, 10) == 9   # Taurus 0-3 deg -> Capricorn


def test_vargottama():
    assert is_vargottama(1.0)          # Aries 1 deg: Aries in D1 and D9
    assert not is_vargottama(5.0)

# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Rahul Sathe
"""Rule-based tests for Shadbala (BPHS ch. 27). Values are checked against the
rules themselves; the Jagannatha Hora golden set will add absolute checks."""

from datetime import datetime

import pytest

from jyotishnet_engine import BirthData, build_chart
from jyotishnet_engine.shadbala import (
    NAISARGIKA, PLANETS7, dig_bala, drekkana_bala, drishti_value, kendra_bala,
    ojayugma_bala, paksha_values, shadbala, uchcha_bala,
)

BIRTH = BirthData(datetime(1990, 1, 15, 6, 30), 28.61, 77.21)


@pytest.fixture(scope="module")
def sb():
    return shadbala(build_chart(BIRTH), BIRTH)


def test_uchcha_extremes():
    assert uchcha_bala("Su", 10.0) == pytest.approx(60)      # deep exaltation, Aries 10
    assert uchcha_bala("Su", 190.0) == pytest.approx(0)      # deep debilitation, Libra 10
    assert uchcha_bala("Sa", 200.0) == pytest.approx(60)     # Libra 20


def test_dig_extremes():
    asc, mc = 100.0, 10.0
    assert dig_bala("Ju", asc, asc, mc) == pytest.approx(60)
    assert dig_bala("Su", mc, asc, mc) == pytest.approx(60)
    assert dig_bala("Sa", asc + 180, asc, mc) == pytest.approx(60)
    assert dig_bala("Mo", mc + 180, asc, mc) == pytest.approx(60)
    assert dig_bala("Su", mc + 180, asc, mc) == pytest.approx(0)


def test_kendra_and_drekkana():
    assert [kendra_bala(h) for h in (1, 2, 3)] == [60, 30, 15]
    assert drekkana_bala("Su", 5) == 15 and drekkana_bala("Su", 15) == 0
    assert drekkana_bala("Sa", 15) == 15
    assert drekkana_bala("Ve", 25) == 15


def test_ojayugma():
    assert ojayugma_bala("Mo", 31.0) == 30     # Taurus (even) in D1, Capricorn (even) in D9
    assert ojayugma_bala("Mo", 35.0) == 15     # Taurus in D1, Aquarius (odd) in D9
    assert ojayugma_bala("Su", 1.0) == 30      # Aries in D1 and D9 (odd)


def test_paksha_full_and_new_moon():
    full = paksha_values(0.0, 180.0, mercury_malefic=False)
    assert full["Ju"] == pytest.approx(60) and full["Sa"] == pytest.approx(0)
    new = paksha_values(0.0, 0.0, mercury_malefic=False)
    assert new["Ju"] == pytest.approx(0) and new["Sa"] == pytest.approx(60)
    assert new["Mo"] == pytest.approx(0)          # waxing Moon at new moon: benefic, 0, doubled


def test_drishti_table():
    assert drishti_value("Su", 180) == pytest.approx(60)    # full 7th aspect
    assert drishti_value("Su", 20) == 0
    assert drishti_value("Su", 90) == pytest.approx(45)
    assert drishti_value("Sa", 70) == pytest.approx(60)     # Saturn's 3rd: 25 + 45, capped
    assert drishti_value("Ju", 130) == pytest.approx(50)    # 20 + 30
    assert drishti_value("Ma", 100) == pytest.approx(55)    # 40 + 15


def test_ranges_and_naisargika(sb):
    for p in PLANETS7:
        s = sb[p]
        assert 0 <= s.sthana["uchcha"] <= 60
        assert 0 <= s.dig <= 60
        assert 0 <= s.cheshta <= 60
        assert 0 <= s.kala["paksha"] <= (120 if p == "Mo" else 60)
        assert s.naisargika == pytest.approx(NAISARGIKA[p])
    assert sb["Su"].naisargika == 60


def test_retrograde_planets_have_high_cheshta(sb):
    # Jan 1990: Venus and Jupiter retrograde, Saturn near conjunction with the Sun.
    assert sb["Ve"].cheshta > 45 and sb["Ju"].cheshta > 45
    assert sb["Sa"].cheshta < 10


def test_time_lords(sb):
    # 15 Jan 1990 06:30 IST is before sunrise: the Vedic day is still Sunday.
    assert sb["Su"].kala["vara"] == 45
    assert sum(sb[p].kala["vara"] for p in PLANETS7) == 45
    assert sum(sb[p].kala["hora"] for p in PLANETS7) == 60
    assert sb["Ju"].kala["tribhaga"] == 60

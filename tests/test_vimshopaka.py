# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Rahul Sathe
"""Vimshopaka bala; JHora agreement is in tests/test_jhora_golden.py."""

from datetime import datetime

import pytest

from jyotishnet_engine import BirthData, build_chart
from jyotishnet_engine.vimshopaka import (SCHEMES, VimshopakaOptions, scheme_weights,
                                         varga_points, vimshopaka)


@pytest.mark.parametrize("weights", ["jhora", "bphs"])
def test_weights_sum_to_20(weights):
    for s in SCHEMES:
        assert sum(scheme_weights(s, VimshopakaOptions(weights)).values()) == 20


def test_points():
    signs = {"Su": 4, "Mo": 3, "Ma": 0, "Me": 2, "Ju": 8, "Ve": 1, "Sa": 9, "Ra": 10, "Ke": 4}
    assert varga_points("Su", signs) == 20          # Sun in Leo: own sign
    # Moon in Leo with the Sun: natural friend, but the same sign is a temporal enemy.
    assert varga_points("Mo", dict(signs, Mo=4)) == 10
    # Rahu in Aquarius: Saturn is a natural friend (JHora) and, in the 12th, a temporal one.
    assert varga_points("Ra", signs) == 18
    # Ketu in Leo with the Sun: natural enemy, temporal enemy.
    assert varga_points("Ke", signs) == 5


def test_range_and_options():
    c = build_chart(BirthData(datetime(1990, 1, 15, 6, 30), 28.61, 77.21, utc_offset_hours=5.5))
    jh = vimshopaka(c)
    bp = vimshopaka(c, options=VimshopakaOptions("bphs"))
    for p in jh:
        for s in SCHEMES:
            assert 5 <= jh[p][s] <= 20
            if s != "saptavarga":
                assert jh[p][s] == bp[p][s]

# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Rahul Sathe
from datetime import datetime

import pytest

from jyotishnet_engine import BirthData, build_chart
from jyotishnet_engine.ashtakavarga import (
    BAV_TOTALS, PLANETS7, ashtakavarga, bav_table, ekadhipatya_shodhana, trikona_shodhana,
)

CHART = build_chart(BirthData(datetime(1990, 1, 15, 6, 30), 28.61, 77.21), vargas=[1])


@pytest.mark.parametrize("variant", ["bphs", "pvr"])
def test_bav_totals(variant):
    table = bav_table(variant)
    for g in PLANETS7:
        assert sum(len(h) for h in table[g].values()) == BAV_TOTALS[g]
    av = ashtakavarga(CHART, variant=variant)
    for g in PLANETS7:
        assert sum(av.bav[g]) == BAV_TOTALS[g]
    assert sum(av.sav) == 337


def test_pvr_variant_differs_only_for_moon_and_venus():
    a, b = bav_table("bphs"), bav_table("pvr")
    changed = {t for t in PLANETS7 if a[t] != b[t]}
    assert changed == {"Mo", "Ve"}


def test_trikona():
    row = [3, 5, 2, 4, 6, 2, 3, 1, 2, 4, 5, 0]
    # Trines: (0,4,8)=3,6,2 -> min 2; (1,5,9)=5,2,4 -> min 2; (2,6,10)=2,3,5 -> min 2;
    # (3,7,11)=4,1,0 -> contains 0, unchanged.
    assert trikona_shodhana(row) == [1, 3, 0, 4, 4, 0, 1, 1, 0, 2, 3, 0]
    assert trikona_shodhana([2] * 12) == [0] * 12


def test_ekadhipatya_rules():
    base = [0] * 12
    # Aries (0) / Scorpio (7), both empty, unequal -> both become the smaller.
    r = list(base); r[0], r[7] = 3, 5
    assert ekadhipatya_shodhana(r, set())[0:8:7] == [3, 3]
    # Both empty, equal -> both 0.
    r = list(base); r[0], r[7] = 4, 4
    assert ekadhipatya_shodhana(r, set())[0:8:7] == [0, 0]
    # Aries occupied with 2, Scorpio empty with 5 -> Scorpio set equal to 2.
    r = list(base); r[0], r[7] = 2, 5
    assert ekadhipatya_shodhana(r, {0})[0:8:7] == [2, 2]
    # Aries occupied with 5, Scorpio empty with 2 -> Scorpio 0.
    r = list(base); r[0], r[7] = 5, 2
    assert ekadhipatya_shodhana(r, {0})[0:8:7] == [5, 0]
    # Both occupied -> unchanged.
    r = list(base); r[0], r[7] = 5, 2
    assert ekadhipatya_shodhana(r, {0, 7})[0:8:7] == [5, 2]


def test_shodhya_pinda_is_sum():
    av = ashtakavarga(CHART)
    for g in PLANETS7:
        assert av.shodhya_pinda[g] == av.rasi_pinda[g] + av.graha_pinda[g]

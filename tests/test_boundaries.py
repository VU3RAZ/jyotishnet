# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Rahul Sathe
from datetime import datetime

import pytest

from jyotishnet_engine import BirthData, boundary_map
from jyotishnet_engine.boundaries import _Tracker
from jyotishnet_engine.config import DEFAULT_CONFIG
from jyotishnet_engine.constants import MODEL_VARGAS

BIRTH = BirthData(datetime(1990, 1, 15, 6, 30), 28.61, 77.21)


@pytest.fixture(scope="module")
def result():
    return boundary_map(BIRTH, window_min=60)


def test_segments_cover_window(result):
    _, segments = result
    assert segments[0].start_min == pytest.approx(-60)
    assert segments[-1].end_min == pytest.approx(60)
    for a, b in zip(segments, segments[1:]):
        assert a.end_min == pytest.approx(b.start_min)


def test_changes_are_real_and_precise(result):
    changes, _ = result
    tr = _Tracker(BIRTH, DEFAULT_CONFIG, MODEL_VARGAS, True, True, True)
    for c in changes[:40]:
        before = tr.state(c.offset_min - 1.5 / 60)[c.key]
        after = tr.state(c.offset_min + 0.5 / 60)[c.key]
        assert before != after, c


def test_d1_lagna_changes_rarely(result):
    changes, _ = result
    assert sum(c.key == "D1.lagna" for c in changes) <= 2


def test_fine_vargas_change_more_often(result):
    changes, _ = result
    count = lambda k: sum(c.key == k for c in changes)
    assert count("D60.lagna") > count("D9.lagna") >= count("D1.lagna")

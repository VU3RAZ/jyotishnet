# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Rahul Sathe
"""Historical Indian time: what `Asia/Kolkata` gives, and where it is not enough.

These pin the IANA history the engine relies on, so a tzdata change shows up
here first. Known gap: IANA models one zone for all of India, so Bombay Time
(UTC+4:51, kept in Bombay until 1955) and Calcutta Time (UTC+5:53:20, kept in
Calcutta until 1948) are not applied; such records need an explicit offset.
"""

from datetime import datetime, timedelta

import pytest

from jyotishnet_engine import BirthData

MUMBAI = (19.08, 72.88)
KOLKATA = (22.57, 88.36)


def offset(dt: datetime, place=KOLKATA) -> timedelta:
    b = BirthData(dt, *place)
    return dt - b.utc().replace(tzinfo=None)


@pytest.mark.parametrize("dt, want", [
    (datetime(1850, 1, 15, 12), timedelta(hours=5, minutes=53, seconds=28)),   # LMT
    (datetime(1860, 1, 15, 12), timedelta(hours=5, minutes=53, seconds=20)),   # Howrah Mean Time
    (datetime(1890, 1, 15, 12), timedelta(hours=5, minutes=21, seconds=10)),   # Madras (railway) time
    (datetime(1910, 1, 15, 12), timedelta(hours=5, minutes=30)),
    (datetime(1941, 9, 15, 12), timedelta(hours=5, minutes=30)),
    (datetime(1941, 11, 15, 12), timedelta(hours=6, minutes=30)),              # war time
    (datetime(1942, 6, 15, 12), timedelta(hours=5, minutes=30)),               # 1942 May 15 - Sep 1
    (datetime(1943, 1, 15, 12), timedelta(hours=6, minutes=30)),
    (datetime(1945, 10, 14, 12), timedelta(hours=6, minutes=30)),
    (datetime(1945, 10, 16, 12), timedelta(hours=5, minutes=30)),
    (datetime(1950, 1, 15, 12), timedelta(hours=5, minutes=30)),
])
def test_iana_india_history(dt, want):
    assert offset(dt) == want


def test_zone_ignores_bombay_time():
    # A 1950 Bombay record kept in Bombay Time is read as IST: 39 minutes late
    # in UT. Until city zones exist, such a record must carry its offset.
    dt = datetime(1950, 3, 1, 10, 0)
    assert offset(dt, MUMBAI) == timedelta(hours=5, minutes=30)
    bombay = BirthData(dt, *MUMBAI, utc_offset_hours=4 + 51 / 60)
    ist = BirthData(dt, *MUMBAI)
    assert (bombay.utc() - ist.utc()) == timedelta(minutes=39)


def test_explicit_offset_overrides_war_time():
    dt = datetime(1943, 6, 1, 12, 0)
    assert BirthData(dt, *KOLKATA, utc_offset_hours=5.5).utc().hour == 6
    assert BirthData(dt, *KOLKATA).utc().hour == 5


def test_shifted_keeps_offset_and_zone():
    b = BirthData(datetime(1943, 6, 1, 12, 0), *KOLKATA, utc_offset_hours=6.5)
    s = b.shifted(30)
    assert s.utc_offset_hours == 6.5 and s.tz_name == b.tz_name
    assert s.utc() - b.utc() == timedelta(minutes=30)

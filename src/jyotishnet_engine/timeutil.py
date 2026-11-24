# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Rahul Sathe
"""Birth data and time conversion.

Historical Indian time is a frequent source of silent errors (pre-1955 zones,
war time 1941-45). IANA zone `Asia/Kolkata` carries the all-India history (local
mean times, Madras time, IST from 1906, war time), but not the city times that
Bombay (UTC+4:51, until 1955) and Calcutta (UTC+5:53:20, until 1948) kept beside
IST: give an explicit UTC offset for such records. An explicit offset always
overrides the zone. See tests/test_timeutil.py.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import swisseph as swe


@dataclass(frozen=True)
class BirthData:
    local_datetime: datetime          # naive local clock time as recorded
    latitude: float                   # north positive
    longitude: float                  # east positive
    tz_name: str = "Asia/Kolkata"
    utc_offset_hours: float | None = None   # overrides tz_name when given
    altitude_m: float = 0.0

    def utc(self) -> datetime:
        if self.utc_offset_hours is not None:
            tz = timezone(timedelta(hours=self.utc_offset_hours))
            return self.local_datetime.replace(tzinfo=tz).astimezone(timezone.utc)
        return self.local_datetime.replace(tzinfo=ZoneInfo(self.tz_name)).astimezone(timezone.utc)

    def jd_ut(self) -> float:
        return datetime_to_jd(self.utc())

    def shifted(self, minutes: float) -> "BirthData":
        return BirthData(
            local_datetime=self.local_datetime + timedelta(minutes=minutes),
            latitude=self.latitude, longitude=self.longitude, tz_name=self.tz_name,
            utc_offset_hours=self.utc_offset_hours, altitude_m=self.altitude_m,
        )


def datetime_to_jd(dt_utc: datetime) -> float:
    dt_utc = dt_utc.astimezone(timezone.utc)
    hour = dt_utc.hour + dt_utc.minute / 60 + (dt_utc.second + dt_utc.microsecond / 1e6) / 3600
    return swe.julday(dt_utc.year, dt_utc.month, dt_utc.day, hour, swe.GREG_CAL)


def jd_to_datetime(jd: float) -> datetime:
    y, m, d, h = swe.revjul(jd, swe.GREG_CAL)
    base = datetime(y, m, d, tzinfo=timezone.utc)
    return base + timedelta(hours=h)

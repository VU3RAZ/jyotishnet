# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Rahul Sathe
"""Birth data and time conversion.

Historical Indian time is a frequent source of silent errors (pre-1955 zones,
war time 1941-45). IANA zone `Asia/Kolkata` carries the all-India history (local
mean times, Madras time, IST from 1906, war time), but not the city times that
Bombay (UTC+4:51, until 1955) and Calcutta (UTC+5:53:20, until 1948) kept beside
IST: give an explicit UTC offset for such records. An explicit offset always
overrides the zone; zone_warnings() flags offsets that look wrong for a date and
place in India before 1956. See tests/test_timeutil.py.
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
    """Julian day (UT). A naive datetime is taken as UTC (not the server's local zone)."""
    if dt_utc.tzinfo is None:
        dt_utc = dt_utc.replace(tzinfo=timezone.utc)
    dt_utc = dt_utc.astimezone(timezone.utc)
    hour = dt_utc.hour + dt_utc.minute / 60 + (dt_utc.second + dt_utc.microsecond / 1e6) / 3600
    return swe.julday(dt_utc.year, dt_utc.month, dt_utc.day, hour, swe.GREG_CAL)


def jd_to_datetime(jd: float) -> datetime:
    y, m, d, h = swe.revjul(jd, swe.GREG_CAL)
    base = datetime(y, m, d, tzinfo=timezone.utc)
    return base + timedelta(hours=h)


# ------------------------------------------------------------ zone warnings
# Historical Indian time is the commonest silent error in a birth record. These
# checks never change the chart; they tell the user when the offset they entered
# differs from what the record was probably written in (decision "Historical
# Indian zones": warn in the birth form, do not model the city times).

BOMBAY = (18.94, 72.84)
CALCUTTA = (22.57, 88.36)
BOMBAY_TIME = 4 + 51 / 60            # until about 1955
CALCUTTA_TIME = 5 + 53 / 60 + 20 / 3600   # until 1948
MADRAS_TIME = 5 + 21 / 60 + 10 / 3600     # railway time 1870-1905


def _km(a: tuple[float, float], b: tuple[float, float]) -> float:
    from math import asin, cos, radians, sin, sqrt
    la1, lo1, la2, lo2 = map(radians, (*a, *b))
    h = sin((la2 - la1) / 2) ** 2 + cos(la1) * cos(la2) * sin((lo2 - lo1) / 2) ** 2
    return 2 * 6371 * asin(sqrt(h))


def format_offset(hours: float) -> str:
    sign = "+" if hours >= 0 else "-"
    s = round(abs(hours) * 3600)
    h, m, sec = s // 3600, s % 3600 // 60, s % 60
    return f"UTC{sign}{h}:{m:02d}" + (f":{sec:02d}" if sec else "")


def _in_india(lat: float, lon: float) -> bool:
    return 6 <= lat <= 37 and 68 <= lon <= 98


def zone_warnings(local: datetime, lat: float, lon: float, offset_hours: float) -> list[str]:
    """Warnings about the UTC offset used for a birth, for records from India
    before 1956. Empty when nothing looks wrong."""
    if not _in_india(lat, lon) or local.year >= 1956:
        return []
    near = lambda h: abs(offset_hours - h) < 1 / 60   # within a minute  # noqa: E731
    out: list[str] = []
    # City times ran beside IST, from 1906; before that local mean time covers them.
    city = local.year >= 1906
    if city and _km((lat, lon), BOMBAY) <= 250 and not near(BOMBAY_TIME):
        out.append("Bombay and nearby kept Bombay Time (UTC+4:51) beside IST until about 1955. "
                   "If the record was written in Bombay Time, enter 4.85 as the UTC offset.")
    if city and _km((lat, lon), CALCUTTA) <= 150 and local.year < 1949 and not near(CALCUTTA_TIME):
        out.append("Calcutta and nearby kept Calcutta Time (UTC+5:53:20) beside IST until 1948. "
                   "If the record was written in Calcutta Time, enter 5.8889 as the UTC offset.")
    if near(BOMBAY_TIME) or near(CALCUTTA_TIME):
        return out
    if local.year < 1906:
        lmt = lon / 15
        if not near(lmt) and not near(MADRAS_TIME):
            out.append(f"Before IST (1906) records usually give local mean time ({format_offset(lmt)} "
                       f"at this longitude) or, from 1870, Madras time (UTC+5:21:10). "
                       f"You entered {format_offset(offset_hours)}.")
        return out
    iana = local.replace(tzinfo=ZoneInfo("Asia/Kolkata")).utcoffset().total_seconds() / 3600
    if not near(iana):
        what = "war time" if abs(iana - 6.5) < 1e-6 else "the official time"
        out.append(f"On this date India used {what}, {format_offset(iana)}; you entered "
                   f"{format_offset(offset_hours)}. Check which time the record was written in.")
    return out

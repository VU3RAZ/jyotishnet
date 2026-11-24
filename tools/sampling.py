# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Rahul Sathe
"""Random birth data for the PyJHora cross-checks.

Every cross-check tool draws its charts from here, so one `--sample` flag picks
the same population everywhere:

    india     Eight Indian cities, UTC+5:30, 1900-2030 (the CI default).
    global    Any longitude, latitudes up to +/-66 deg (high latitudes and the
              southern hemisphere), offset from the longitude in half hours.
    boundary  An India or global chart whose time is nudged so that the Lagna
              lies within 30" of a division boundary of a random Shodashavarga,
              or the Moon within 3" of a nakshatra or pada boundary.
    mixed     india, global and boundary in equal shares (the release run).

A tool passes `--seed` through; the release workflow runs several seeds in
parallel and adds the counts.
"""

from __future__ import annotations

import os
import random
import sys
from dataclasses import dataclass
from datetime import datetime, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from jyotishnet_engine import BirthData, SchoolConfig, build_chart  # noqa: E402
from jyotishnet_engine.constants import GRAHAS, SHODASHAVARGA  # noqa: E402

MODES = ("india", "global", "boundary", "mixed")

CITIES = [
    ("New Delhi", 28.61, 77.21), ("Mumbai", 19.08, 72.88), ("Chennai", 13.08, 80.27),
    ("Kolkata", 22.57, 88.36), ("Bengaluru", 12.97, 77.59), ("Srinagar", 34.08, 74.80),
    ("Guwahati", 26.14, 91.74), ("Thiruvananthapuram", 8.52, 76.94),
]

NAK = 360 / 27
PADA = NAK / 4
_CFG = SchoolConfig()


@dataclass(frozen=True)
class Sample:
    name: str
    local: datetime          # local clock time, whole seconds
    lat: float
    lon: float
    tz: float                # UTC offset in hours
    kind: str                # india, global or boundary

    def birth(self) -> BirthData:
        return BirthData(self.local, self.lat, self.lon, utc_offset_hours=self.tz)

    def hms(self) -> tuple[int, int, int]:
        return self.local.hour, self.local.minute, self.local.second

    def ymd(self) -> tuple[int, int, int]:
        return self.local.year, self.local.month, self.local.day


def _random_time(rng: random.Random, years: tuple[int, int]) -> datetime:
    return datetime(rng.randint(*years), rng.randint(1, 12), rng.randint(1, 28),
                    rng.randint(0, 23), rng.randint(0, 59), rng.randint(0, 59))


def _india(rng: random.Random, years: tuple[int, int]) -> Sample:
    name, lat, lon = rng.choice(CITIES)
    return Sample(name, _random_time(rng, years), lat, lon, 5.5, "india")


def _global(rng: random.Random, years: tuple[int, int]) -> Sample:
    lat = round(rng.uniform(-66.0, 66.0), 4)
    lon = round(rng.uniform(-180.0, 180.0), 4)
    tz = round(lon / 15 * 2) / 2
    return Sample("global", _random_time(rng, years), lat, lon, tz, "global")


def _offset(lon: float, size: float, target: float) -> float:
    """Signed degrees from lon to the nearest boundary of a `size` grid, plus target."""
    r = lon % size
    d = -r if r < size / 2 else size - r
    return d + target


def _nudge(s: Sample, point: str, size: float, target: float) -> Sample:
    """Move the birth time so `point` sits `target` degrees past a `size` boundary."""
    def longitude(t: datetime) -> float:
        c = build_chart(BirthData(t, s.lat, s.lon, utc_offset_hours=s.tz), _CFG, [1])
        return c.lagna.longitude if point == "La" else c.grahas["Mo"].longitude

    rate = 360 / 86164.1 if point == "La" else 13.2 / 86400   # degrees per second, first guess
    local, lon = s.local, longitude(s.local)
    for _ in range(8):
        d = _offset(lon, size, target)
        step = round(d / rate)
        if step == 0:
            break
        new = local + timedelta(seconds=step)
        new_lon = longitude(new)
        moved = (new_lon - lon + 180) % 360 - 180
        if moved * step > 0:          # secant: use the rate actually seen
            rate = moved / step
        local, lon = new, new_lon
    return Sample(s.name, local, s.lat, s.lon, s.tz, "boundary")


def _boundary(rng: random.Random, years: tuple[int, int]) -> Sample:
    base = _india(rng, years) if rng.random() < 0.5 else _global(rng, years)
    if rng.random() < 0.7:
        n = rng.choice(SHODASHAVARGA)
        # D30's parts are unequal; its 5-degree grid covers every boundary but 12 and 18.
        size = 5.0 if n == 30 else 30.0 / n
        return _nudge(base, "La", size, rng.uniform(-30, 30) / 3600)
    size = NAK if rng.random() < 0.5 else PADA
    return _nudge(base, "Mo", size, rng.uniform(-3, 3) / 3600)


def sample(rng: random.Random, mode: str = "india", years: tuple[int, int] = (1900, 2030)) -> Sample:
    if mode == "mixed":
        mode = rng.choice(("india", "global", "boundary"))
    if mode == "india":
        return _india(rng, years)
    if mode == "global":
        return _global(rng, years)
    if mode == "boundary":
        return _boundary(rng, years)
    raise ValueError(f"unknown sample mode {mode!r}")


def add_arguments(ap, charts: int, seed: int) -> None:
    ap.add_argument("--charts", type=int, default=charts)
    ap.add_argument("--seed", type=int, default=seed)
    ap.add_argument("--sample", choices=MODES, default="india",
                    help="chart population (see tools/sampling.py)")


def d1_disagreements(chart, pyjhora_positions, tol: float = 0.002) -> tuple[list[str], list[str]]:
    """Points whose D1 sign differs from PyJHora's, split into (hard, near-boundary).

    `pyjhora_positions` is PyJHora's [(key, (sign, degree)), ...] with key "L" for
    the Lagna and 0-8 for the grahas. A point within `tol` degrees of a sign
    boundary can flip on a sub-arcsecond ephemeris difference, so it is reported
    apart from real disagreements.
    """
    hard, edge = [], []
    for key, (sign, _) in pyjhora_positions:
        code = "La" if key == "L" else GRAHAS[key]
        point = chart.lagna if code == "La" else chart.grahas[code]
        if point.sign != sign:
            r = point.longitude % 30
            (edge if min(r, 30 - r) < tol else hard).append(code)
    return hard, edge

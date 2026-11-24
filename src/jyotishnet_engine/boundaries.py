# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Rahul Sathe
"""Boundary map for birth-time rectification (design doc, BTR pipeline step 2).

Scans a window around the recorded birth time and finds every moment where
something time-sensitive changes:

- the Lagna sign in each varga,
- the Moon's sign in each varga,
- the sign of each special lagna (Bhava, Hora, Ghati Lagna, Pranapada),
- the Moon's nakshatra pada (which moves dasha dates).

Each change is refined by bisection to `precision_s` seconds. Between two
consecutive changes every tracked quantity is constant: that span is a segment,
and the model only needs to run once per segment.
"""

from __future__ import annotations

from dataclasses import dataclass

from .config import DEFAULT_CONFIG, SchoolConfig
from .constants import MODEL_VARGAS, modality
from .ephemeris import ascendant, body_longitude, previous_sunrise
from .nakshatra import nakshatra_of
from .timeutil import BirthData
from .vargas import varga_sign

MIN_PER_DAY = 1440.0


@dataclass(frozen=True)
class Change:
    key: str
    offset_min: float        # minutes from the recorded birth time
    jd_ut: float
    before: object
    after: object


@dataclass(frozen=True)
class Segment:
    start_min: float
    end_min: float

    @property
    def mid_min(self) -> float:
        return (self.start_min + self.end_min) / 2


class _Tracker:
    def __init__(self, birth: BirthData, cfg: SchoolConfig, vargas: list[int],
                 track_moon: bool, track_special: bool, track_pada: bool):
        self.birth = birth
        self.cfg = cfg
        self.vargas = vargas
        self.track_moon = track_moon
        self.track_special = track_special
        self.track_pada = track_pada
        self.jd0 = birth.jd_ut()
        self._rise_cache: dict[int, tuple[float, float]] = {}

    def _sunrise(self, jd: float) -> tuple[float, float]:
        """Sunrise and Sun longitude at sunrise, cached per civil day."""
        key = int(jd + 0.5)
        hit = self._rise_cache.get(key)
        if hit is None or hit[0] > jd:
            rise = previous_sunrise(jd, self.birth.latitude, self.birth.longitude,
                                    self.birth.altitude_m, self.cfg)
            hit = (rise, body_longitude(rise, "Su", self.cfg))
            self._rise_cache[key] = hit
        return hit

    def state(self, offset_min: float) -> dict[str, object]:
        jd = self.jd0 + offset_min / MIN_PER_DAY
        b = self.birth
        asc = ascendant(jd, b.latitude, b.longitude, self.cfg)
        out: dict[str, object] = {f"D{n}.lagna": varga_sign(asc, n) for n in self.vargas}
        if self.track_moon or self.track_pada:
            moon = body_longitude(jd, "Mo", self.cfg)
            if self.track_moon:
                out.update({f"D{n}.moon": varga_sign(moon, n) for n in self.vargas})
            if self.track_pada:
                nk = nakshatra_of(moon)
                out["moon.pada"] = (nk.index, nk.pada)
        if self.track_special:
            rise, sun_rise = self._sunrise(jd)
            minutes = (jd - rise) * MIN_PER_DAY
            sun_now = body_longitude(jd, "Su", self.cfg)
            out["BL"] = int(((sun_rise + minutes / 120 * 30) % 360) // 30)
            out["HL"] = int(((sun_rise + minutes / 60 * 30) % 360) // 30)
            out["GL"] = int(((sun_rise + minutes / 24 * 30) % 360) // 30)
            off = {0: 0.0, 1: 240.0, 2: 120.0}[modality(int(sun_now // 30))]
            out["PP"] = int(((sun_now + off + minutes / 6 * 30) % 360) // 30)
        return out


def boundary_map(birth: BirthData, window_min: float = 60.0, step_s: float = 10.0,
                 precision_s: float = 1.0, cfg: SchoolConfig = DEFAULT_CONFIG,
                 vargas: list[int] | None = None, track_moon: bool = True,
                 track_special: bool = True, track_pada: bool = True
                 ) -> tuple[list[Change], list[Segment]]:
    """Changes and segments within [-window_min, +window_min] of the birth time.

    step_s must be shorter than the fastest change being tracked; 10 s is safe
    for D60 Lagna and Pranapada at any latitude below the polar circles.
    """
    vargas = vargas or MODEL_VARGAS
    tr = _Tracker(birth, cfg, vargas, track_moon, track_special, track_pada)
    step = step_s / 60.0
    eps = precision_s / 60.0

    changes: list[Change] = []
    t = -window_min
    prev = tr.state(t)
    while t < window_min:
        t_next = min(t + step, window_min)
        cur = tr.state(t_next)
        diff = [k for k in cur if cur[k] != prev[k]]
        for key in diff:
            lo, hi = t, t_next
            v_lo = prev[key]
            while hi - lo > eps:
                mid = (lo + hi) / 2
                if tr.state(mid)[key] == v_lo:
                    lo = mid
                else:
                    hi = mid
            changes.append(Change(key, hi, tr.jd0 + hi / MIN_PER_DAY, prev[key], cur[key]))
        prev, t = cur, t_next

    changes.sort(key=lambda c: c.offset_min)
    cuts = [-window_min] + [c.offset_min for c in changes] + [window_min]
    segments = [Segment(a, b) for a, b in zip(cuts, cuts[1:]) if b - a > 1e-9]
    return changes, segments

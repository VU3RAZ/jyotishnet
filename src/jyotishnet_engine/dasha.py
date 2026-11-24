# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Rahul Sathe
"""Dasha systems: Vimshottari (three levels), Ashtottari and Yogini.

Periods are computed in years from birth, then converted to Julian days by the
configured year definition:

- "solar" (default; Jagannatha Hora's default): a dasha year is the time the Sun
  takes to move 360 degrees of sidereal longitude, so fractions of a year follow
  the Sun's actual (uneven) motion.
- "fixed": a year is `cfg.dasha_year_days` days (365.25, 360, ...).
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .config import SchoolConfig
from .constants import (
    ASHTOTTARI_FIRST_NAKSHATRA, ASHTOTTARI_LORDS, ASHTOTTARI_NAKSHATRAS, ASHTOTTARI_YEARS,
    SIGN_LORD, VIMSHOTTARI_LORDS, VIMSHOTTARI_YEARS, YOGINIS,
)
from .ephemeris import body_longitude
from .nakshatra import nakshatra_of

VIMSHOTTARI_TOTAL = 120.0
SIDEREAL_YEAR_DAYS = 365.256363
SUN_MEAN_MOTION = 360.0 / SIDEREAL_YEAR_DAYS


@dataclass
class Period:
    lord: str
    start_jd: float
    end_jd: float
    level: int                      # 1 = maha, 2 = antar, 3 = pratyantar
    name: str | None = None         # Yogini name, when relevant
    children: list["Period"] = field(default_factory=list)
    start_years: float = 0.0        # offset from birth in dasha years
    end_years: float = 0.0

    def contains(self, jd: float) -> bool:
        return self.start_jd <= jd < self.end_jd


class YearClock:
    """Converts 'years after birth' to Julian days under the configured year."""

    def __init__(self, birth_jd: float, cfg: SchoolConfig):
        self.birth_jd = birth_jd
        self.cfg = cfg
        self.solar = cfg.dasha_year_mode == "solar"
        if self.solar:
            self.sun0 = body_longitude(birth_jd, "Su", cfg)
        self._cache: dict[float, float] = {}

    def jd(self, years: float) -> float:
        if not self.solar:
            return self.birth_jd + years * self.cfg.dasha_year_days
        key = round(years, 12)
        if key in self._cache:
            return self._cache[key]
        target = 360.0 * years
        jd = self.birth_jd + years * SIDEREAL_YEAR_DAYS
        for _ in range(6):
            approx = (jd - self.birth_jd) * SUN_MEAN_MOTION
            delta = (body_longitude(jd, "Su", self.cfg) - self.sun0 - approx + 180) % 360 - 180
            err = target - (approx + delta)
            jd += err / SUN_MEAN_MOTION
            if abs(err) < 1e-7:
                break
        self._cache[key] = jd
        return jd


def _subdivide_years(parent: Period, start_idx: int, seq: list[str], years: dict[str, float],
                     total: float, levels_left: int) -> None:
    if levels_left <= 0:
        return
    span = parent.end_years - parent.start_years
    t = parent.start_years
    for i in range(len(seq)):
        idx = (start_idx + i) % len(seq)
        length = span * years[seq[idx]] / total
        child = Period(seq[idx], 0, 0, parent.level + 1, start_years=t, end_years=t + length)
        _subdivide_years(child, idx, seq, years, total, levels_left - 1)
        parent.children.append(child)
        t += length


def _build(seq: list[str], years: dict[str, float], total: float, first_index: int,
           first_start_years: float, span_years: float, levels: int, clock: YearClock) -> list[Period]:
    """Generic nakshatra-dasha builder working in years from birth."""
    out: list[Period] = []
    t = first_start_years
    i = 0
    while t < span_years:
        idx = (first_index + i) % len(seq)
        md = Period(seq[idx], 0, 0, 1, start_years=t, end_years=t + years[seq[idx]])
        _subdivide_years(md, idx, seq, years, total, levels - 1)
        out.append(md)
        t = md.end_years
        i += 1
    _assign_jd(out, clock)
    return out


def _assign_jd(periods: list[Period], clock: YearClock) -> None:
    for p in periods:
        p.start_jd = clock.jd(p.start_years)
        p.end_jd = clock.jd(p.end_years)
        _assign_jd(p.children, clock)


def vimshottari(moon_lon: float, birth_jd: float, cfg: SchoolConfig,
                levels: int = 3, span_years: float = 120.0) -> list[Period]:
    """Mahadashas from the one running at birth until span_years after birth."""
    nk = nakshatra_of(moon_lon)
    idx = VIMSHOTTARI_LORDS.index(nk.lord)
    first_start = -nk.fraction * VIMSHOTTARI_YEARS[nk.lord]   # the first maha began before birth
    years = {k: float(v) for k, v in VIMSHOTTARI_YEARS.items()}
    return _build(VIMSHOTTARI_LORDS, years, VIMSHOTTARI_TOTAL, idx, first_start, span_years,
                  levels, YearClock(birth_jd, cfg))


def ashtottari(moon_lon: float, birth_jd: float, cfg: SchoolConfig,
               levels: int = 3, span_years: float = 108.0) -> list[Period]:
    """Ashtottari dasha (108 years), antardashas from the dasha lord onwards.

    The starting lord rules the run of nakshatras holding the Moon; the part of
    that dasha elapsed at birth is the Moon's progress through the whole run
    (Jagannatha Hora's method).
    """
    span = 360.0 / 27.0
    rel = (moon_lon - ASHTOTTARI_FIRST_NAKSHATRA * span) % 360.0
    start = 0.0
    for idx, lord in enumerate(ASHTOTTARI_LORDS):
        width = ASHTOTTARI_NAKSHATRAS[lord] * span
        if rel < start + width:
            fraction = (rel - start) / width
            break
        start += width
    years = {k: float(v) for k, v in ASHTOTTARI_YEARS.items()}
    return _build(ASHTOTTARI_LORDS, years, 108.0, idx, -fraction * years[lord], span_years,
                  levels, YearClock(birth_jd, cfg))


def ashtottari_applicable(lagna_sign: int, signs: dict[str, int]) -> bool:
    """Common rule for when Ashtottari applies: Rahu in a kendra or trikona from
    the Lagna lord, but not in the Lagna."""
    lord_sign = signs[SIGN_LORD[lagna_sign]]
    d = (signs["Ra"] - lord_sign) % 12 + 1
    return signs["Ra"] != lagna_sign and d in (1, 4, 5, 7, 9, 10)


def yogini(moon_lon: float, birth_jd: float, cfg: SchoolConfig,
           levels: int = 2, span_years: float = 108.0) -> list[Period]:
    nk = nakshatra_of(moon_lon)
    n = (nk.index + 1 + 3) % 8
    first = (n - 1) % 8                      # 0-based index into YOGINIS; 0 maps to Sankata
    names = [y[0] for y in YOGINIS]
    lords = {y[0]: y[1] for y in YOGINIS}
    years = {y[0]: float(y[2]) for y in YOGINIS}
    periods = _build(names, years, 36.0, first, -nk.fraction * years[names[first]], span_years,
                     levels, YearClock(birth_jd, cfg))

    def relabel(ps: list[Period]) -> None:   # built on Yogini names; expose the lord too
        for p in ps:
            p.name, p.lord = p.lord, lords[p.lord]
            relabel(p.children)
    relabel(periods)
    return periods


def running(periods: list[Period], jd: float) -> list[Period]:
    """Chain of periods (maha, antar, ...) running at jd."""
    chain: list[Period] = []
    level = periods
    while level:
        hit = next((p for p in level if p.contains(jd)), None)
        if hit is None:
            break
        chain.append(hit)
        level = hit.children
    return chain

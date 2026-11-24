# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Rahul Sathe
"""Dasha systems: Vimshottari (three levels) and Yogini.

Periods are returned with Julian-day start and end so callers can convert to
any calendar. Year length comes from SchoolConfig.dasha_year_days.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .config import SchoolConfig
from .constants import VIMSHOTTARI_LORDS, VIMSHOTTARI_YEARS, YOGINIS
from .nakshatra import nakshatra_of

VIMSHOTTARI_TOTAL = 120.0


@dataclass
class Period:
    lord: str
    start_jd: float
    end_jd: float
    level: int                      # 1 = maha, 2 = antar, 3 = pratyantar
    name: str | None = None         # Yogini name, when relevant
    children: list["Period"] = field(default_factory=list)

    def contains(self, jd: float) -> bool:
        return self.start_jd <= jd < self.end_jd


def _subdivide(parent: Period, sequence: list[str], years: dict[str, float], total: float,
               levels_left: int) -> None:
    if levels_left <= 0:
        return
    span = parent.end_jd - parent.start_jd
    start_idx = sequence.index(parent.lord)
    t = parent.start_jd
    for i in range(len(sequence)):
        lord = sequence[(start_idx + i) % len(sequence)]
        length = span * years[lord] / total
        child = Period(lord, t, t + length, parent.level + 1)
        _subdivide(child, sequence, years, total, levels_left - 1)
        parent.children.append(child)
        t += length


def vimshottari(moon_lon: float, birth_jd: float, cfg: SchoolConfig,
                levels: int = 3, span_years: float = 120.0) -> list[Period]:
    """Mahadashas from the one running at birth until span_years after birth."""
    year = cfg.dasha_year_days
    nk = nakshatra_of(moon_lon)
    idx = VIMSHOTTARI_LORDS.index(nk.lord)
    first_len = VIMSHOTTARI_YEARS[nk.lord] * year
    start = birth_jd - nk.fraction * first_len     # the first maha began before birth
    out: list[Period] = []
    t = start
    i = 0
    while t < birth_jd + span_years * year:
        lord = VIMSHOTTARI_LORDS[(idx + i) % 9]
        length = VIMSHOTTARI_YEARS[lord] * year
        md = Period(lord, t, t + length, 1)
        _subdivide(md, VIMSHOTTARI_LORDS, VIMSHOTTARI_YEARS, VIMSHOTTARI_TOTAL, levels - 1)
        out.append(md)
        t += length
        i += 1
    return out


def yogini(moon_lon: float, birth_jd: float, cfg: SchoolConfig,
           levels: int = 2, span_years: float = 108.0) -> list[Period]:
    year = cfg.dasha_year_days
    nk = nakshatra_of(moon_lon)
    n = (nk.index + 1 + 3) % 8
    first = (n - 1) % 8                      # 0-based index into YOGINIS; 0 maps to Sankata
    names = [y[0] for y in YOGINIS]
    years = {y[0]: float(y[2]) for y in YOGINIS}
    lords = {y[0]: y[1] for y in YOGINIS}
    first_len = years[names[first]] * year
    t = birth_jd - nk.fraction * first_len
    out: list[Period] = []
    i = 0
    while t < birth_jd + span_years * year:
        nm = names[(first + i) % 8]
        length = years[nm] * year
        md = Period(lords[nm], t, t + length, 1, name=nm)
        if levels > 1:
            span = length
            tt = t
            for j in range(8):
                sub = names[(first + i + j) % 8]
                sl = span * years[sub] / 36.0
                md.children.append(Period(lords[sub], tt, tt + sl, 2, name=sub))
                tt += sl
        out.append(md)
        t += length
        i += 1
    return out


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

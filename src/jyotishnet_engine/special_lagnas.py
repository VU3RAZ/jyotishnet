# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Rahul Sathe
"""Special lagnas that move faster than the ascendant (key for rectification).

Conventions differ between sources; these follow the common Parashari
formulation (as in BPHS and PVR Narasimha Rao's book) and are flagged for
expert sign-off and cross-checking against PyJHora / Jagannatha Hora.

- Bhava Lagna: Sun at sunrise + 1 sign per 5 ghatis (2 hours).
- Hora Lagna:  Sun at sunrise + 1 sign per 2.5 ghatis (1 hour).
- Ghati Lagna: Sun at sunrise + 1 sign per ghati (24 minutes).
- Pranapada:   1 sign per 15 vighatis (6 minutes), counted from the Sun when the
               Sun is in a movable sign, from the 9th when fixed, the 5th when dual.
- Vighati Lagna: Sun at sunrise + 1 sign per 15 vighatis (6 minutes), as Jagannatha
               Hora 8.0 (matched on its 55 golden charts).
"""

from __future__ import annotations

from dataclasses import dataclass

from .config import SchoolConfig
from .constants import modality
from .ephemeris import previous_sunrise, sun_longitude


@dataclass(frozen=True)
class SpecialLagnas:
    sunrise_jd: float
    bhava_lagna: float
    hora_lagna: float
    ghati_lagna: float
    pranapada: float
    vighati_lagna: float


def special_lagnas(jd_ut: float, lat: float, lon: float, alt: float, cfg: SchoolConfig) -> SpecialLagnas:
    rise = previous_sunrise(jd_ut, lat, lon, alt, cfg)
    minutes = (jd_ut - rise) * 1440.0
    sun_rise = sun_longitude(rise, cfg)
    sun_now = sun_longitude(jd_ut, cfg)

    bl = (sun_rise + minutes / 120.0 * 30.0) % 360.0
    hl = (sun_rise + minutes / 60.0 * 30.0) % 360.0
    gl = (sun_rise + minutes / 24.0 * 30.0) % 360.0

    offset = {0: 0.0, 1: 240.0, 2: 120.0}[modality(int(sun_now // 30))]
    pp = (sun_now + offset + minutes / 6.0 * 30.0) % 360.0
    vl = (sun_rise + minutes / 6.0 * 30.0) % 360.0
    return SpecialLagnas(rise, bl, hl, gl, pp, vl)

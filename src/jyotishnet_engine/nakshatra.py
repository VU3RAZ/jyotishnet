# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Rahul Sathe
"""Nakshatra, pada and nakshatra lord."""

from __future__ import annotations

from dataclasses import dataclass

from .constants import NAKSHATRAS, NAKSHATRA_SPAN, VIMSHOTTARI_LORDS


@dataclass(frozen=True)
class NakshatraPosition:
    index: int          # 0..26
    name: str
    pada: int           # 1..4
    lord: str           # Vimshottari lord
    fraction: float     # 0..1 through the nakshatra


def nakshatra_of(lon: float) -> NakshatraPosition:
    lon = lon % 360.0
    idx = min(int(lon // NAKSHATRA_SPAN), 26)
    frac = (lon - idx * NAKSHATRA_SPAN) / NAKSHATRA_SPAN
    pada = min(int(frac * 4) + 1, 4)
    return NakshatraPosition(idx, NAKSHATRAS[idx], pada, VIMSHOTTARI_LORDS[idx % 9], frac)

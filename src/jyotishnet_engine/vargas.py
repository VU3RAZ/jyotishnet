# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Rahul Sathe
"""Parashari divisional charts (Shodashavarga), per Brihat Parashara Hora Shastra.

`varga_sign(lon, n)` returns the sign (0..11) a sidereal longitude falls in for
divisional chart Dn. `varga_longitude` also gives the position within that sign,
scaling the division to 30 degrees, which the slider and the model use.

Variant schemes (Parivritti or Kashinatha hora, Somanatha drekkana and others)
are added as separate functions keyed by name; the defaults below are Parashari.
"""

from __future__ import annotations

from .constants import element, is_odd_sign, modality


def _parts(lon: float, n: int) -> tuple[int, int, float]:
    """Sign, part index within the sign, and fraction through that part."""
    lon = lon % 360.0
    sign = int(lon // 30)
    within = lon - sign * 30
    # Multiply before dividing so exact boundaries (e.g. 10 deg in D9) land in
    # the next part, matching the continuous formula floor(lon * n / 30).
    scaled = within * n / 30.0
    part = min(int(scaled), n - 1)
    frac = min(max(scaled - part, 0.0), 1.0 - 1e-12)
    return sign, part, frac


def varga_sign(lon: float, n: int) -> int:
    sign, part, _ = _parts(lon, n)
    odd = is_odd_sign(sign)
    mod = modality(sign)

    if n == 1:
        return sign
    if n == 2:  # Hora: Sun's hora = Leo, Moon's hora = Cancer
        first = 4 if odd else 3
        return first if part == 0 else (3 if first == 4 else 4)
    if n == 3:  # Drekkana: 1st, 5th, 9th from the sign
        return (sign + 4 * part) % 12
    if n == 4:  # Chaturthamsa: kendras from the sign
        return (sign + 3 * part) % 12
    if n == 7:  # Saptamsa: odd from the sign, even from the 7th
        return (sign + part + (0 if odd else 6)) % 12
    if n == 9:  # Navamsa: movable from itself, fixed from 9th, dual from 5th
        start = {0: sign, 1: sign + 8, 2: sign + 4}[mod]
        return (start + part) % 12
    if n == 10:  # Dasamsa: odd from the sign, even from the 9th
        return (sign + part + (0 if odd else 8)) % 12
    if n == 12:  # Dwadasamsa: from the sign
        return (sign + part) % 12
    if n == 16:  # Shodasamsa: movable Aries, fixed Leo, dual Sagittarius
        return ({0: 0, 1: 4, 2: 8}[mod] + part) % 12
    if n == 20:  # Vimsamsa: movable Aries, fixed Sagittarius, dual Leo
        return ({0: 0, 1: 8, 2: 4}[mod] + part) % 12
    if n == 24:  # Chaturvimsamsa: odd from Leo, even from Cancer
        return ((4 if odd else 3) + part) % 12
    if n == 27:  # Bhamsa: fire Aries, earth Cancer, air Libra, water Capricorn
        return ({0: 0, 1: 3, 2: 6, 3: 9}[element(sign)] + part) % 12
    if n == 30:  # Trimsamsa: unequal parts ruled by the five tara grahas
        return _trimsamsa(lon)
    if n == 40:  # Khavedamsa: odd from Aries, even from Libra
        return ((0 if odd else 6) + part) % 12
    if n == 45:  # Akshavedamsa: movable Aries, fixed Leo, dual Sagittarius
        return ({0: 0, 1: 4, 2: 8}[mod] + part) % 12
    if n == 60:  # Shashtiamsa: from the sign
        return (sign + part) % 12
    raise ValueError(f"Unsupported varga D{n}")


# Odd signs: Mars 0-5 (Aries), Saturn 5-10 (Aquarius), Jupiter 10-18 (Sagittarius),
# Mercury 18-25 (Gemini), Venus 25-30 (Libra). Even signs reverse the order:
# Venus 0-5 (Taurus), Mercury 5-12 (Virgo), Jupiter 12-20 (Pisces),
# Saturn 20-25 (Capricorn), Mars 25-30 (Scorpio).
_TRIMSAMSA_ODD = [(5, 0), (10, 10), (18, 8), (25, 2), (30, 6)]
_TRIMSAMSA_EVEN = [(5, 1), (12, 5), (20, 11), (25, 9), (30, 7)]


def _trimsamsa_bounds(lon: float) -> tuple[float, float, int]:
    lon = lon % 360.0
    sign = int(lon // 30)
    within = lon - sign * 30
    table = _TRIMSAMSA_ODD if is_odd_sign(sign) else _TRIMSAMSA_EVEN
    start = 0.0
    for end, target in table:
        if within < end:
            return start, float(end), target
        start = float(end)
    return 25.0, 30.0, table[-1][1]


def _trimsamsa(lon: float) -> int:
    return _trimsamsa_bounds(lon)[2]


def varga_longitude(lon: float, n: int) -> float:
    """Longitude in the varga chart: target sign plus scaled position in the part."""
    if n == 1:
        return lon % 360.0
    if n == 30:
        start, end, target = _trimsamsa_bounds(lon)
        within = (lon % 30.0)
        frac = (within - start) / (end - start)
        return target * 30.0 + frac * 30.0
    _, _, frac = _parts(lon, n)
    return varga_sign(lon, n) * 30.0 + frac * 30.0


def is_vargottama(lon: float) -> bool:
    return varga_sign(lon, 1) == varga_sign(lon, 9)

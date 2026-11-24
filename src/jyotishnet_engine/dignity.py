"""Planetary dignity in a sign (exaltation, moolatrikona, own, natural relation).

Rahu and Ketu dignities differ between schools and are left as "node" here.
"""

from __future__ import annotations

from .constants import (
    EXALTATION, MOOLATRIKONA, NATURAL_ENEMIES, NATURAL_FRIENDS, OWN_SIGNS, SIGN_LORD,
)


def dignity(planet: str, lon: float) -> str:
    if planet in ("Ra", "Ke"):
        return "node"
    lon = lon % 360.0
    sign = int(lon // 30)
    deg = lon - sign * 30
    ex_sign, _ = EXALTATION[planet]
    if sign == ex_sign:
        return "exalted"
    if sign == (ex_sign + 6) % 12:
        return "debilitated"
    mt_sign, mt_start, mt_end = MOOLATRIKONA[planet]
    if sign == mt_sign and mt_start <= deg < mt_end:
        return "moolatrikona"
    if sign in OWN_SIGNS[planet]:
        return "own"
    lord = SIGN_LORD[sign]
    if lord in NATURAL_FRIENDS[planet]:
        return "friend"
    if lord in NATURAL_ENEMIES[planet]:
        return "enemy"
    return "neutral"

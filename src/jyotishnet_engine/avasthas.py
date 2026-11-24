# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Rahul Sathe
"""Avasthas (planetary states) of the nine grahas in the Rasi chart.

Follows Jagannatha Hora 8.0's code (read from jhora.exe), which shows three
columns: age (Baladi), alertness (Jagradadi) and mood (Deeptadi and Lajjitadi
states together, several at once).

- Baladi (BPHS ch. 45): the degree within the sign, counted from the end in even
  signs, in five 6-degree parts: Baala, Kumara, Yuva, Vriddha, Mrita.
- Jagradadi: Jaagrita in its own or exaltation sign; otherwise Swapna when the
  sign's lord is a friend or neutral, Sushupta when an enemy. JHora uses the
  natural relationship by default (its "UseCompundRelationshipInAvasthas" off);
  `compound=True` uses natural + temporal.
- Mood, each state independent (JHora's conditions):
  Deepta exalted; Swastha own sign; Mudita, Saanta, Deena, Duhkhita in the sign of
  a great friend, friend, neutral, enemy or great enemy (compound relationship);
  Vikala with two or more other malefics in its sign; Khala in a sign of the Sun,
  Mars or Saturn; Kopita within 6 deg of the Sun; Lajjita in the 5th house with a
  malefic; Garvita exalted or in its moolatrikona sign.
  Malefics here are the Sun, Mars, Saturn, Rahu and Ketu.
  JHora 8.0 lists Kshudhita, Trishita, Mudita (Lajjitadi) and Kshobhita but never
  sets them; they are not computed here either.
- Rahu and Ketu: own Aquarius and Scorpio, exalted in Gemini and Sagittarius,
  moolatrikona Virgo and Pisces; Venus and Saturn friends, Mercury and Jupiter
  neutral, the Sun, Moon and Mars enemies.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .chart import Chart
from .constants import EXALTATION, NATURAL_ENEMIES, NATURAL_FRIENDS, OWN_SIGNS, SIGN_LORD

GRAHAS9 = ("Su", "Mo", "Ma", "Me", "Ju", "Ve", "Sa", "Ra", "Ke")
BALADI = ("Baala", "Kumara", "Yuva", "Vriddha", "Mrita")
JAGRADADI = ("Jaagrita", "Swapna", "Sushupta")
MOODS = ("Deepta", "Swastha", "Mudita", "Saanta", "Deena", "Duhkhita", "Vikala", "Khala",
         "Kopita", "Lajjita", "Garvita")
MALEFICS = ("Su", "Ma", "Sa", "Ra", "Ke")

_OWN = {**{p: tuple(s) for p, s in OWN_SIGNS.items()}, "Ra": (10,), "Ke": (7,)}
_EXALT = {**{p: s for p, (s, _) in EXALTATION.items()}, "Ra": 2, "Ke": 8}
# Moolatrikona signs as JHora's table (sign only, no degree range).
_MOOLA = {"Su": 4, "Mo": 1, "Ma": 0, "Me": 5, "Ju": 8, "Ve": 6, "Sa": 10, "Ra": 5, "Ke": 11}
_NODE_FRIENDS, _NODE_ENEMIES = ("Ve", "Sa"), ("Su", "Mo", "Ma")


@dataclass(frozen=True)
class Avasthas:
    baladi: str
    jagradadi: str
    moods: tuple[str, ...] = field(default_factory=tuple)


def natural_relation(p: str, lord: str) -> int:
    """+1 friend, 0 neutral, -1 enemy."""
    if p in ("Ra", "Ke"):
        return 1 if lord in _NODE_FRIENDS else -1 if lord in _NODE_ENEMIES else 0
    return 1 if lord in NATURAL_FRIENDS[p] else -1 if lord in NATURAL_ENEMIES[p] else 0


def compound_relation(p: str, lord: str, signs: dict[str, int]) -> int:
    """-2 great enemy .. +2 great friend: natural plus temporal (lord 2nd-4th or
    10th-12th from the graha is a temporal friend)."""
    temporal = 1 if (signs[lord] - signs[p]) % 12 + 1 in (2, 3, 4, 10, 11, 12) else -1
    return natural_relation(p, lord) + temporal


def baladi(lon: float) -> str:
    sign, d = int(lon // 30) % 12, lon % 30
    if sign % 2 == 1:          # even sign (Taurus, Cancer, ...): counted from the end
        d = 30.0 - d
    return BALADI[min(int(d / 6.0), 4)]


def avasthas(chart: Chart, compound: bool = False) -> dict[str, Avasthas]:
    """Avasthas of the nine grahas (Rasi chart)."""
    lons = {p: chart.grahas[p].longitude for p in GRAHAS9}
    signs = {p: chart.grahas[p].sign for p in GRAHAS9}
    lagna_sign = chart.lagna.sign
    out = {}
    for p in GRAHAS9:
        s, lord = signs[p], SIGN_LORD[signs[p]]
        own, exalted = s in _OWN[p], s == _EXALT[p]
        rel = compound_relation(p, lord, signs) if compound else natural_relation(p, lord)
        jag = JAGRADADI[0] if (own or exalted) else JAGRADADI[1] if rel >= 0 else JAGRADADI[2]

        moods = []
        if exalted:
            moods.append("Deepta")
        if own:
            moods.append("Swastha")
        if lord != p:
            moods.append({2: "Mudita", 1: "Saanta", 0: "Deena", -1: "Duhkhita",
                          -2: "Duhkhita"}[compound_relation(p, lord, signs)])
        malefics_here = sum(1 for q in MALEFICS if signs[q] == s)
        others = malefics_here - (1 if p in MALEFICS else 0)
        if others >= 2:
            moods.append("Vikala")
        if lord in ("Su", "Ma", "Sa"):
            moods.append("Khala")
        if p != "Su":
            d = abs(lons[p] - lons["Su"]) % 360
            if min(d, 360 - d) <= 6.0:
                moods.append("Kopita")
        if (s - lagna_sign) % 12 == 4 and others >= 1:
            moods.append("Lajjita")
        if exalted or s == _MOOLA[p]:
            moods.append("Garvita")
        out[p] = Avasthas(baladi(lons[p]), jag, tuple(m for m in MOODS if m in moods))
    return out

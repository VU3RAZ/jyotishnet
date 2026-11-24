# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Rahul Sathe
"""Vimshopaka bala: a graha's dignity across groups of vargas, out of 20 points.

In each varga a graha scores 20 in its own sign, otherwise by its compound
relationship (natural + temporal) with the sign's lord: great friend 18, friend
15, neutral 10, enemy 7, great enemy 5 (BPHS ch. 7). The temporal relationship
is taken within that varga's chart. Each varga's score is weighted, and the
weights of a scheme sum to 20.

Back-solved from Jagannatha Hora's Vimsopaka table on 31 golden charts (all
1,116 values within 0.005):
- Rahu and Ketu own no sign; they treat Venus and Saturn as friends, Mercury and
  Jupiter as neutral, the Sun, Moon and Mars as enemies.
- JHora's Saptavarga weights are D1 5, D2 2, D3 3, D7 1, D9 2.5, D12 4.5, D30 2.
  BPHS gives D7 2.5, D9 4.5, D12 2, D30 1 (JHora's last four look shifted by one
  varga). Both are available; see docs/DECISIONS.md.
"""

from __future__ import annotations

from dataclasses import dataclass

from .chart import Chart
from .config import DEFAULT_CONFIG, SchoolConfig
from .constants import NATURAL_ENEMIES, NATURAL_FRIENDS, OWN_SIGNS, SIGN_LORD
from .vargas import varga_sign

GRAHAS9 = ("Su", "Mo", "Ma", "Me", "Ju", "Ve", "Sa", "Ra", "Ke")

SCHEMES: dict[str, dict[int, float]] = {
    "shadvarga": {1: 6, 2: 2, 3: 4, 9: 5, 12: 2, 30: 1},
    "saptavarga": {1: 5, 2: 2, 3: 3, 7: 2.5, 9: 4.5, 12: 2, 30: 1},
    "dashavarga": {1: 3, 2: 1.5, 3: 1.5, 7: 1.5, 9: 1.5, 10: 1.5, 12: 1.5, 16: 1.5,
                   30: 1.5, 60: 5},
    "shodashavarga": {1: 3.5, 2: 1, 3: 1, 4: 0.5, 7: 0.5, 9: 3, 10: 0.5, 12: 0.5,
                      16: 2, 20: 0.5, 24: 0.5, 27: 0.5, 30: 1, 40: 0.5, 45: 0.5, 60: 4},
}
SAPTAVARGA_JHORA = {1: 5, 2: 2, 3: 3, 7: 1, 9: 2.5, 12: 4.5, 30: 2}

POINTS = {"own": 20.0, 2: 18.0, 1: 15.0, 0: 10.0, -1: 7.0, -2: 5.0}

# Natural relationships of the nodes with the seven sign lords (JHora).
NODE_FRIENDS = ("Ve", "Sa")
NODE_ENEMIES = ("Su", "Mo", "Ma")


@dataclass(frozen=True)
class VimshopakaOptions:
    """School choices in Vimshopaka bala; defaults reproduce Jagannatha Hora."""
    # Saptavarga weights: "jhora" (D7 1, D9 2.5, D12 4.5, D30 2) or "bphs"
    # (D7 2.5, D9 4.5, D12 2, D30 1).
    saptavarga_weights: str = "jhora"


DEFAULT_VIMSHOPAKA = VimshopakaOptions()


def _natural(p: str, lord: str) -> int:
    if p in ("Ra", "Ke"):
        return 1 if lord in NODE_FRIENDS else -1 if lord in NODE_ENEMIES else 0
    return 1 if lord in NATURAL_FRIENDS[p] else -1 if lord in NATURAL_ENEMIES[p] else 0


def varga_points(p: str, signs: dict[str, int]) -> float:
    """Points (out of 20) for graha `p` in one varga, given every graha's sign there."""
    sign = signs[p]
    if p in OWN_SIGNS and sign in OWN_SIGNS[p]:
        return POINTS["own"]
    lord = SIGN_LORD[sign]
    temporal = 1 if (signs[lord] - sign) % 12 + 1 in (2, 3, 4, 10, 11, 12) else -1
    return POINTS[_natural(p, lord) + temporal]


def scheme_weights(scheme: str, options: VimshopakaOptions = DEFAULT_VIMSHOPAKA) -> dict[int, float]:
    if scheme == "saptavarga" and options.saptavarga_weights == "jhora":
        return SAPTAVARGA_JHORA
    return SCHEMES[scheme]


def vimshopaka(chart: Chart, cfg: SchoolConfig = DEFAULT_CONFIG,
               options: VimshopakaOptions = DEFAULT_VIMSHOPAKA) -> dict[str, dict[str, float]]:
    """{graha: {scheme: points out of 20}} for the nine grahas and four schemes."""
    lons = {p: chart.grahas[p].longitude for p in GRAHAS9}
    needed = sorted({n for s in SCHEMES for n in SCHEMES[s]})
    pts = {}
    for n in needed:
        signs = {p: varga_sign(lon, n, cfg.hora_scheme) for p, lon in lons.items()}
        pts[n] = {p: varga_points(p, signs) for p in GRAHAS9}
    return {p: {s: sum(w * pts[n][p] / 20 for n, w in scheme_weights(s, options).items())
                for s in SCHEMES}
            for p in GRAHAS9}

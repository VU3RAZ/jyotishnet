# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Rahul Sathe
"""Ashtakavarga per Brihat Parashara Hora Shastra (chapters 66-70).

- Bhinnashtakavarga (BAV): for each of the seven grahas, a benefic point (bindu)
  is placed in a sign when one of the eight contributors (seven grahas + Lagna)
  is in a specified house from that sign... counted from the contributor.
- Sarvashtakavarga (SAV): sum of the seven BAVs per sign (total 337).
- Trikona and Ekadhipatya shodhana reductions, then Shodhya pinda.

Signs are 0..11 from Aries. Some texts differ on a few BAV points; the
variants are listed in VARIANTS and can be switched on by name.
"""

from __future__ import annotations

from dataclasses import dataclass

from .chart import Chart
from .constants import SIGN_LORD

PLANETS7 = ["Su", "Mo", "Ma", "Me", "Ju", "Ve", "Sa"]
CONTRIBUTORS = PLANETS7 + ["La"]

# BAV_TABLE[target][contributor] = houses (1..12) counted from the contributor's sign.
BAV_TABLE: dict[str, dict[str, list[int]]] = {
    "Su": {
        "Su": [1, 2, 4, 7, 8, 9, 10, 11], "Mo": [3, 6, 10, 11],
        "Ma": [1, 2, 4, 7, 8, 9, 10, 11], "Me": [3, 5, 6, 9, 10, 11, 12],
        "Ju": [5, 6, 9, 11], "Ve": [6, 7, 12],
        "Sa": [1, 2, 4, 7, 8, 9, 10, 11], "La": [3, 4, 6, 10, 11, 12],
    },
    "Mo": {
        "Su": [3, 6, 7, 8, 10, 11], "Mo": [1, 3, 6, 7, 10, 11],
        "Ma": [2, 3, 5, 6, 9, 10, 11], "Me": [1, 3, 4, 5, 7, 8, 10, 11],
        "Ju": [1, 4, 7, 8, 10, 11, 12], "Ve": [3, 4, 5, 7, 9, 10, 11],
        "Sa": [3, 5, 6, 11], "La": [3, 6, 10, 11],
    },
    "Ma": {
        "Su": [3, 5, 6, 10, 11], "Mo": [3, 6, 11],
        "Ma": [1, 2, 4, 7, 8, 10, 11], "Me": [3, 5, 6, 11],
        "Ju": [6, 10, 11, 12], "Ve": [6, 8, 11, 12],
        "Sa": [1, 4, 7, 8, 9, 10, 11], "La": [1, 3, 6, 10, 11],
    },
    "Me": {
        "Su": [5, 6, 9, 11, 12], "Mo": [2, 4, 6, 8, 10, 11],
        "Ma": [1, 2, 4, 7, 8, 9, 10, 11], "Me": [1, 3, 5, 6, 9, 10, 11, 12],
        "Ju": [6, 8, 11, 12], "Ve": [1, 2, 3, 4, 5, 8, 9, 11],
        "Sa": [1, 2, 4, 7, 8, 9, 10, 11], "La": [1, 2, 4, 6, 8, 10, 11],
    },
    "Ju": {
        "Su": [1, 2, 3, 4, 7, 8, 9, 10, 11], "Mo": [2, 5, 7, 9, 11],
        "Ma": [1, 2, 4, 7, 8, 10, 11], "Me": [1, 2, 4, 5, 6, 9, 10, 11],
        "Ju": [1, 2, 3, 4, 7, 8, 10, 11], "Ve": [2, 5, 6, 9, 10, 11],
        "Sa": [3, 5, 6, 12], "La": [1, 2, 4, 5, 6, 7, 9, 10, 11],
    },
    "Ve": {
        "Su": [8, 11, 12], "Mo": [1, 2, 3, 4, 5, 8, 9, 11, 12],
        "Ma": [3, 5, 6, 9, 11, 12], "Me": [3, 5, 6, 9, 11],
        "Ju": [5, 8, 9, 10, 11], "Ve": [1, 2, 3, 4, 5, 8, 9, 10, 11],
        "Sa": [3, 4, 5, 8, 9, 10, 11], "La": [1, 2, 3, 4, 5, 8, 9, 11],
    },
    "Sa": {
        "Su": [1, 2, 4, 7, 8, 10, 11], "Mo": [3, 6, 11],
        "Ma": [3, 5, 6, 10, 11, 12], "Me": [6, 8, 9, 10, 11, 12],
        "Ju": [5, 6, 11, 12], "Ve": [6, 11, 12],
        "Sa": [3, 5, 6, 11], "La": [1, 3, 4, 6, 10, 11],
    },
}

# Textual variants. "bphs" is the table above (B. V. Raman's reading of BPHS);
# "pvr" follows PVR Narasimha Rao (also PyJHora's default). Totals are unchanged.
VARIANTS: dict[str, list[tuple[str, str, int, bool]]] = {
    "bphs": [],
    "pvr": [
        ("Mo", "Mo", 9, True), ("Mo", "Ma", 9, False),
        ("Mo", "Ju", 2, True), ("Mo", "Ju", 12, False),
        ("Ve", "Ma", 4, True), ("Ve", "Ma", 5, False),
    ],
}


def bav_table(variant: str = "bphs") -> dict[str, dict[str, list[int]]]:
    table = {t: {c: list(h) for c, h in row.items()} for t, row in BAV_TABLE.items()}
    for target, contrib, house, add in VARIANTS[variant]:
        houses = set(table[target][contrib])
        houses.add(house) if add else houses.discard(house)
        table[target][contrib] = sorted(houses)
    return table


BAV_TOTALS = {"Su": 48, "Mo": 49, "Ma": 39, "Me": 54, "Ju": 56, "Ve": 52, "Sa": 39}

# Shodhya pinda multipliers.
RASI_MULTIPLIER = [7, 10, 8, 4, 10, 5, 7, 8, 9, 5, 11, 12]   # Virgo 5 (6 in some books)
GRAHA_MULTIPLIER = {"Su": 5, "Mo": 5, "Ma": 8, "Me": 5, "Ju": 10, "Ve": 7, "Sa": 5}


@dataclass
class Ashtakavarga:
    bav: dict[str, list[int]]                  # graha -> 12 bindu counts by sign
    sav: list[int]                             # 12 totals by sign
    prastara: dict[str, dict[str, list[int]]]  # graha -> contributor -> 0/1 by sign
    bav_trikona: dict[str, list[int]]
    bav_reduced: dict[str, list[int]]          # after trikona + ekadhipatya
    rasi_pinda: dict[str, int]
    graha_pinda: dict[str, int]
    shodhya_pinda: dict[str, int]


def _positions(chart: Chart) -> dict[str, int]:
    pos = {k: chart.grahas[k].sign for k in PLANETS7}
    pos["La"] = chart.lagna.sign
    return pos


def bhinnashtakavarga(positions: dict[str, int], variant: str = "bphs"
                      ) -> tuple[dict[str, list[int]], dict]:
    table = bav_table(variant)
    bav: dict[str, list[int]] = {}
    prastara: dict[str, dict[str, list[int]]] = {}
    for target in PLANETS7:
        row = [0] * 12
        prastara[target] = {}
        for contrib in CONTRIBUTORS:
            marks = [0] * 12
            for h in table[target][contrib]:
                s = (positions[contrib] + h - 1) % 12
                marks[s] = 1
                row[s] += 1
            prastara[target][contrib] = marks
        bav[target] = row
    return bav, prastara


def trikona_shodhana(row: list[int]) -> list[int]:
    """In each trine (signs 4 apart): all equal -> all 0; else subtract the minimum."""
    out = list(row)
    for start in range(4):
        idx = [start, start + 4, start + 8]
        vals = [row[i] for i in idx]
        m = min(vals)
        if vals[0] == vals[1] == vals[2]:
            for i in idx:
                out[i] = 0
        elif m > 0:
            for i in idx:
                out[i] = row[i] - m
    return out


# Sign pairs owned by one graha (Cancer and Leo are single-owner and exempt).
_PAIRS = [(0, 7), (1, 6), (2, 5), (8, 11), (9, 10)]


def ekadhipatya_shodhana(row: list[int], occupied: set[int]) -> list[int]:
    """Reduction between two signs of the same lord (applied after trikona).

    Rules (BPHS, as summarised by B. V. Raman and PVR Narasimha Rao):
    - either sign at 0, or both signs occupied by grahas: no change;
    - neither occupied: equal -> both 0, unequal -> the larger becomes the smaller;
    - one occupied: if the empty sign has fewer or equal points it becomes 0;
      if more, it is set equal to the occupied sign (the printed rule; the
      equal case follows secondary sources, as PyJHora does).

    Which signs count as "occupied" is a school choice; see `ashtakavarga()`.
    """
    out = list(row)
    for a, b in _PAIRS:
        va, vb = out[a], out[b]
        if va == 0 or vb == 0:
            continue
        oa, ob = a in occupied, b in occupied
        if oa and ob:
            continue
        if not oa and not ob:
            if va == vb:
                out[a] = out[b] = 0
            else:
                out[a] = out[b] = min(va, vb)
            continue
        occ, emp = (a, b) if oa else (b, a)
        if out[emp] <= out[occ]:
            out[emp] = 0
        else:
            out[emp] = out[occ]
    return out


def ashtakavarga(chart: Chart, variant: str = "bphs", virgo_multiplier: int = 5,
                 occupancy: str = "grahas7") -> Ashtakavarga:
    """Full Ashtakavarga.

    occupancy decides which signs count as occupied in Ekadhipatya shodhana:
    "grahas7" (Sun..Saturn), "grahas9" (with Rahu and Ketu) or "all"
    (nine grahas and the Lagna, as PyJHora does).
    """
    pos = _positions(chart)
    bav, prastara = bhinnashtakavarga(pos, variant)
    sav = [sum(bav[g][s] for g in PLANETS7) for s in range(12)]

    occupied = {pos[g] for g in PLANETS7}
    if occupancy in ("grahas9", "all"):
        occupied |= {chart.grahas["Ra"].sign, chart.grahas["Ke"].sign}
    if occupancy == "all":
        occupied.add(chart.lagna.sign)
    rasi_mult = list(RASI_MULTIPLIER)
    rasi_mult[5] = virgo_multiplier

    trik = {g: trikona_shodhana(bav[g]) for g in PLANETS7}
    reduced = {g: ekadhipatya_shodhana(trik[g], occupied) for g in PLANETS7}

    rasi_p, graha_p, shodhya = {}, {}, {}
    for g in PLANETS7:
        r = reduced[g]
        rasi_p[g] = sum(r[s] * rasi_mult[s] for s in range(12))
        graha_p[g] = sum(r[pos[p]] * GRAHA_MULTIPLIER[p] for p in PLANETS7)
        shodhya[g] = rasi_p[g] + graha_p[g]
    return Ashtakavarga(bav, sav, prastara, trik, reduced, rasi_p, graha_p, shodhya)


def sign_lord_pairs() -> list[tuple[int, int, str]]:
    return [(a, b, SIGN_LORD[a]) for a, b in _PAIRS]

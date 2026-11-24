# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Rahul Sathe
"""Bhava bala: the strength of each of the twelve houses (BPHS ch. 27).

Three parts, in virupas:
- Bhavadhipati bala: the total Shadbala of the house's lord.
- Bhava dig bala: by the class of the house's sign. Human signs are strongest in
  the 1st house, water signs in the 4th, four-footed signs in the 10th and
  Scorpio (keeta) in the 7th: 60 virupas there, 10 less for each house away, 0
  in the opposite house.
- Bhava drik bala: aspects on the house's middle. Jupiter and Mercury add their
  full aspect, other benefics a quarter, malefics take away a quarter.

The details follow Jagannatha Hora 8.0's code (read from jhora.exe):
- Houses are equal, the middle of each at the Lagna's degree in the sign
  counted from the Lagna sign (Lagna + 30 deg x n).
- Sign classes: human Gemini, Virgo, Libra, Aquarius; water Cancer, Pisces;
  four-footed Aries, Taurus, Leo; Scorpio keeta. Sagittarius is human and
  Capricorn four-footed while the Lagna is in the first 15 deg of its sign;
  from 15 deg on, Sagittarius is four-footed and Capricorn a water sign.
- Aspects are Drik bala's (`drishti_value_jhora` by default); the Moon and
  Mercury are benefic or malefic as in Shadbala, but Mercury's full aspect is
  added whatever its nature. Rahu and Ketu do not aspect.
- The lord's strength is its Shadbala total, which here includes Yuddha bala
  (JHora applies none; decision "Yuddha").
"""

from __future__ import annotations

from dataclasses import dataclass

from .chart import Chart
from .config import DEFAULT_CONFIG, SchoolConfig
from .constants import SIGN_LORD
from .shadbala import (DEFAULT_OPTIONS, PLANETS7, ShadbalaOptions, drishti_value,
                       drishti_value_jhora, mercury_is_malefic, moon_is_benefic, shadbala)
from .timeutil import BirthData

HUMAN, WATER, QUADRUPED, KEETA = "human", "water", "quadruped", "keeta"
# House (0 = 1st) where each class is strongest.
STRONGEST = {HUMAN: 0, WATER: 3, QUADRUPED: 9, KEETA: 6}
_CLASS = [QUADRUPED, QUADRUPED, HUMAN, WATER, QUADRUPED, HUMAN,
          HUMAN, KEETA, None, None, HUMAN, WATER]


@dataclass(frozen=True)
class HouseStrength:
    house: int          # 1..12
    sign: int           # 0..11
    lord: str
    adhipati: float     # lord's Shadbala, virupas
    dig: float
    drik: float

    @property
    def total(self) -> float:
        return self.adhipati + self.dig + self.drik

    @property
    def rupas(self) -> float:
        return self.total / 60.0


def sign_class(sign: int, lagna_degree: float) -> str:
    """Class of a sign for Bhava dig bala; Sagittarius and Capricorn change at the
    Lagna's 15th degree (JHora)."""
    if sign == 8:
        return HUMAN if lagna_degree < 15.0 else QUADRUPED
    if sign == 9:
        return QUADRUPED if lagna_degree < 15.0 else WATER
    return _CLASS[sign]


def bhava_dig_bala(house: int, sign: int, lagna_degree: float) -> float:
    """Virupas for house (0 = 1st) holding `sign`."""
    k = (house - STRONGEST[sign_class(sign, lagna_degree)]) % 12
    return 60.0 - 10.0 * min(k, 12 - k)


def bhava_drik_bala(point: float, lons: dict[str, float], benefic: dict[str, bool],
                    method: str = "jhora") -> float:
    value = drishti_value_jhora if method == "jhora" else drishti_value
    s = 0.0
    for p in PLANETS7:
        v = value(p, point - lons[p])
        if p in ("Ju", "Me"):
            s += v
        elif benefic[p]:
            s += v / 4.0
        else:
            s -= v / 4.0
    return s


def bhava_bala(chart: Chart, birth: BirthData, cfg: SchoolConfig = DEFAULT_CONFIG,
               opts: ShadbalaOptions = DEFAULT_OPTIONS) -> list[HouseStrength]:
    """The twelve houses' strengths, 1st house first."""
    strengths = shadbala(chart, birth, cfg, opts)
    lons = {p: chart.grahas[p].longitude for p in PLANETS7}
    moon_good = moon_is_benefic(lons["Su"], lons["Mo"], opts.moon_benefic)
    me_malefic = mercury_is_malefic({p: g.sign for p, g in chart.grahas.items()}, moon_good, opts,
                                    lons={p: g.longitude for p, g in chart.grahas.items()})
    benefic = {"Su": False, "Mo": moon_good, "Ma": False, "Me": not me_malefic,
               "Ju": True, "Ve": True, "Sa": False}
    asc = chart.lagna.longitude
    lagna_sign, lagna_degree = int(asc // 30), asc % 30
    out = []
    for h in range(12):
        sign = (lagna_sign + h) % 12
        lord = SIGN_LORD[sign]
        out.append(HouseStrength(
            house=h + 1, sign=sign, lord=lord, adhipati=strengths[lord].total,
            dig=bhava_dig_bala(h, sign, lagna_degree),
            drik=bhava_drik_bala((asc + 30.0 * h) % 360, lons, benefic, opts.drishti)))
    return out

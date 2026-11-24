# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Rahul Sathe
"""Shadbala (six-fold strength) per Brihat Parashara Hora Shastra, chapter 27.

All values are in virupas (shashtiamsas); 60 virupas = 1 rupa.

Components implemented here:
- Sthana bala: Uchcha, Saptavargaja, Ojayugma, Kendra, Drekkana
- Dig bala
- Kala bala: Nathonnatha, Paksha, Tribhaga, Abda, Masa, Vara, Hora, Ayana
  (Yuddha bala is not yet implemented and is reported as 0)
- Cheshta bala (Sun: Ayana bala; Moon: Paksha bala; others: cheshta kendra
  from modern mean elements)
- Naisargika bala
- Drik bala

Points where texts and software differ are parameters with the default noted.
Every number here should be checked against Jagannatha Hora reference charts
(tests/golden) before it is relied on; this module has no external oracle yet.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

from .chart import Chart
from .config import SchoolConfig, DEFAULT_CONFIG
from .constants import (
    EXALTATION, MOOLATRIKONA, NATURAL_ENEMIES, NATURAL_FRIENDS, OWN_SIGNS, SIGN_LORD,
    is_odd_sign,
)
from .ephemeris import declination, midheaven, previous_sunrise, sun_event_after
from .timeutil import BirthData
from .vargas import varga_sign

PLANETS7 = ["Su", "Mo", "Ma", "Me", "Ju", "Ve", "Sa"]

NAISARGIKA = {"Su": 60.0, "Mo": 360 / 7, "Ve": 300 / 7, "Ju": 240 / 7,
              "Me": 180 / 7, "Ma": 120 / 7, "Sa": 60 / 7}

# Minimum required Shadbala in rupas (BPHS 27).
REQUIRED_RUPAS = {"Su": 5.0, "Mo": 6.0, "Ma": 5.0, "Me": 7.0, "Ju": 6.5, "Ve": 5.5, "Sa": 5.0}

SAPTAVARGA = [1, 2, 3, 7, 9, 12, 30]
SAPTAVARGA_POINTS = {"moolatrikona": 45.0, "own": 30.0, "great_friend": 22.5, "friend": 15.0,
                     "neutral": 7.5, "enemy": 3.75, "great_enemy": 1.875}

# Hora sequence (descending orbital speed) and weekday lords (Sunday = 0).
HORA_ORDER = ["Sa", "Ju", "Ma", "Su", "Ve", "Me", "Mo"]
WEEKDAY_LORD = ["Su", "Mo", "Ma", "Me", "Ju", "Ve", "Sa"]

# Kali Yuga epoch for Ahargana (midnight at Ujjain, 18 February 3102 BCE), used for
# Abda and Masa lords. Sources differ on the epoch; this is a parameter.
KALI_EPOCH_JD = 588465.5

# J2000 mean longitudes (deg) and rates (deg per Julian century), Standish (JPL),
# valid 1800-2050 to well under a degree: ample for cheshta kendra.
_MEAN_ELEMENTS = {
    "Me": (252.25032350, 149472.67411175), "Ve": (181.97909950, 58517.81538729),
    "Ea": (100.46457166, 35999.37244981), "Ma": (-4.55343205, 19140.30268499),
    "Ju": (34.39644051, 3034.74612775), "Sa": (49.95424423, 1222.49362201),
}


@dataclass
class PlanetStrength:
    sthana: dict[str, float] = field(default_factory=dict)
    dig: float = 0.0
    kala: dict[str, float] = field(default_factory=dict)
    cheshta: float = 0.0
    naisargika: float = 0.0
    drik: float = 0.0

    @property
    def total(self) -> float:
        return (sum(self.sthana.values()) + self.dig + sum(self.kala.values())
                + self.cheshta + self.naisargika + self.drik)

    @property
    def rupas(self) -> float:
        return self.total / 60.0


# --------------------------------------------------------------- relationships

def _natural(p: str, other: str) -> int:
    """+1 friend, 0 neutral, -1 enemy."""
    if other in NATURAL_FRIENDS[p]:
        return 1
    if other in NATURAL_ENEMIES[p]:
        return -1
    return 0


def _temporal(p: str, other: str, signs: dict[str, int]) -> int:
    """Tatkalika: friend if `other` is in the 2,3,4,10,11,12th from `p` in D1."""
    h = (signs[other] - signs[p]) % 12 + 1
    return 1 if h in (2, 3, 4, 10, 11, 12) else -1


def compound_relation(p: str, other: str, signs: dict[str, int]) -> str:
    score = _natural(p, other) + _temporal(p, other, signs)
    return {2: "great_friend", 1: "friend", 0: "neutral", -1: "enemy", -2: "great_enemy"}[score]


# ---------------------------------------------------------------- sthana bala

def uchcha_bala(p: str, lon: float) -> float:
    ex_sign, ex_deg = EXALTATION[p]
    deb = (ex_sign * 30 + ex_deg + 180) % 360
    d = abs(lon - deb) % 360
    return min(d, 360 - d) / 3.0


def saptavargaja_bala(p: str, lon: float, d1_signs: dict[str, int]) -> float:
    total = 0.0
    for n in SAPTAVARGA:
        sign = varga_sign(lon, n)
        if n == 1:
            mt_sign, mt_a, mt_b = MOOLATRIKONA[p]
            if sign == mt_sign and mt_a <= lon % 30 < mt_b:
                total += SAPTAVARGA_POINTS["moolatrikona"]
                continue
        if sign in OWN_SIGNS[p]:
            total += SAPTAVARGA_POINTS["own"]
            continue
        lord = SIGN_LORD[sign]
        total += SAPTAVARGA_POINTS[compound_relation(p, lord, d1_signs)]
    return total


def ojayugma_bala(p: str, lon: float) -> float:
    female = p in ("Mo", "Ve")
    pts = 0.0
    for n in (1, 9):
        odd = is_odd_sign(varga_sign(lon, n))
        if odd != female:
            pts += 15.0
    return pts


def kendra_bala(house: int) -> float:
    if house in (1, 4, 7, 10):
        return 60.0
    if house in (2, 5, 8, 11):
        return 30.0
    return 15.0


def drekkana_bala(p: str, lon: float) -> float:
    part = int((lon % 30) // 10)
    want = {"Su": 0, "Ma": 0, "Ju": 0, "Me": 1, "Sa": 1, "Mo": 2, "Ve": 2}[p]
    return 15.0 if part == want else 0.0


# ------------------------------------------------------------------ dig bala

def dig_bala(p: str, lon: float, asc: float, mc: float) -> float:
    strongest = {"Ju": asc, "Me": asc, "Su": mc, "Ma": mc,
                 "Sa": (asc + 180) % 360, "Mo": (mc + 180) % 360, "Ve": (mc + 180) % 360}[p]
    weakest = (strongest + 180) % 360
    d = abs(lon - weakest) % 360
    return min(d, 360 - d) / 3.0


# ----------------------------------------------------------------- kala bala

def _arc(a: float, b: float) -> float:
    d = abs(a - b) % 360
    return min(d, 360 - d)


def paksha_values(sun: float, moon: float, mercury_malefic: bool) -> dict[str, float]:
    elong = (moon - sun) % 360
    benefic_pts = _arc(moon, sun) / 3.0
    waxing = elong < 180
    out = {}
    for p in PLANETS7:
        if p == "Mo":
            out[p] = 2 * (benefic_pts if waxing else 60 - benefic_pts)
        elif p in ("Ju", "Ve") or (p == "Me" and not mercury_malefic):
            out[p] = benefic_pts
        else:
            out[p] = 60 - benefic_pts
    return out


def _weekday(jd_civil_midnight: float) -> int:
    """Weekday (Sunday = 0) of the civil day starting at this Julian day (x.5)."""
    return int(math.floor(jd_civil_midnight + 1.5)) % 7


def kala_components(birth: BirthData, chart: Chart, cfg: SchoolConfig,
                    mercury_malefic: bool) -> dict[str, dict[str, float]]:
    jd = chart.jd_ut
    lat, lon, alt = birth.latitude, birth.longitude, birth.altitude_m

    # Nathonnatha: distance from apparent midnight (Sun's lower transit).
    lower = sun_event_after(jd - 1.0, lat, lon, alt, cfg, "lower")
    while True:
        nxt = sun_event_after(lower + 0.01, lat, lon, alt, cfg, "lower")
        if nxt > jd:
            break
        lower = nxt
    hours = (jd - lower) * 24.0
    from_midnight = hours if hours <= 12 else 24 - hours
    day_pts = 60.0 * from_midnight / 12.0

    # Day/night and tribhaga.
    sunrise = previous_sunrise(jd, lat, lon, alt, cfg)
    sunset = sun_event_after(sunrise, lat, lon, alt, cfg, "set")
    next_rise = sun_event_after(sunrise + 0.01, lat, lon, alt, cfg, "rise")
    is_day = jd < sunset
    if is_day:
        third = int(3 * (jd - sunrise) / (sunset - sunrise))
        tribhaga_lord = ["Me", "Su", "Sa"][min(third, 2)]
    else:
        third = int(3 * (jd - sunset) / (next_rise - sunset))
        tribhaga_lord = ["Mo", "Ve", "Ma"][min(third, 2)]

    # Vara: weekday of the Vedic day, which begins at sunrise.
    sunrise_local_day = math.floor(sunrise + 0.5 + lon / 360.0) - 0.5
    vara_lord = WEEKDAY_LORD[_weekday(sunrise_local_day)]

    # Hora: equal 60-minute horas counted from sunrise, starting with the vara lord.
    hora_idx = int((jd - sunrise) * 24.0)
    start = HORA_ORDER.index(vara_lord)
    hora_lord = HORA_ORDER[(start + hora_idx) % 7]

    # Abda and Masa: weekday on which the current 360-day year / 30-day month began.
    ahargana = int(math.floor(sunrise_local_day + 0.5 - KALI_EPOCH_JD))
    year_start = sunrise_local_day - (ahargana % 360)
    month_start = sunrise_local_day - (ahargana % 30)
    abda_lord = WEEKDAY_LORD[_weekday(year_start)]
    masa_lord = WEEKDAY_LORD[_weekday(month_start)]

    sun = chart.grahas["Su"].longitude
    moon = chart.grahas["Mo"].longitude
    paksha = paksha_values(sun, moon, mercury_malefic)

    out: dict[str, dict[str, float]] = {}
    for p in PLANETS7:
        if p == "Me":
            nath = 60.0
        elif p in ("Su", "Ju", "Ve"):
            nath = day_pts
        else:
            nath = 60.0 - day_pts
        dec = declination(jd, p, cfg)
        if p in ("Mo", "Sa"):
            ayana = (24.0 - dec) / 48.0 * 60.0
        elif p == "Me":
            ayana = (24.0 + abs(dec)) / 48.0 * 60.0
        else:
            ayana = (24.0 + dec) / 48.0 * 60.0
        if p == "Su":
            ayana *= 2
        out[p] = {
            "nathonnatha": nath,
            "paksha": paksha[p],
            "tribhaga": 60.0 if (p == "Ju" or p == tribhaga_lord) else 0.0,
            "abda": 15.0 if p == abda_lord else 0.0,
            "masa": 30.0 if p == masa_lord else 0.0,
            "vara": 45.0 if p == vara_lord else 0.0,
            "hora": 60.0 if p == hora_lord else 0.0,
            "ayana": ayana,
            "yuddha": 0.0,
        }
    out["_meta"] = {"is_day": float(is_day), "vara": vara_lord, "hora": hora_lord,
                    "abda": abda_lord, "masa": masa_lord, "tribhaga": tribhaga_lord}  # type: ignore[dict-item]
    return out


# --------------------------------------------------------------- cheshta bala

def _mean_lon(code: str, jd: float) -> float:
    t = (jd - 2451545.0) / 36525.0
    l0, rate = _MEAN_ELEMENTS[code]
    return (l0 + rate * t) % 360


def cheshta_bala(p: str, jd: float, true_tropical: float, kala: dict[str, dict[str, float]]) -> float:
    if p == "Su":
        return kala["Su"]["ayana"] / 2.0     # Sun's own Ayana bala (undoubled)
    if p == "Mo":
        return kala["Mo"]["paksha"] / 2.0    # Moon's own Paksha bala (undoubled)
    mean_sun = (_mean_lon("Ea", jd) + 180) % 360
    if p in ("Ma", "Ju", "Sa"):
        mean, seeghrocha = _mean_lon(p, jd), mean_sun
    else:  # Mercury, Venus
        mean, seeghrocha = mean_sun, _mean_lon(p, jd)
    mid = (mean + true_tropical) / 2.0
    if abs(mean - true_tropical) > 180:   # average across the 0/360 seam
        mid = (mid + 180) % 360
    k = (seeghrocha - mid) % 360
    if k > 180:
        k = 360 - k
    return k / 3.0


# ------------------------------------------------------------------ drik bala

def drishti_value(aspecting: str, d: float) -> float:
    """Aspect strength (virupas) of `aspecting` on a point d degrees ahead of it."""
    d %= 360
    if d < 30 or d >= 300:
        v = 0.0
    elif d < 60:
        v = (d - 30) / 2
    elif d < 90:
        v = d - 60 + 15
    elif d < 120:
        v = (120 - d) / 2 + 30
    elif d < 150:
        v = 150 - d
    elif d < 180:
        v = (d - 150) * 2
    else:
        v = (300 - d) / 2
    if aspecting == "Ma" and (90 <= d < 120 or 210 <= d < 240):
        v += 15
    elif aspecting == "Ju" and (120 <= d < 150 or 240 <= d < 270):
        v += 30
    elif aspecting == "Sa" and (60 <= d < 90 or 270 <= d < 300):
        v += 45
    return min(v, 60.0)


def drik_bala(lons: dict[str, float], benefic: dict[str, bool]) -> dict[str, float]:
    out = {}
    for target in PLANETS7:
        s = 0.0
        for src in PLANETS7:
            if src == target:
                continue
            v = drishti_value(src, lons[target] - lons[src])
            s += v if benefic[src] else -v
        out[target] = s / 4.0
    return out


# --------------------------------------------------------------------- total

def shadbala(chart: Chart, birth: BirthData, cfg: SchoolConfig = DEFAULT_CONFIG
             ) -> dict[str, PlanetStrength]:
    lons = {p: chart.grahas[p].longitude for p in PLANETS7}
    d1 = {p: chart.grahas[p].sign for p in chart.grahas}
    # Mercury is treated as malefic when it shares a sign with Mars, Saturn,
    # Rahu or Ketu (the Sun is excluded: Mercury is never far from it).
    mercury_malefic = any(d1[m] == d1["Me"] for m in ("Ma", "Sa", "Ra", "Ke"))
    waxing = (lons["Mo"] - lons["Su"]) % 360 < 180
    benefic = {"Su": False, "Mo": waxing, "Ma": False, "Me": not mercury_malefic,
               "Ju": True, "Ve": True, "Sa": False}

    asc = chart.lagna.longitude
    mc = midheaven(chart.jd_ut, birth.latitude, birth.longitude, cfg)
    kala = kala_components(birth, chart, cfg, mercury_malefic)
    drik = drik_bala(lons, benefic)
    ayan = chart.ayanamsa

    out: dict[str, PlanetStrength] = {}
    for p in PLANETS7:
        lon = lons[p]
        ps = PlanetStrength()
        ps.sthana = {
            "uchcha": uchcha_bala(p, lon),
            "saptavargaja": saptavargaja_bala(p, lon, d1),
            "ojayugma": ojayugma_bala(p, lon),
            "kendra": kendra_bala(chart.grahas[p].house),
            "drekkana": drekkana_bala(p, lon),
        }
        ps.dig = dig_bala(p, lon, asc, mc)
        ps.kala = dict(kala[p])
        ps.cheshta = cheshta_bala(p, chart.jd_ut, (lon + ayan) % 360, kala)
        ps.naisargika = NAISARGIKA[p]
        ps.drik = drik[p]
        out[p] = ps
    return out

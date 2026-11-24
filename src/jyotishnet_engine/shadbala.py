# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Rahul Sathe
"""Shadbala (six-fold strength) per Brihat Parashara Hora Shastra, chapter 27.

All values are in virupas (shashtiamsas); 60 virupas = 1 rupa.

Components implemented here:
- Sthana bala: Uchcha, Saptavargaja, Ojayugma, Kendra, Drekkana
- Dig bala
- Kala bala: Nathonnatha, Paksha, Tribhaga, Abda, Masa, Vara, Hora, Ayana
  and Yuddha (planetary war between Mars, Mercury, Jupiter, Venus and Saturn)
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


@dataclass(frozen=True)
class ShadbalaOptions:
    """School choices inside Shadbala. Defaults reproduce Jagannatha Hora where the
    golden set shows its convention (see docs/DECISIONS.md)."""
    # Moon is benefic when "waxing" (elongation < 180), or per "ashtami": from Shukla
    # Ashtami to Krishna Ashtami, i.e. at least 90 degrees from the Sun.
    moon_benefic: str = "ashtami"
    # Mercury's nature.
    # "jhora" (as Jagannatha Hora 8.0's code, read from jhora.exe): the Sun, Moon,
    #   Mars, Jupiter, Venus and Saturn score +1 if benefic, -1 if malefic (the Moon by
    #   `moon_benefic`). Each adds its score when Mercury is within 15 deg of it or
    #   165-195 deg from it, and 0.75 x its score when Mercury falls within 15 deg of
    #   its special aspect (Mars 90/210, Jupiter 120/240, Saturn 60/270 deg ahead of
    #   it); one planet can add more than once. Mercury is malefic when the total is
    #   negative, or zero with at least one planet counted; untouched, it is benefic.
    #   The nodes are not counted (decision "Shadbala benefics").
    # "bhava": the same count among grahas in Mercury's equal bhava (Lagna at the
    #   middle of the 1st, each Lagna + 30n +/- 15 deg), alone or a tie benefic; fitted
    #   to 13 charts, failed edge_42 and edge_43.
    # "majority": the same count by sign, alone or a tie benefic.
    # "any": malefic with any of `mercury_malefic_with` in its sign (Moon only when
    #   malefic).
    mercury_rule: str = "jhora"
    mercury_malefic_with: tuple[str, ...] = ("Mo", "Ma", "Sa", "Ra", "Ke")
    # Days added to the Kali-epoch ahargana for Abda and Masa lords. -13 is the only
    # value (mod 360) that reproduces JHora's year and month lords on all five golden
    # Shadbala charts; +1 matched the first three but not edge_06 (1990-01-10).
    ahargana_offset_days: int = -13
    # Temporal relationships for Saptavargaja: from D1 ("d1") or within each varga.
    saptavarga_relation: str = "d1"
    # Dig bala's 10th/4th points: "lagna" = Lagna -/+ 90 deg (JHora; back-solved from
    # golden charts edge_18-20, where the meridian is 16 deg away) or "meridian" (MC/IC).
    dig_tenth: str = "lagna"
    # Nathonnatha: "lagna" = from the Sun's distance to Lagna - 90 deg (JHora: equals
    # the Sun's Dig bala; matches all 6 charts with Kaala Bala tables) or "time" =
    # hours from apparent midnight (the Sun's lower transit), as BPHS describes.
    nathonnatha: str = "lagna"
    # Drishti (aspect) strength for Drik bala: "jhora" = straight lines between the
    # BPHS values at every 30 deg, with a special aspect's point raised to 60 (Mars
    # 90/210, Jupiter 120/240, Saturn 60/270); fitted to JHora's Drik bala on 9
    # golden charts. "bphs_add" = the base curve plus BPHS's flat additions (+15
    # Mars, +30 Jupiter, +45 Saturn) in the special-aspect signs.
    drishti: str = "jhora"
    # Declination for Ayana bala: "kranti" = BPHS kranti table (24 deg maximum, by
    # 15-degree steps, linear between) from the tropical longitude, ecliptic latitude
    # ignored; within 0.73 virupa of JHora on 70 values (decision #13). "true" = the
    # ephemeris declination, which lets the Moon pass 24 deg at a lunar standstill.
    ayana_declination: str = "kranti"
    # Longitude fed to the kranti table: sidereal + this many degrees (JHora: a fixed
    # 23 deg, back-solved from 20 golden charts 1965-2001, where the needed shift was
    # exactly the chart's ayanamsa - 23), or None for the true tropical longitude
    # (sidereal + the chart's ayanamsa).
    ayana_fixed_ayanamsa: float | None = 23.0
    # Moon's Cheshta: "elongation" (arc from the Sun / 3) or "paksha" (its Paksha bala).
    moon_cheshta: str = "elongation"
    # Sun's Cheshta: "jhora" = the Sun's arc from the winter solstice point taken as
    # sidereal 270 - `ayana_fixed_ayanamsa` (247 deg with 23), / 3; read from
    # jhora.exe, exact on 23 golden charts. "ayana" = half its (doubled) Ayana bala.
    sun_cheshta: str = "jhora"
    # Whether the Sun's and Moon's Cheshta count in their Shadbala totals. JHora
    # shows them but leaves them out of the totals (read from jhora.exe; the totals
    # then match within JHora's rounding on 23 charts), as BPHS's Cheshta stands in
    # for the luminaries' Ayana and Paksha bala, which are already counted.
    luminary_cheshta_in_total: bool = False
    # Planetary war: two of Ma, Me, Ju, Ve, Sa within this many degrees of longitude.
    yuddha_orb: float = 1.0


DEFAULT_OPTIONS = ShadbalaOptions()


@dataclass
class PlanetStrength:
    sthana: dict[str, float] = field(default_factory=dict)
    dig: float = 0.0
    kala: dict[str, float] = field(default_factory=dict)
    cheshta: float = 0.0
    naisargika: float = 0.0
    drik: float = 0.0
    cheshta_counted: bool = True     # False: shown but left out of the total

    @property
    def total(self) -> float:
        return (sum(self.sthana.values()) + self.dig + sum(self.kala.values())
                + (self.cheshta if self.cheshta_counted else 0.0) + self.naisargika + self.drik)

    @property
    def ishta(self) -> float:
        """Ishta phala: sqrt(Uchcha bala x Cheshta bala) (BPHS ch. 27; JHora)."""
        return math.sqrt(max(self.sthana["uchcha"], 0.0) * max(self.cheshta, 0.0))

    @property
    def kashta(self) -> float:
        """Kashta phala: sqrt((60 - Uchcha) x (60 - Cheshta))."""
        return math.sqrt(max(60.0 - self.sthana["uchcha"], 0.0) * max(60.0 - self.cheshta, 0.0))

    @property
    def rupas(self) -> float:
        return self.total / 60.0


# Disc diameters (bimba) in seconds of arc, BPHS ch. 27.
DISC_DIAMETER = {"Ma": 9.4, "Me": 6.6, "Ju": 190.4, "Ve": 16.6, "Sa": 158.0}
WAR_PLANETS = ("Ma", "Me", "Ju", "Ve", "Sa")
# Kala components counted "up to Hora bala" (BPHS order; Ayana and Yuddha excluded).
_PRE_YUDDHA_KALA = ("nathonnatha", "paksha", "tribhaga", "abda", "masa", "vara", "hora")


@dataclass
class PlanetaryWar:
    winner: str
    loser: str
    separation: float        # degrees of longitude
    yuddha_bala: float       # virupas added to the winner and taken from the loser


def planetary_wars(lons: dict[str, float], orb: float = 1.0) -> list[tuple[str, str, float]]:
    """Pairs of Ma, Me, Ju, Ve, Sa closer than `orb` degrees."""
    out = []
    for i, a in enumerate(WAR_PLANETS):
        for b in WAR_PLANETS[i + 1:]:
            d = _arc(lons[a], lons[b])
            if d < orb:
                out.append((a, b, d))
    return out


def yuddha_bala(strengths: dict[str, "PlanetStrength"], lons: dict[str, float],
                orb: float = 1.0) -> list[PlanetaryWar]:
    """Apply Yuddha bala in place (BPHS ch. 27).

    For each pair at war, add Sthana, Dig and Kala bala up to Hora bala; the
    difference of the two totals divided by the difference of their disc
    diameters is the Yuddha bala, added to the stronger planet (the winner)
    and subtracted from the weaker one.
    """
    wars = []
    for a, b, d in planetary_wars(lons, orb):
        tot = {p: sum(strengths[p].sthana.values()) + strengths[p].dig
               + sum(strengths[p].kala[k] for k in _PRE_YUDDHA_KALA) for p in (a, b)}
        winner, loser = (a, b) if tot[a] >= tot[b] else (b, a)
        yb = abs(tot[a] - tot[b]) / abs(DISC_DIAMETER[a] - DISC_DIAMETER[b])
        strengths[winner].kala["yuddha"] += yb
        strengths[loser].kala["yuddha"] -= yb
        wars.append(PlanetaryWar(winner, loser, d, yb))
    return wars


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


def saptavargaja_bala(p: str, lon: float, d1_signs: dict[str, int],
                      varga_signs: dict[int, dict[str, int]] | None = None,
                      hora_scheme: str = "uma_shambhu") -> float:
    total = 0.0
    for n in SAPTAVARGA:
        rel_signs = varga_signs[n] if varga_signs else d1_signs
        sign = varga_sign(lon, n, hora_scheme)
        if n == 1:
            mt_sign, mt_a, mt_b = MOOLATRIKONA[p]
            if sign == mt_sign and mt_a <= lon % 30 < mt_b:
                total += SAPTAVARGA_POINTS["moolatrikona"]
                continue
        if sign in OWN_SIGNS[p]:
            total += SAPTAVARGA_POINTS["own"]
            continue
        lord = SIGN_LORD[sign]
        total += SAPTAVARGA_POINTS[compound_relation(p, lord, rel_signs)]
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


def moon_is_benefic(sun: float, moon: float, rule: str = "ashtami") -> bool:
    if rule == "waxing":
        return (moon - sun) % 360 < 180
    return _arc(moon, sun) >= 90.0


def paksha_values(sun: float, moon: float, mercury_malefic: bool,
                  moon_rule: str = "waxing") -> dict[str, float]:
    benefic_pts = _arc(moon, sun) / 3.0
    moon_good = moon_is_benefic(sun, moon, moon_rule)
    out = {}
    for p in PLANETS7:
        if p == "Mo":
            out[p] = 2 * (benefic_pts if moon_good else 60 - benefic_pts)
        elif p in ("Ju", "Ve") or (p == "Me" and not mercury_malefic):
            out[p] = benefic_pts
        else:
            out[p] = 60 - benefic_pts
    return out


def _weekday(jd_civil_midnight: float) -> int:
    """Weekday (Sunday = 0) of the civil day starting at this Julian day (x.5)."""
    return int(math.floor(jd_civil_midnight + 1.5)) % 7


def kala_components(birth: BirthData, chart: Chart, cfg: SchoolConfig,
                    mercury_malefic: bool, opts: ShadbalaOptions = DEFAULT_OPTIONS
                    ) -> dict[str, dict[str, float]]:
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
    if opts.nathonnatha == "lagna":
        noon_point = (chart.lagna.longitude - 90.0) % 360
        day_pts = 60.0 - _arc(chart.grahas["Su"].longitude, noon_point) / 3.0

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
    ahargana = int(math.floor(sunrise_local_day + 0.5 - KALI_EPOCH_JD)) + opts.ahargana_offset_days
    year_start = sunrise_local_day - (ahargana % 360)
    month_start = sunrise_local_day - (ahargana % 30)
    abda_lord = WEEKDAY_LORD[_weekday(year_start)]
    masa_lord = WEEKDAY_LORD[_weekday(month_start)]

    sun = chart.grahas["Su"].longitude
    moon = chart.grahas["Mo"].longitude
    paksha = paksha_values(sun, moon, mercury_malefic, opts.moon_benefic)

    out: dict[str, dict[str, float]] = {}
    for p in PLANETS7:
        if p == "Me":
            nath = 60.0
        elif p in ("Su", "Ju", "Ve"):
            nath = day_pts
        else:
            nath = 60.0 - day_pts
        if opts.ayana_declination == "kranti":
            add = chart.ayanamsa if opts.ayana_fixed_ayanamsa is None else opts.ayana_fixed_ayanamsa
            dec = kranti((chart.grahas[p].longitude + add) % 360)
        else:
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


def cheshta_bala(p: str, jd: float, true_tropical: float, kala: dict[str, dict[str, float]],
                 moon_elongation_arc: float | None = None) -> float:
    if p == "Su":
        return kala["Su"]["ayana"] / 2.0     # Sun's own Ayana bala (undoubled)
    if p == "Mo":
        if moon_elongation_arc is not None:  # JHora: Moon's distance from the Sun / 3
            return moon_elongation_arc / 3.0
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

# Aspect strength at 0, 30, ..., 330 degrees ahead of the aspecting planet.
_DRISHTI_POINTS = [0, 0, 15, 45, 30, 0, 60, 45, 30, 15, 0, 0]
_SPECIAL_POINTS = {"Ma": (3, 7), "Ju": (4, 8), "Sa": (2, 9)}   # indices of 90/210, 120/240, 60/270


def drishti_value_jhora(aspecting: str, d: float) -> float:
    """Aspect strength by linear interpolation between 30-degree points, a special
    aspect's points set to 60 (Jagannatha Hora)."""
    pts = list(_DRISHTI_POINTS)
    for i in _SPECIAL_POINTS.get(aspecting, ()):
        pts[i] = 60
    d %= 360
    i = int(d // 30)
    f = (d - 30 * i) / 30.0
    return pts[i] + (pts[(i + 1) % 12] - pts[i]) * f


def drishti_value(aspecting: str, d: float) -> float:
    """Aspect strength (virupas) of `aspecting` on a point d degrees ahead of it,
    base curve plus BPHS's flat special-aspect additions."""
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


def drik_bala(lons: dict[str, float], benefic: dict[str, bool],
              method: str = "jhora") -> dict[str, float]:
    value = drishti_value_jhora if method == "jhora" else drishti_value
    out = {}
    for target in PLANETS7:
        s = 0.0
        for src in PLANETS7:
            if src == target:
                continue
            v = value(src, lons[target] - lons[src])
            s += v if benefic[src] else -v
        out[target] = s / 4.0
    return out


def equal_bhava(lon: float, lagna: float) -> int:
    """Equal-house bhava (0..11) with the Lagna at the middle of the 1st."""
    return int(((lon - lagna + 15.0) % 360.0) // 30.0)


# JHora's Mercury rule: natural score of each counted planet (Moon set per chart)
# and the special aspects, in degrees from the planet forward to Mercury.
_MERCURY_SCORE = {"Su": -1, "Ma": -1, "Ju": 1, "Ve": 1, "Sa": -1}
_SPECIAL_ASPECTS = {"Ma": (90.0, 210.0), "Ju": (120.0, 240.0), "Sa": (60.0, 270.0)}


def _mercury_aspect_score(lons: dict[str, float], moon_good: bool) -> tuple[float, bool]:
    """(total, any planet counted) for JHora's aspect rule on Mercury."""
    total, touched = 0.0, False
    for p in ("Su", "Mo", "Ma", "Ju", "Ve", "Sa"):
        score = (1 if moon_good else -1) if p == "Mo" else _MERCURY_SCORE[p]
        d = (lons["Me"] - lons[p]) % 360
        if d <= 15.0 or d >= 345.0:
            total, touched = total + score, True
        if 165.0 <= d <= 195.0:
            total, touched = total + score, True
        for a in _SPECIAL_ASPECTS.get(p, ()):
            if a - 15.0 <= d <= a + 15.0:
                total, touched = total + 0.75 * score, True
    return total, touched


def mercury_is_malefic(signs: dict[str, int], moon_good: bool,
                       opts: ShadbalaOptions = DEFAULT_OPTIONS,
                       bhavas: dict[str, int] | None = None,
                       lons: dict[str, float] | None = None) -> bool:
    """Mercury's nature (see ShadbalaOptions.mercury_rule)."""
    rule = opts.mercury_rule
    if rule == "jhora":
        if lons is None:
            raise ValueError("mercury_rule 'jhora' needs longitudes")
        total, touched = _mercury_aspect_score(lons, moon_good)
        return total < 0 or (total == 0 and touched)
    grahas = ("Su", "Mo", "Ma", "Ju", "Ve", "Sa", "Ra", "Ke")
    where = bhavas if (rule == "bhava" and bhavas is not None) else signs
    mates = [p for p in grahas if p in where and where[p] == where["Me"]]
    good = sum(1 for p in mates if p in ("Ju", "Ve") or (p == "Mo" and moon_good))
    if rule in ("majority", "bhava"):
        return len(mates) - good > good
    if rule == "any":
        return any(p in opts.mercury_malefic_with and not (p == "Mo" and moon_good) for p in mates)
    raise ValueError(f"Unknown mercury_rule {rule!r}")


# BPHS kranti (declination) in arc-minutes at 0, 15, ..., 90 deg from the equinox.
_KRANTI = [0, 362, 703, 1002, 1238, 1388, 1440]


def kranti(tropical_lon: float) -> float:
    """Declination in degrees from the BPHS kranti table (linear between 15-degree steps)."""
    t = tropical_lon % 360
    south = t > 180
    if south:
        t -= 180
    bhuja = t if t <= 90 else 180 - t
    i = min(int(bhuja // 15), 5)
    f = (bhuja - 15 * i) / 15
    v = (_KRANTI[i] + (_KRANTI[i + 1] - _KRANTI[i]) * f) / 60.0
    return -v if south else v


# --------------------------------------------------------------------- total

def shadbala(chart: Chart, birth: BirthData, cfg: SchoolConfig = DEFAULT_CONFIG,
             opts: ShadbalaOptions = DEFAULT_OPTIONS) -> dict[str, PlanetStrength]:
    lons = {p: chart.grahas[p].longitude for p in PLANETS7}
    d1 = {p: chart.grahas[p].sign for p in chart.grahas}
    moon_good = moon_is_benefic(lons["Su"], lons["Mo"], opts.moon_benefic)
    bhavas = {p: equal_bhava(chart.grahas[p].longitude, chart.lagna.longitude) for p in chart.grahas}
    mercury_malefic = mercury_is_malefic(d1, moon_good, opts, bhavas,
                                         {p: g.longitude for p, g in chart.grahas.items()})
    benefic = {"Su": False, "Mo": moon_good, "Ma": False, "Me": not mercury_malefic,
               "Ju": True, "Ve": True, "Sa": False}
    varga_signs = None
    if opts.saptavarga_relation == "varga":
        varga_signs = {n: {k: varga_sign(chart.grahas[k].longitude, n, cfg.hora_scheme) for k in chart.grahas}
                       for n in SAPTAVARGA}

    asc = chart.lagna.longitude
    mc = midheaven(chart.jd_ut, birth.latitude, birth.longitude, cfg)
    kala = kala_components(birth, chart, cfg, mercury_malefic, opts)
    moon_arc = _arc(lons["Mo"], lons["Su"]) if opts.moon_cheshta == "elongation" else None
    drik = drik_bala(lons, benefic, opts.drishti)
    ayan = chart.ayanamsa

    out: dict[str, PlanetStrength] = {}
    for p in PLANETS7:
        lon = lons[p]
        ps = PlanetStrength()
        ps.sthana = {
            "uchcha": uchcha_bala(p, lon),
            "saptavargaja": saptavargaja_bala(p, lon, d1, varga_signs, cfg.hora_scheme),
            "ojayugma": ojayugma_bala(p, lon),
            "kendra": kendra_bala(chart.grahas[p].house),
            "drekkana": drekkana_bala(p, lon),
        }
        ps.dig = dig_bala(p, lon, asc, (asc - 90.0) % 360 if opts.dig_tenth == "lagna" else mc)
        ps.kala = dict(kala[p])
        if p == "Su" and opts.sun_cheshta == "jhora":
            fixed = 23.0 if opts.ayana_fixed_ayanamsa is None else opts.ayana_fixed_ayanamsa
            ps.cheshta = _arc(lon, 270.0 - fixed) / 3.0
        else:
            ps.cheshta = cheshta_bala(p, chart.jd_ut, (lon + ayan) % 360, kala, moon_arc)
        if p in ("Su", "Mo"):
            ps.cheshta_counted = opts.luminary_cheshta_in_total
        ps.naisargika = NAISARGIKA[p]
        ps.drik = drik[p]
        out[p] = ps
    yuddha_bala(out, lons, opts.yuddha_orb)
    return out

# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Rahul Sathe
"""Panchanga as Jagannatha Hora 8.0 shows it (Basics > Key info, and Miscellany >
Panchanga > "Copy monthly panchanga"); see docs/DECISIONS.md, "Panchanga (M2.8)".

A panchanga day runs from sunrise to the next sunrise (JHora's convention; the sunrise
setting is SchoolConfig.sunrise). Tithi = (Moon - Sun) / 12 deg, nakshatra = Moon /
13 deg 20', yoga = (Moon + Sun) / 13 deg 20' with sidereal longitudes, karana = half
tithi. For each element, the day lists those that end before the next sunrise (and the
one running at sunrise when none ends), each with its end time.

Rahu kala, Gulika kala and Yamaganda: the 8 equal parts of the daytime (sunrise to
sunset), in the part given by the weekday (Phaladeepika, Muhurta Chintamani).
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

from .config import DEFAULT_CONFIG, SchoolConfig
from .constants import NAKSHATRAS, VIMSHOTTARI_LORDS
from .ephemeris import ascendant, body_longitude, previous_sunrise, sun_event_after

TITHI_NAMES = [f"{p} {n}" for p in ("Shukla", "Krishna") for n in (
    "Pratipada", "Dwitiya", "Tritiya", "Chaturthi", "Panchami", "Shashthi", "Saptami",
    "Ashtami", "Navami", "Dashami", "Ekadashi", "Dwadashi", "Trayodashi", "Chaturdashi")]
TITHI_NAMES.insert(14, "Purnima")
TITHI_NAMES.append("Amavasya")
YOGAS = ["Vishkambha", "Priti", "Ayushman", "Saubhagya", "Shobhana", "Atiganda",
         "Sukarman", "Dhriti", "Shoola", "Ganda", "Vriddhi", "Dhruva", "Vyaghata",
         "Harshana", "Vajra", "Siddhi", "Vyatipata", "Variyan", "Parigha", "Shiva",
         "Siddha", "Sadhya", "Shubha", "Shukla", "Brahma", "Indra", "Vaidhriti"]
MOVABLE_KARANAS = ["Bava", "Balava", "Kaulava", "Taitila", "Garaja", "Vanija", "Vishti"]
WEEKDAYS = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
WEEKDAY_LORDS = ["Su", "Mo", "Ma", "Me", "Ju", "Ve", "Sa"]
CHALDEAN = ["Sa", "Ju", "Ma", "Su", "Ve", "Me", "Mo"]        # hora order
MASAS = ["Chaitra", "Vaishakha", "Jyeshtha", "Ashadha", "Shravana", "Bhadrapada",
         "Ashvina", "Kartika", "Margashirsha", "Pausha", "Magha", "Phalguna"]
# The 60 years of the Jupiter cycle (spelling as JHora 8.0 shows them).
SAMVATSARAS = [
    "Prabhava", "Vibhava", "Sukla", "Pramoda", "Prajapati", "Angirasa", "Sreemukha",
    "Bhava", "Yuva", "Dhaata", "Isvara", "Bahu-dhanya", "Pramathi", "Vikrama", "Vrisha",
    "Chitrabhanu", "Subhanu", "Tarana", "Parthiva", "Vyaya", "Sarva-jit", "Sarva-dhari",
    "Virodhi", "Vikriti", "Khara", "Nandana", "Vijaya", "Jaya", "Manmatha", "Durmukha",
    "Hemalamba", "Vilamba", "Vikari", "Sharvari", "Plava", "Shubha-krit", "Shobhana",
    "Krodhi", "Viswa-vasu", "Parabhava", "Plavanga", "Keelaka", "Saumya", "Sadharana",
    "Virodha-krit", "Paridhavi", "Pramadi", "Ananda", "Rakshasa", "Nala", "Pingala",
    "Kaala-yukta", "Siddarthi", "Raudra", "Durmati", "Dundubhi", "Rudhirodgaari",
    "Raktaaksha", "Krodhana", "Kshaya"]

# Part (1..8) of the daytime by weekday, Sunday first.
RAHU_KALA = (8, 2, 7, 5, 6, 4, 3)
GULIKA_KALA = (7, 6, 5, 4, 3, 2, 1)
YAMAGANDA = (5, 4, 3, 2, 1, 7, 6)

# Durmuhurta: muhurtas (1..15 of the daytime) by weekday, Sunday first (JHora 8.0).
DURMUHURTA = ((14,), (8, 12), (4, 11), (8,), (12, 13), (4, 9), (1, 2))
# Varjya (tyajya): starts at this ghati of each nakshatra (of 60) and lasts 4 ghatis
# (JHora 8.0's table, fitted exactly from its panchanga; some books give Bharani 24,
# Uttara Phalguni 18).
VARJYA_GHATI = (50, 4, 30, 40, 14, 21, 30, 20, 32, 30, 20, 1, 21, 20, 14, 14, 10, 14,
                20, 20, 20, 10, 10, 18, 16, 30, 30)

NAK = 360.0 / 27.0
_LORDS8 = ("Su", "Mo", "Ma", "Me", "Ju", "Ve", "Sa", "Ra")


def tithi_lord(index: int) -> str:
    """JHora: Su, Mo, Ma, Me, Ju, Ve, Sa, Ra from Pratipada in each paksha."""
    return _LORDS8[(index % 15) % 8]


def yoga_lord(index: int) -> str:
    """JHora: the Vimshottari order from Saturn for Vishkambha."""
    return VIMSHOTTARI_LORDS[(index + 7) % 9]


def karana_name(index: int) -> str:
    """Karana 0..59 of the lunar month (0 = first half of Shukla Pratipada)."""
    if index == 0:
        return "Kimstughna"
    if index >= 57:
        return ("Shakuni", "Chatushpada", "Naga")[index - 57]
    return MOVABLE_KARANAS[(index - 1) % 7]


_SIGN_LORDS = ("Ma", "Ve", "Me", "Mo", "Su", "Me", "Ve", "Ma", "Ju", "Sa", "Sa", "Ju")
_FIXED_KENDRA = {57: 0, 58: 3, 59: 6, 0: 9}       # Shakuni, Chatushpada, Naga, Kimstughna


def karana_lord(index: int, lagna_sign: int | None = None) -> str | None:
    """JHora 8.0 (read from jhora.exe): the movable karanas Bava..Vishti are ruled by
    Su..Sa; the fixed ones by the lord of a kendra from the Lagna: Shakuni the 1st,
    Chatushpada the 4th, Naga the 7th, Kimstughna the 10th (None without a Lagna)."""
    if index in _FIXED_KENDRA:
        if lagna_sign is None:
            return None
        return _SIGN_LORDS[(lagna_sign + _FIXED_KENDRA[index]) % 12]
    return WEEKDAY_LORDS[(index - 1) % 7]


def _moon(jd: float, cfg: SchoolConfig) -> float:
    return body_longitude(jd, "Mo", cfg)


def _elongation(jd: float, cfg: SchoolConfig) -> float:
    return (body_longitude(jd, "Mo", cfg) - body_longitude(jd, "Su", cfg)) % 360.0


def _sum(jd: float, cfg: SchoolConfig) -> float:
    return (body_longitude(jd, "Mo", cfg) + body_longitude(jd, "Su", cfg)) % 360.0


_FUNCS = {"tithi": (_elongation, 12.0, 12.19), "nakshatra": (_moon, NAK, 13.18),
          "yoga": (_sum, NAK, 14.17), "karana": (_elongation, 6.0, 12.19)}


def _crossing(f, target: float, jd: float, rate: float, cfg: SchoolConfig) -> float:
    """First moment after jd (within about a day and a half) when f reaches target."""
    t = jd + ((target - f(jd, cfg)) % 360.0) / rate
    for _ in range(30):
        d = ((target - f(t, cfg) + 180.0) % 360.0) - 180.0
        if abs(d) < 1e-7:
            break
        t += d / rate
    return t


@dataclass
class Element:
    kind: str
    index: int
    name: str
    lord: str | None
    end_jd: float
    fraction_left: float | None = None


def _make(kind: str, index: int, end: float) -> Element:
    if kind == "tithi":
        return Element(kind, index, TITHI_NAMES[index], tithi_lord(index), end)
    if kind == "nakshatra":
        return Element(kind, index, NAKSHATRAS[index], VIMSHOTTARI_LORDS[index % 9], end)
    if kind == "yoga":
        return Element(kind, index, YOGAS[index], yoga_lord(index), end)
    return Element(kind, index, karana_name(index), karana_lord(index), end)


def element_at(kind: str, jd: float, cfg: SchoolConfig = DEFAULT_CONFIG) -> Element:
    """The tithi, nakshatra, yoga or karana running at jd, with its end and the fraction
    of it still to run (as JHora's "% left")."""
    f, span, rate = _FUNCS[kind]
    x = f(jd, cfg)
    n = int(360.0 / span)
    i = int(x // span) % n
    end = _crossing(f, ((i + 1) * span) % 360.0, jd, rate, cfg)
    e = _make(kind, i, end)
    e.fraction_left = 1.0 - (x - i * span) / span
    return e


def elements_between(kind: str, start: float, stop: float,
                     cfg: SchoolConfig = DEFAULT_CONFIG) -> list[Element]:
    """Elements ending in [start, stop); the one running at start if none ends."""
    f, span, rate = _FUNCS[kind]
    n = int(360.0 / span)
    e = element_at(kind, start, cfg)
    out = []
    while e.end_jd < stop:
        out.append(e)
        i = (e.index + 1) % n
        end = _crossing(f, ((i + 1) * span) % 360.0, e.end_jd + 1e-5, rate, cfg)
        e = _make(kind, i, end)
    return out or [e]


def weekday(sunrise_jd: float, lon: float) -> int:
    """Weekday (Sunday = 0) of the local day of a sunrise."""
    return int(math.floor(sunrise_jd + 0.5 + lon / 360.0 + 1.0)) % 7


def _start_of(kind: str, e: Element, cfg: SchoolConfig) -> float:
    f, span, rate = _FUNCS[kind]
    return _crossing(f, (e.index * span) % 360.0, e.end_jd - 360.0 / (360.0 / span) / rate * 1.25,
                     rate, cfg)


def varjya(start: float, stop: float, cfg: SchoolConfig = DEFAULT_CONFIG) -> list[tuple[float, float]]:
    """Varjya periods overlapping [start, stop), as JHora lists them (it lists one
    that spans a sunrise under both days)."""
    out = []
    e = element_at("nakshatra", start - 1.2, cfg)
    while True:
        s = _start_of("nakshatra", e, cfg)
        if s >= stop:
            break
        length = e.end_jd - s
        a = s + length * VARJYA_GHATI[e.index] / 60.0
        b = a + length * 4.0 / 60.0
        if b > start and a < stop:
            out.append((a, b))
        e = element_at("nakshatra", e.end_jd + 1e-5, cfg)
    return out


def durmuhurta(rise: float, set_: float, wd: int) -> list[tuple[float, float]]:
    w = (set_ - rise) / 15.0
    return [(rise + (k - 1) * w, rise + k * w) for k in DURMUHURTA[wd]]


def _lagna_meets_moon(jd: float, lat: float, lon: float, offset: float,
                      cfg: SchoolConfig) -> float:
    """First moment after jd when the Lagna reaches the Moon's longitude + offset."""
    def f(t: float) -> float:
        return ((ascendant(t, lat, lon, cfg) - body_longitude(t, "Mo", cfg) - offset + 180.0)
                % 360.0) - 180.0
    t, prev, step = jd, f(jd), 1.0 / 96.0
    for _ in range(96 * 3):
        t2 = t + step
        cur = f(t2)
        if prev < 0.0 <= cur and cur - prev < 90.0:
            a, b = t, t2
            for _ in range(36):
                mid = (a + b) / 2.0
                a, b = (mid, b) if f(mid) < 0.0 else (a, mid)
            return (a + b) / 2.0
        t, prev = t2, cur
    raise ValueError("The Moon's longitude does not rise here within three days.")


def moonrise(jd: float, lat: float, lon: float, cfg: SchoolConfig = DEFAULT_CONFIG) -> float:
    """JHora's moonrise: the Lagna reaches the Moon's longitude (the Moon's latitude
    and parallax are ignored), the first time after jd."""
    return _lagna_meets_moon(jd, lat, lon, 0.0, cfg)


def moonset(jd: float, lat: float, lon: float, cfg: SchoolConfig = DEFAULT_CONFIG) -> float:
    """JHora's moonset: the Lagna reaches the Moon's longitude + 180 deg."""
    return _lagna_meets_moon(jd, lat, lon, 180.0, cfg)


@dataclass
class Day:
    sunrise: float
    sunset: float
    next_sunrise: float
    weekday: int
    tithis: list[Element]
    nakshatras: list[Element]
    yogas: list[Element]
    karanas: list[Element]
    rahu_kala: tuple[float, float]
    gulika_kala: tuple[float, float]
    yamaganda: tuple[float, float]
    durmuhurta: list[tuple[float, float]] = field(default_factory=list)
    varjya: list[tuple[float, float]] = field(default_factory=list)
    moonrise: float | None = None
    moonset: float | None = None
    moon_sign: int = 0
    moon_sign_end: float | None = None           # None: the Moon keeps its sign all day


def _part(rise: float, set_: float, k: int) -> tuple[float, float]:
    w = (set_ - rise) / 8.0
    return rise + (k - 1) * w, rise + k * w


def day_panchanga(jd_ut: float, lat: float, lon: float, alt: float = 0.0,
                  cfg: SchoolConfig = DEFAULT_CONFIG) -> Day:
    """The panchanga day (sunrise to next sunrise) containing jd_ut."""
    rise = previous_sunrise(jd_ut, lat, lon, alt, cfg)
    set_ = sun_event_after(rise, lat, lon, alt, cfg, "set")
    nxt = sun_event_after(rise + 0.01, lat, lon, alt, cfg, "rise")
    wd = weekday(rise, lon)
    els = {k: elements_between(k, rise, nxt, cfg) for k in ("tithi", "nakshatra", "yoga", "karana")}
    moon = body_longitude(rise, "Mo", cfg)
    sign = int(moon // 30)
    sign_end = _crossing(_moon, ((sign + 1) * 30.0) % 360.0, rise, 13.18, cfg)
    return Day(rise, set_, nxt, wd, els["tithi"], els["nakshatra"], els["yoga"], els["karana"],
               _part(rise, set_, RAHU_KALA[wd]), _part(rise, set_, GULIKA_KALA[wd]),
               _part(rise, set_, YAMAGANDA[wd]), durmuhurta(rise, set_, wd),
               varjya(rise, nxt, cfg), moonrise(rise, lat, lon, cfg), moonset(rise, lat, lon, cfg),
               sign, sign_end if sign_end < nxt else None)


def hora_lord(jd_ut: float, sunrise: float, wd: int) -> str:
    """JHora's default hora: hours of 60 minutes from sunrise, the first ruled by the
    weekday lord, then in Chaldean order."""
    k = int((jd_ut - sunrise) * 24.0)
    return CHALDEAN[(CHALDEAN.index(WEEKDAY_LORDS[wd]) + k) % 7]


def lunar_month(jd_ut: float, cfg: SchoolConfig = DEFAULT_CONFIG) -> tuple[int, str]:
    """(masa index 0 = Chaitra, prefix): amanta month named after the sign the Sun is in
    at the new moon that begins it (Sun in Pisces: Chaitra). A month without a solar
    ingress is adhika ("Adhika"), and the regular month after it "Nija"."""
    start = _crossing(_elongation, 0.0, jd_ut - _elongation(jd_ut, cfg) / 12.19 - 1.5, 12.19, cfg)
    if start > jd_ut:
        start = _crossing(_elongation, 0.0, start - 31.0, 12.19, cfg)
    end = _crossing(_elongation, 0.0, start + 25.0, 12.19, cfg)
    s0 = int(body_longitude(start, "Su", cfg) // 30)
    s1 = int(body_longitude(end, "Su", cfg) // 30)
    masa = (s0 + 1) % 12
    if s0 == s1:
        return masa, "Adhika"
    prev = _crossing(_elongation, 0.0, start - 31.0, 12.19, cfg)
    if int(body_longitude(prev, "Su", cfg) // 30) == s0:
        return masa, "Nija"
    return masa, ""


def samvatsara(jd_ut: float, cfg: SchoolConfig = DEFAULT_CONFIG) -> int:
    """Index (0 = Prabhava) of the lunar year running at jd_ut; the year begins with
    Chaitra (Prabhava = the year from Chaitra 1987)."""
    from .timeutil import jd_to_datetime
    masa, _ = lunar_month(jd_ut, cfg)
    start_of_year = jd_ut - masa * 29.53 - 10.0
    return (jd_to_datetime(start_of_year).year - 1987) % 60


def _with_lagna(e: Element, lagna_sign: int | None) -> Element:
    e.lord = karana_lord(e.index, lagna_sign)
    return e


@dataclass
class BirthPanchanga:
    samvatsara: str
    masa: str
    tithi: Element
    weekday: int
    nakshatra: Element
    yoga: Element
    karana: Element
    hora_lord: str
    sunrise: float
    sunset: float
    janma_ghatis: float


def birth_panchanga(jd_ut: float, lat: float, lon: float, alt: float = 0.0,
                    cfg: SchoolConfig = DEFAULT_CONFIG,
                    lagna_sign: int | None = None) -> BirthPanchanga:
    """JHora's Key info panchanga for a moment (the Lagna sign names the lord of a
    fixed karana)."""
    rise = previous_sunrise(jd_ut, lat, lon, alt, cfg)
    set_ = sun_event_after(rise, lat, lon, alt, cfg, "set")
    wd = weekday(rise, lon)
    masa, prefix = lunar_month(jd_ut, cfg)
    return BirthPanchanga(
        SAMVATSARAS[samvatsara(jd_ut, cfg)], f"{prefix} {MASAS[masa]}".strip(),
        element_at("tithi", jd_ut, cfg), wd, element_at("nakshatra", jd_ut, cfg),
        element_at("yoga", jd_ut, cfg), _with_lagna(element_at("karana", jd_ut, cfg), lagna_sign),
        hora_lord(jd_ut, rise, wd), rise, set_, (jd_ut - rise) * 60.0)

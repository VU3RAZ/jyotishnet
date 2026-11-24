# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Rahul Sathe
"""Upagrahas and other sensitive points of a chart, as Jagannatha Hora 8.0
computes them (matched on the 55 golden charts):

- Sun-based (BPHS ch. 3): Dhooma = Sun + 133 deg 20'; Vyatipata = 360 - Dhooma;
  Parivesha = Vyatipata + 180; Indra Chapa = 360 - Parivesha; Upaketu =
  Indra Chapa + 16 deg 40' (= Sun - 30).
- Time-based: the day (sunrise to sunset) or night is cut into eight equal parts.
  Their lords run Sun, Moon, Mars, Mercury, Jupiter, Venus, Saturn and a lordless
  part, in a cycle that starts by day from the weekday lord and by night from the
  fifth weekday lord. Each upagraha is the ascendant at the middle of its lord's
  part: Kaala (Sun), Mrityu (Mars), Artha Prahara (Mercury), Yama Ghantaka
  (Jupiter), Maandi (Saturn); Gulika is the ascendant at the start of Saturn's part.
- Sree Lagna: Lagna + 360 deg x the Moon's progress through its nakshatra.
- Indu Lagna: the kalas (Sun 30, Moon 16, Mars 6, Mercury 8, Jupiter 10, Venus 12,
  Saturn 1) of the 9th lords from the Lagna and from the Moon, added; the remainder
  by 12 counted from the Moon's sign (0 = 12th); at the Moon's degree.
- Varnada Lagna: count the Lagna from Aries if odd, from Pisces backwards if even,
  and the Hora Lagna the same way; add the counts if both are odd or both even,
  otherwise take the difference; count the result from Aries if the Lagna is odd,
  backwards from Pisces if it is even; at the Lagna's degree.
- Bhrigu Bindu: midway from Rahu to the Moon (zodiacal arc).
- Yogi point: Sun + Moon + 93 deg 20'; Yogi = the lord of its nakshatra, Sahayogi
  = the lord of its sign; Avayogi = the lord of the nakshatra 186 deg 40' further.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from .config import SchoolConfig
from .constants import NAKSHATRA_SPAN, SIGN_LORD
from .ephemeris import ascendant, previous_sunrise, sun_event_after
from .nakshatra import nakshatra_of

_CYCLE = ("Su", "Mo", "Ma", "Me", "Ju", "Ve", "Sa", None)
_WEEKDAY = ("Su", "Mo", "Ma", "Me", "Ju", "Ve", "Sa")
KALAS = {"Su": 30, "Mo": 16, "Ma": 6, "Me": 8, "Ju": 10, "Ve": 12, "Sa": 1}
TIME_UPAGRAHAS = {"Kl": ("Su", 0.5), "Mr": ("Ma", 0.5), "AP": ("Me", 0.5),
                  "YG": ("Ju", 0.5), "Gk": ("Sa", 0.0), "Md": ("Sa", 0.5)}
NAMES = {"Dh": "Dhooma", "Vy": "Vyatipata", "Pv": "Parivesha", "IC": "Indra Chapa",
         "UK": "Upaketu", "Kl": "Kaala", "Mr": "Mrityu", "AP": "Artha Prahara",
         "YG": "Yama Ghantaka", "Gk": "Gulika", "Md": "Maandi", "SL": "Sree Lagna",
         "IL": "Indu Lagna", "VL": "Varnada Lagna", "BB": "Bhrigu Bindu"}


@dataclass(frozen=True)
class Yogi:
    point: float
    yogi: str
    sahayogi: str
    avayogi_point: float
    avayogi: str


def sun_upagrahas(sun: float) -> dict[str, float]:
    dh = (sun + 133.0 + 1.0 / 3.0) % 360.0
    vy = (360.0 - dh) % 360.0
    pv = (vy + 180.0) % 360.0
    ic = (360.0 - pv) % 360.0
    uk = (ic + 16.0 + 2.0 / 3.0) % 360.0
    return {"Dh": dh, "Vy": vy, "Pv": pv, "IC": ic, "UK": uk}


def upagraha_times(jd_ut: float, lat: float, lon: float, alt: float,
                   cfg: SchoolConfig) -> dict[str, float]:
    """Julian day (UT) of each time-based upagraha's moment."""
    rise = previous_sunrise(jd_ut, lat, lon, alt, cfg)
    sunset = sun_event_after(rise, lat, lon, alt, cfg, "set")
    weekday = int(math.floor(rise + 0.5 + lon / 360.0 + 1.0)) % 7   # Sunday = 0
    if jd_ut < sunset:
        start, end, first = rise, sunset, weekday
    else:
        start, end = sunset, sun_event_after(rise + 0.01, lat, lon, alt, cfg, "rise")
        first = (weekday + 4) % 7
    part = (end - start) / 8.0
    out = {}
    for code, (lord, frac) in TIME_UPAGRAHAS.items():
        k = (_CYCLE.index(lord) - _CYCLE.index(_WEEKDAY[first])) % 8
        out[code] = start + part * (k + frac)
    return out


def time_upagrahas(jd_ut: float, lat: float, lon: float, alt: float,
                   cfg: SchoolConfig) -> dict[str, float]:
    """Kaala, Mrityu, Artha Prahara, Yama Ghantaka, Gulika, Maandi: the ascendant
    at each one's moment."""
    return {k: ascendant(t, lat, lon, cfg)
            for k, t in upagraha_times(jd_ut, lat, lon, alt, cfg).items()}


def sree_lagna(lagna: float, moon: float) -> float:
    frac = (moon % NAKSHATRA_SPAN) / NAKSHATRA_SPAN
    return (lagna + 360.0 * frac) % 360.0


def indu_lagna(lagna: float, moon: float) -> float:
    ls, ms = int(lagna // 30), int(moon // 30)
    total = KALAS[SIGN_LORD[(ls + 8) % 12]] + KALAS[SIGN_LORD[(ms + 8) % 12]]
    r = total % 12 or 12
    return ((ms + r - 1) % 12) * 30.0 + moon % 30.0


def _count(sign: int) -> int:
    """Aries = 1 forwards for odd signs, Pisces = 1 backwards for even signs."""
    return sign + 1 if sign % 2 == 0 else 12 - sign


def varnada_lagna(lagna: float, hora_lagna: float) -> float:
    a, b = int(lagna // 30), int(hora_lagna // 30)
    ca, cb = _count(a), _count(b)
    n = ca + cb if (a % 2) == (b % 2) else abs(ca - cb)
    n = n % 12 or 12
    sign = (n - 1) if a % 2 == 0 else (12 - n) % 12
    return sign * 30.0 + lagna % 30.0


def bhrigu_bindu(moon: float, rahu: float) -> float:
    return (rahu + ((moon - rahu) % 360.0) / 2.0) % 360.0


def yogi(sun: float, moon: float) -> Yogi:
    point = (sun + moon + 93.0 + 1.0 / 3.0) % 360.0
    ava = (point + 186.0 + 2.0 / 3.0) % 360.0
    return Yogi(point, nakshatra_of(point).lord, SIGN_LORD[int(point // 30)], ava,
                nakshatra_of(ava).lord)

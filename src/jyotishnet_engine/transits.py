# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Rahul Sathe
"""Transit (gochara) tools, as Jagannatha Hora 8.0's "Basic Transit Results".

For each transiting graha, with the natal Moon as the reference:
- house from the natal Moon, and whether it is a good house (Phaladeepika ch. 26);
- vedha: a good house is obstructed by a graha transiting its vedha house (as JHora,
  Mercury in the 10th is obstructed from the 7th, where the published table gives the
  8th: an open decision in docs/DECISIONS.md), except
  that the Sun and Saturn, and the Moon and Mercury, never obstruct each other;
  Rahu and Ketu obstruct others but are never obstructed (as JHora);
- tara: the transit nakshatra counted from the natal Moon's, in cycles of nine;
- murthi: by the transit Moon's house from the natal Moon at the moment the graha
  entered its present sign (1, 6, 11 golden; 2, 5, 9 silver; 3, 7, 10 copper;
  4, 8, 12 iron); none for the Moon;
- Ashtakavarga: the graha's natal BAV and the SAV in the transit sign; the kakshya
  (one of eight 3 deg 45' parts of the sign, lords Saturn, Jupiter, Mars, Sun,
  Venus, Mercury, Moon, Lagna) and whether its lord gave a bindu there.

Sade Sati: Saturn in the 12th, 1st or 2nd sign from the natal Moon (rising, peak,
setting); Kantaka/Ashtama Shani: Saturn in the 4th or 8th from the Moon.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .ashtakavarga import Ashtakavarga, ashtakavarga
from .chart import Chart
from .config import SchoolConfig
from .ephemeris import body_longitude
from .nakshatra import nakshatra_of

GRAHAS9 = ("Su", "Mo", "Ma", "Me", "Ju", "Ve", "Sa", "Ra", "Ke")

# Good houses from the natal Moon and the vedha house for each (Phaladeepika 26;
# Mercury 10 -> 7 as JHora; Rahu and Ketu, not in the text, as JHora).
VEDHA: dict[str, dict[int, int]] = {
    "Su": {3: 9, 6: 12, 10: 4, 11: 5},
    "Mo": {1: 5, 3: 9, 6: 12, 7: 2, 10: 4, 11: 8},
    "Ma": {3: 12, 6: 9, 11: 5},
    "Me": {2: 5, 4: 3, 6: 9, 8: 1, 10: 7, 11: 12},
    "Ju": {2: 12, 5: 4, 7: 3, 9: 10, 11: 8},
    "Ve": {1: 8, 2: 7, 3: 1, 4: 10, 5: 9, 8: 5, 9: 11, 11: 6, 12: 3},
    "Sa": {3: 12, 6: 9, 11: 5},
    "Ra": {3: 12, 6: 9, 11: 5},
    "Ke": {3: 12, 6: 9, 11: 5},
}
NO_VEDHA_PAIRS = ({"Su", "Sa"}, {"Mo", "Me"})
NODES = ("Ra", "Ke")   # JHora: the nodes obstruct others but are never obstructed
TARAS = ("Janma", "Sampat", "Vipat", "Kshema", "Pratyak", "Saadhana", "Naidhana", "Mitra",
         "Parama Mitra")
MURTHI = {1: "Swarna", 6: "Swarna", 11: "Swarna", 2: "Rajata", 5: "Rajata", 9: "Rajata",
          3: "Taamra", 7: "Taamra", 10: "Taamra", 4: "Loha", 8: "Loha", 12: "Loha"}
KAKSHYA_LORDS = ("Sa", "Ju", "Ma", "Su", "Ve", "Me", "Mo", "La")
SADE_SATI = {12: "rising", 1: "peak", 2: "setting"}


@dataclass
class TransitPlanet:
    code: str
    longitude: float
    sign: int
    house_from_moon: int
    good: bool
    vedha_from: list[str] = field(default_factory=list)   # grahas obstructing this one
    vedha_to: list[str] = field(default_factory=list)     # grahas this one obstructs
    tara: str = ""
    tara_number: int = 0                                  # 1..9
    murthi: str | None = None
    av_score: int | None = None                           # own BAV bindus in the sign
    sav_score: int | None = None
    kakshya: str | None = None                            # lord of the kakshya
    kakshya_good: bool | None = None
    bindu_from: list[str] = field(default_factory=list)   # contributors of the bindus


def house_from(sign: int, ref_sign: int) -> int:
    return (sign - ref_sign) % 12 + 1


def tara(natal_moon: float, lon: float) -> tuple[int, str]:
    n = (nakshatra_of(lon).index - nakshatra_of(natal_moon).index) % 27
    k = n % 9 + 1
    return k, TARAS[k - 1]


def kakshya(lon: float) -> str:
    return KAKSHYA_LORDS[min(int((lon % 30.0) / 3.75), 7)]


def sign_entry(code: str, jd_ut: float, cfg: SchoolConfig) -> float:
    """Julian day (UT) at which the graha entered the sign it occupies at jd_ut."""
    sign = int(body_longitude(jd_ut, code, cfg) // 30)
    step = 0.25 if code == "Mo" else 1.0
    t = jd_ut
    while int(body_longitude(t - step, code, cfg) // 30) == sign:
        t -= step
    lo, hi = t - step, t          # lo outside the sign, hi inside
    while hi - lo > 1e-5:
        mid = (lo + hi) / 2
        if int(body_longitude(mid, code, cfg) // 30) == sign:
            hi = mid
        else:
            lo = mid
    return hi


def murthi(code: str, jd_ut: float, natal_moon_sign: int, cfg: SchoolConfig) -> str | None:
    if code == "Mo":
        return None
    entry = sign_entry(code, jd_ut, cfg)
    moon_sign = int(body_longitude(entry, "Mo", cfg) // 30)
    return MURTHI[house_from(moon_sign, natal_moon_sign)]


def gochara(natal: Chart, transit: Chart, cfg: SchoolConfig,
            av: Ashtakavarga | None = None) -> dict[str, TransitPlanet]:
    """Transit results of the nine grahas of `transit` against the natal chart."""
    av = av or ashtakavarga(natal)
    moon = natal.grahas["Mo"]
    out: dict[str, TransitPlanet] = {}
    for p in GRAHAS9:
        g = transit.grahas[p]
        h = house_from(g.sign, moon.sign)
        k, name = tara(moon.longitude, g.longitude)
        tp = TransitPlanet(p, g.longitude, g.sign, h, h in VEDHA[p], tara=name, tara_number=k,
                           murthi=murthi(p, transit.jd_ut, moon.sign, cfg))
        if p in av.bav:
            tp.av_score = av.bav[p][g.sign]
            tp.sav_score = av.sav[g.sign]
            tp.kakshya = kakshya(g.longitude)
            tp.bindu_from = [c for c, row in av.prastara[p].items() if row[g.sign]]
            tp.kakshya_good = tp.kakshya in tp.bindu_from
        out[p] = tp
    houses = {p: tp.house_from_moon for p, tp in out.items()}
    for p, tp in out.items():
        if not tp.good or p in NODES:
            continue
        vh = VEDHA[p][tp.house_from_moon]
        for q, hq in houses.items():
            if q != p and hq == vh and {p, q} not in NO_VEDHA_PAIRS:
                tp.vedha_from.append(q)
                out[q].vedha_to.append(p)
    return out


def sade_sati_phase(saturn_sign: int, natal_moon_sign: int) -> str | None:
    """"rising", "peak", "setting" (Sade Sati), "kantaka" (4th), "ashtama" (8th) or None."""
    h = house_from(saturn_sign, natal_moon_sign)
    return SADE_SATI.get(h) or {4: "kantaka", 8: "ashtama"}.get(h)


@dataclass(frozen=True)
class SaturnSpell:
    phase: str          # rising, peak, setting, kantaka, ashtama
    start_jd: float
    end_jd: float


def saturn_spells(natal_moon_sign: int, start_jd: float, end_jd: float,
                  cfg: SchoolConfig) -> list[SaturnSpell]:
    """Saturn's stays in the 12th, 1st, 2nd, 4th and 8th signs from the natal Moon
    between two dates, each sign entry found to about a second (retrograde
    re-entries give separate spells)."""
    spells: list[SaturnSpell] = []
    step = 2.0
    t = start_jd
    cur = int(body_longitude(t, "Sa", cfg) // 30)
    begin = t
    while t < end_jd:
        nt = min(t + step, end_jd)
        s = int(body_longitude(nt, "Sa", cfg) // 30)
        if s != cur:
            lo, hi = t, nt
            while hi - lo > 1e-5:
                mid = (lo + hi) / 2
                if int(body_longitude(mid, "Sa", cfg) // 30) == cur:
                    lo = mid
                else:
                    hi = mid
            phase = sade_sati_phase(cur, natal_moon_sign)
            if phase:
                spells.append(SaturnSpell(phase, begin, hi))
            cur, begin = s, hi
        t = nt
    phase = sade_sati_phase(cur, natal_moon_sign)
    if phase:
        spells.append(SaturnSpell(phase, begin, end_jd))
    return spells

# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Rahul Sathe
"""Jaimini sign strength, arudhas and the rasi dashas as Jagannatha Hora 8.0
computes them with its default settings (read from jhora.exe: the routine that fills
its "stronger of X and Y" tables, its co-lord routines for Scorpio and Aquarius, the
arudha routine and each rasi dasa routine; see docs/DECISIONS.md, "Jaimini (M2.7)").
Each dasha function's docstring states its rules; RASI_DASHAS lists them.

Positions are signs 0..11 of Su..Ke (and longitudes for the tie-breaks).

Stronger of two signs (in order; the first sign wins a full tie):
  1. more grahas (Sun to Ketu) in the sign;
  2. more of Mercury, Jupiter and the sign's lord (for Scorpio Mars, else Ketu; for
     Aquarius Saturn, else Rahu) in the sign or aspecting it by rasi drishti;
  3. more grahas exalted in the sign;
  4. fewer grahas debilitated in the sign;
  5. the sign whose (stronger) lord sits in a sign of the other oddity;
  6. dual over fixed over movable;
  7. the lord further advanced in its sign (Rahu and Ketu counted backwards).
Stronger co-lord (Saturn/Rahu of Aquarius, Mars/Ketu of Scorpio; the first wins a tie):
  0. if one of them occupies the sign, the other;
  1. more grahas in its sign; 2. as rule 2 above for its sign; 3. exalted;
  4. not debilitated; 5. dual over fixed over movable sign; 6. the longer dasha count
     from the co-lords' sign to it.
Bhava arudhas (JHora defaults: Parashara's exceptions on, Rahu/Ketu as lords of
Aquarius/Scorpio when stronger, by the co-lord rules above with the more advanced
co-lord winning the last tie).
Saturn/Ketu exception of a sign: Saturn in it (and not a stronger Ketu with it) -> 1,
Ketu in it -> 2 (stronger of the two: exalted, not debilitated, moolatrikona, own
sign, more advanced).

Narayana dasha (rasi chart): starts from the stronger of the Lagna and the 7th;
movable signs progress regularly, fixed signs by every sixth sign, dual signs by
trines (1, 5, 9, 10, 2, 6, 7, 11, 3, 4, 8, 12); forward from Ar, Le, Vi, Li, Aq, Pi,
backward from the others; Saturn in the first sign makes the progression regular and
forward, Ketu reverses it. Years: count from the sign to its lord, forward from Ar,
Ta, Ge, Li, Sc, Sg and backward from the others, less one (12 when the lord is in
the sign), plus one if the lord is exalted (to at most 12), minus one if debilitated;
the second cycle gives each sign 12 minus its first-cycle years (a sign with 12
first-cycle years gets a zero-length second period). Antardashas: 12 equal parts
from the sign holding the lord of the stronger of the dasa sign and its 7th, forward
if that sign is odd, backward if even, with the same Saturn/Ketu exception of the
stronger sign.
"""

from __future__ import annotations

from .config import DEFAULT_CONFIG, SchoolConfig
from .dasha import Period, YearClock, _assign_jd

GRAHAS9 = ("Su", "Mo", "Ma", "Me", "Ju", "Ve", "Sa", "Ra", "Ke")
LORD = ("Ma", "Ve", "Me", "Mo", "Su", "Me", "Ve", "Ma", "Ju", "Sa", "Sa", "Ju")
EXALT = {"Su": 0, "Mo": 1, "Ma": 9, "Me": 5, "Ju": 3, "Ve": 11, "Sa": 6, "Ra": 2, "Ke": 8}
DEBIL = {p: (s + 6) % 12 for p, s in EXALT.items()}
MOOLA = {"Su": 4, "Mo": 1, "Ma": 0, "Me": 5, "Ju": 8, "Ve": 6, "Sa": 10, "Ra": 5, "Ke": 11}
CO_LORDS = {10: ("Sa", "Ra"), 7: ("Ma", "Ke")}
FORWARD = frozenset({0, 4, 5, 6, 10, 11})          # Narayana MD direction from the seed
PROGRESSION = (
    (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11),         # movable: regular
    (0, 5, 10, 3, 8, 1, 6, 11, 4, 9, 2, 7),         # fixed: every sixth
    (0, 4, 8, 9, 1, 5, 6, 10, 2, 3, 7, 11),         # dual: trines
)


def sees(a: int, b: int) -> bool:
    """Same sign, or rasi drishti between the signs (symmetric)."""
    if a == b:
        return True
    ma, mb = a % 3, b % 3
    if ma == 2:
        return mb == 2
    if (ma == 0 and mb == 1) or (ma == 1 and mb == 0):
        return (a + 1) % 12 != b and (b + 1) % 12 != a
    return False


def _owns(p: str, sign: int) -> bool:
    return LORD[sign] == p or (sign == 10 and p == "Ra") or (sign == 7 and p == "Ke")


def _advance(p: str, lon: dict[str, float]) -> float:
    d = lon[p] % 30.0
    return 30.0 - d if p in ("Ra", "Ke") else d


class JaiminiChart:
    """Sign positions of Su..Ke (and longitudes) with JHora's Jaimini strength rules."""

    def __init__(self, signs: dict[str, int], longitudes: dict[str, float],
                 lagna_lon: float | None = None):
        self.signs = {p: signs[p] for p in GRAHAS9}
        self.lon = {p: longitudes[p] for p in GRAHAS9}
        if lagna_lon is not None:
            # JHora's lord table read at index 12 gives slot 0, the Lagna: Sudasa can
            # compare a "sign 12" (Pisces + 1, not reduced) that has no grahas and
            # the Lagna as its lord.
            self.signs["La"] = int(lagna_lon // 30)
            self.lon["La"] = lagna_lon
        self.lords = {10: self._co_lord("Sa", "Ra"), 7: self._co_lord("Ma", "Ke")}
        self.arudha_lords = {10: self._co_lord("Sa", "Ra", advance_last=True),
                             7: self._co_lord("Ma", "Ke", advance_last=True)}

    # -- counts -----------------------------------------------------------------
    def occupants(self, sign: int) -> int:
        return sum(1 for p in GRAHAS9 if self.signs[p] == sign)

    def helpers(self, sign: int) -> int:
        """Mercury, Jupiter and the lord (or Ketu/Rahu for Sc/Aq) in or aspecting."""
        s = self.signs
        n = int(sees(sign, s["Me"])) + int(sees(sign, s["Ju"]))
        if sees(sign, s[LORD[sign] if sign < 12 else "La"]):
            n += 1
        elif sign == 7 and sees(7, s["Ke"]):
            n += 1
        elif sign == 10 and sees(10, s["Ra"]):
            n += 1
        return n

    def _years_from(self, base: int, p: str) -> int:
        at = self.signs[p]
        count = (at - base) % 12 if (base // 3) % 2 == 0 else (base - at) % 12
        count = count or 12                    # lord in the sign itself: 12
        if EXALT[p] == at and count < 12:
            count += 1
        if DEBIL[p] == at and count > 0:
            count -= 1
        return count

    # -- rules ------------------------------------------------------------------
    def _co_lord(self, a: str, b: str, advance_last: bool = False) -> str:
        own = 10 if a == "Sa" else 7
        sa, sb = self.signs[a], self.signs[b]
        if sa == own and sb != own:
            return b
        if sb == own and sa != own:
            return a
        for key in (self.occupants, self.helpers):
            ka, kb = key(sa), key(sb)
            if ka != kb:
                return a if ka > kb else b
        ea, eb = EXALT[a] == sa, EXALT[b] == sb
        if ea != eb:
            return a if ea else b
        da, db = DEBIL[a] == sa, DEBIL[b] == sb
        if da != db:
            return b if da else a
        if sa % 3 != sb % 3:
            return a if sa % 3 > sb % 3 else b
        if advance_last:                       # arudha table: more advanced wins
            return b if _advance(a, self.lon) < _advance(b, self.lon) else a
        return b if self._years_from(own, a) < self._years_from(own, b) else a

    def bhava_arudhas(self, lagna: int, exceptions: bool = True,
                      nodes_as_lords: bool = True) -> list[int]:
        """Signs of A1 (Arudha Lagna) .. A12 (Upapada). The pada is as far from the
        lord as the lord is from the house; with Parashara's exceptions a pada in the
        house itself or its 7th moves to the 10th from there. With nodes_as_lords the
        stronger of Saturn/Rahu (Aquarius) and Mars/Ketu (Scorpio) is the lord."""
        out = []
        for k in range(12):
            sign = (lagna + k) % 12
            lord = self.arudha_lords.get(sign, LORD[sign]) if nodes_as_lords else LORD[sign]
            pada = (2 * self.signs[lord] - sign) % 12
            if exceptions and (pada - sign) % 6 == 0:
                pada = (pada + 9) % 12
            out.append(pada)
        return out

    def lord(self, sign: int) -> str:
        return self.lords.get(sign, LORD[sign] if sign < 12 else "La")

    def stronger(self, a: int, b: int, dignity_first: bool = False) -> int:
        """Stronger of two signs. dignity_first puts the exaltation and debilitation
        rules before the Mercury/Jupiter/lord rule (JHora's second comparator, used to
        order the kendras in Atma Karaka Kendradi dasha)."""
        s = self.signs
        exalted = lambda x: sum(1 for p in GRAHAS9 if s[p] == x and EXALT[p] == x)
        debil = lambda x: -sum(1 for p in GRAHAS9 if s[p] == x and DEBIL[p] == x)
        middle = (exalted, debil, self.helpers) if dignity_first else (self.helpers, exalted, debil)
        rules = (
            self.occupants, *middle,
            lambda x: int(s[self.lord(x)] % 2 != x % 2),
            lambda x: x % 3,
        )
        for key in rules:
            ka, kb = key(a), key(b)
            if ka != kb:
                return a if ka > kb else b
        return b if _advance(self.lord(a), self.lon) < _advance(self.lord(b), self.lon) else a

    def stronger_of_pair(self, sign: int) -> int:
        """Stronger of a sign and its 7th, compared with the lower-numbered sign first."""
        lo, hi = sorted((sign, (sign + 6) % 12))
        return self.stronger(lo, hi)

    def stronger_graha(self, a: str, b: str) -> str:
        """Stronger of two grahas (JHora's order; the first wins a full tie)."""
        sa, sb = self.signs[a], self.signs[b]
        for test in (lambda p, x: EXALT[p] == x, lambda p, x: DEBIL[p] != x,
                     lambda p, x: MOOLA[p] == x, _owns):
            ta, tb = test(a, sa), test(b, sb)
            if ta != tb:
                return a if ta else b
        return b if _advance(a, self.lon) < _advance(b, self.lon) else a

    def _saturn_or_ketu(self) -> str:
        """Stronger of Saturn and Ketu when they share a sign."""
        return self.stronger_graha("Sa", "Ke")

    def brahma(self, lagna: int) -> str:
        """Brahma: of the lords of the 6th, 8th and 12th from the stronger of the Lagna
        and the 7th, those in odd signs in the 7th..12th houses from it (else from the
        weaker one; else those in odd signs from the stronger, then from the weaker;
        else all three), the strongest; Saturn, Rahu and Ketu give way to Mars,
        Mercury and Jupiter (JHora)."""
        strong = self.stronger(lagna, (lagna + 6) % 12)
        weak = (lagna + 6) % 12 if strong == lagna else lagna
        lords = lambda base: [self.arudha_lords.get((base + k) % 12, LORD[(base + k) % 12])
                              for k in (5, 7, 11)]
        odd = lambda p: self.signs[p] % 2 == 0
        cands: list[str] = []
        for base in (strong, weak):
            cands = [p for p in lords(base) if odd(p) and (self.signs[p] - base) % 12 > 5]
            if cands:
                break
        if not cands:
            for base in (strong, weak):
                cands = [p for p in lords(base) if odd(p)]
                if cands:
                    break
        cands = cands or lords(strong)
        best = cands[0]
        for p in cands[1:]:
            best = self.stronger_graha(best, p)
        return {"Sa": "Ma", "Ra": "Me", "Ke": "Ju"}.get(best, best)

    def brahma_years(self, sign: int) -> int:
        """Years of a sign in Brahma dasha: count to the lord of its 6th (odd sign,
        forward) or 8th (even sign, backward), 0 in the sign itself; +1 exalted, -1
        debilitated."""
        odd = sign % 2 == 0
        h = (sign + (5 if odd else 7)) % 12
        p = self.arudha_lords.get(h, LORD[h])
        at = self.signs[p]
        n = (at - sign) % 12 if odd else (sign - at) % 12
        if EXALT[p] == at and n < 12:
            n += 1
        if DEBIL[p] == at and n > 0:
            n -= 1
        return n

    def ad_order(self, md: int) -> list[int]:
        """Antardasha signs: from the sign of the lord of the stronger of md and its 7th,
        forward if that sign is odd, with the Saturn/Ketu exception of the stronger."""
        strong = self.stronger_of_pair(md)
        start = self.signs[self.lord(strong)]
        step = 1 if start % 2 == 0 else -1
        e = self.exception(strong)
        if e == 1:
            step = 1
        elif e == 2:
            step = -step
        return [(start + step * i) % 12 for i in range(12)]

    def direction(self, sign: int) -> int:
        """+1 from an odd sign, -1 from an even one, with the Saturn/Ketu exception."""
        step = 1 if sign % 2 == 0 else -1
        e = self.exception(sign)
        return 1 if e == 1 else -step if e == 2 else step

    def exception(self, sign: int) -> int:
        """0 none, 1 Saturn (regular, forward), 2 Ketu (reverse)."""
        sat, ket = self.signs["Sa"] == sign, self.signs["Ke"] == sign
        if sat and ket:
            return 2 if self._saturn_or_ketu() == "Ke" else 1
        return 1 if sat else 2 if ket else 0

    def narayana_years(self, sign: int) -> int:
        return self._years_from(sign, self.lord(sign))


def narayana_dasha(lagna: int, signs: dict[str, int], longitudes: dict[str, float],
                   birth_jd: float, cfg: SchoolConfig = DEFAULT_CONFIG, cycles: int = 2,
                   levels: int = 2, points: dict[str, float] | None = None,
                   start_sign: int | None = None) -> list[Period]:
    """Narayana dasha of the rasi chart as JHora 8.0. Period.lord is the sign index as
    a string and Period.name the sign name. A sign with 0 years in a cycle is kept as
    a zero-length period (JHora lists it). start_sign replaces the Lagna as the sign
    whose stronger of itself and its 7th starts the dasha."""
    from .constants import SIGNS
    jc = JaiminiChart(signs, longitudes)
    seed = jc.stronger_of_pair(lagna if start_sign is None else start_sign)
    row = PROGRESSION[seed % 3]
    step = 1 if seed in FORWARD else -1
    exc = jc.exception(seed)
    if exc == 1:
        row, step = PROGRESSION[0], 1
    elif exc == 2:
        step = -step
    order = [(seed + step * k) % 12 for k in row]
    first = {s: jc.narayana_years(s) for s in order}
    out: list[Period] = []
    t = 0.0
    for c in range(cycles):
        for s in order:
            yrs = first[s] if c == 0 else 12 - first[s]
            md = Period(str(s), 0, 0, 1, name=SIGNS[s], start_years=t, end_years=t + yrs)
            if levels > 1:
                for i, a in enumerate(jc.ad_order(s)):
                    md.children.append(Period(str(a), 0, 0, 2, name=SIGNS[a],
                                              start_years=t + yrs * i / 12,
                                              end_years=t + yrs * (i + 1) / 12))
            out.append(md)
            t += yrs
    _assign_jd(out, YearClock(birth_jd, cfg))
    return out


def _rasi_periods(order: list[int], years: dict[int, float], ads, birth_jd: float,
                  cfg: SchoolConfig, levels: int) -> list[Period]:
    from .constants import SIGNS
    out: list[Period] = []
    t = 0.0
    for s in order:
        yrs = years[s]
        md = Period(str(s), 0, 0, 1, name=SIGNS[s], start_years=t, end_years=t + yrs)
        if levels > 1:
            for i, a in enumerate(ads(s)):
                md.children.append(Period(str(a), 0, 0, 2, name=SIGNS[a],
                                          start_years=t + yrs * i / 12,
                                          end_years=t + yrs * (i + 1) / 12))
        out.append(md)
        t += yrs
    _assign_jd(out, YearClock(birth_jd, cfg))
    return out


MODAL_YEARS = (7, 8, 9)          # movable, fixed, dual


def sthira_dasha(lagna: int, signs: dict[str, int], longitudes: dict[str, float],
                 birth_jd: float, cfg: SchoolConfig = DEFAULT_CONFIG,
                 levels: int = 2, points: dict[str, float] | None = None) -> list[Period]:
    """Sthira dasha: from the sign of Brahma, forward from an odd sign (Saturn/Ketu
    exception applies); 7, 8 and 9 years for movable, fixed and dual signs."""
    jc = JaiminiChart(signs, longitudes)
    seed = jc.signs[jc.brahma(lagna)]
    step = jc.direction(seed)
    order = [(seed + step * k) % 12 for k in range(12)]
    return _rasi_periods(order, {s: MODAL_YEARS[s % 3] for s in order}, jc.ad_order,
                         birth_jd, cfg, levels)


def niryana_shoola_dasha(lagna: int, signs: dict[str, int], longitudes: dict[str, float],
                         birth_jd: float, cfg: SchoolConfig = DEFAULT_CONFIG,
                         levels: int = 2, points: dict[str, float] | None = None) -> list[Period]:
    """Niryana Shoola dasha: from the stronger of the 2nd and 8th houses, forward from
    an odd sign (Saturn/Ketu exception applies); 7, 8, 9 years by sign kind."""
    jc = JaiminiChart(signs, longitudes)
    seed = jc.stronger_of_pair((lagna + 7) % 12)
    step = jc.direction(seed)
    order = [(seed + step * k) % 12 for k in range(12)]
    return _rasi_periods(order, {s: MODAL_YEARS[s % 3] for s in order}, jc.ad_order,
                         birth_jd, cfg, levels)


def shoola_dasha(lagna: int, signs: dict[str, int], longitudes: dict[str, float],
                 birth_jd: float, cfg: SchoolConfig = DEFAULT_CONFIG,
                 levels: int = 2, from_house: int = 1,
                 points: dict[str, float] | None = None) -> list[Period]:
    """Shoola dasha: from the stronger of the house (default the Lagna) and its 7th,
    always forward, 9 years each; antardashas forward from the stronger of the dasa
    sign and its 7th (JHora's default antardasha option)."""
    jc = JaiminiChart(signs, longitudes)
    seed = jc.stronger_of_pair((lagna + from_house - 1) % 12)
    order = [(seed + k) % 12 for k in range(12)]
    return _rasi_periods(order, {s: 9 for s in order},
                         lambda s: [(jc.stronger_of_pair(s) + i) % 12 for i in range(12)],
                         birth_jd, cfg, levels)


def brahma_dasha(lagna: int, signs: dict[str, int], longitudes: dict[str, float],
                 birth_jd: float, cfg: SchoolConfig = DEFAULT_CONFIG,
                 levels: int = 2, points: dict[str, float] | None = None) -> list[Period]:
    """Brahma dasha: from Brahma's sign (its 7th if that sign is even), forward; two
    cycles (years, then 12 minus years); antardashas forward from the lord's sign."""
    jc = JaiminiChart(signs, longitudes)
    seed = jc.signs[jc.brahma(lagna)]
    if seed % 2 == 1:
        seed = (seed + 6) % 12
    order = [(seed + k) % 12 for k in range(12)]
    first = {s: jc.brahma_years(s) for s in order}
    ads = lambda s: [(jc.signs[jc.lord(s)] + i) % 12 for i in range(12)]
    p1 = _rasi_periods(order, first, ads, birth_jd, cfg, levels)
    return _two_cycles(p1, order, first, ads, birth_jd, cfg, levels)


def _two_cycles(p1, order, first, ads, birth_jd, cfg, levels):
    from .constants import SIGNS
    t = p1[-1].end_years if p1 else 0.0
    out = list(p1)
    for s in order:
        yrs = 12 - first[s]
        md = Period(str(s), 0, 0, 1, name=SIGNS[s], start_years=t, end_years=t + yrs)
        if levels > 1:
            for i, a in enumerate(ads(s)):
                md.children.append(Period(str(a), 0, 0, 2, name=SIGNS[a],
                                          start_years=t + yrs * i / 12,
                                          end_years=t + yrs * (i + 1) / 12))
        out.append(md)
        t += yrs
    _assign_jd(out, YearClock(birth_jd, cfg))
    return out


NAVAMSA_EVEN = (7, 6, 5, 10, 9, 2, 1, 0, 11, 4, 3, 8)   # JHora's start for even signs


def navamsa_dasha(lagna: int, signs: dict[str, int], longitudes: dict[str, float],
                  birth_jd: float, cfg: SchoolConfig = DEFAULT_CONFIG,
                  levels: int = 2, points: dict[str, float] | None = None) -> list[Period]:
    """Navamsa dasha: from the stronger of the Lagna and the 7th (an even sign replaced
    by JHora's table NAVAMSA_EVEN), forward, 9 years each; antardashas likewise from
    the stronger of the dasa sign and its 7th."""
    jc = JaiminiChart(signs, longitudes)
    def start(x: int) -> int:
        s = jc.stronger_of_pair(x)
        return NAVAMSA_EVEN[s] if s % 2 == 1 else s
    seed = start(lagna)
    order = [(seed + k) % 12 for k in range(12)]
    return _rasi_periods(order, {s: 9 for s in order},
                         lambda s: [(start(s) + i) % 12 for i in range(12)], birth_jd, cfg, levels)


def varnada_dasha(lagna: int, signs: dict[str, int], longitudes: dict[str, float],
                  birth_jd: float, cfg: SchoolConfig = DEFAULT_CONFIG,
                  levels: int = 2, points: dict[str, float] | None = None) -> list[Period]:
    """Varnada dasha: from the stronger of the Lagna and the Hora Lagna, forward from an
    odd sign; years from the Varnada Lagna to the sign (two cycles: then 12 minus);
    antardashas from the dasa sign, forward if odd. Needs points HL and VL (longitudes)."""
    jc = JaiminiChart(signs, longitudes)
    seed = jc.stronger(lagna, int(points["HL"] // 30))
    step = 1 if seed % 2 == 0 else -1
    order = [(seed + step * k) % 12 for k in range(12)]
    vl = int(points["VL"] // 30)
    first = {s: (s - vl) % 12 for s in order}
    ads = lambda s: [(s + (1 if s % 2 == 0 else -1) * i) % 12 for i in range(12)]
    p1 = _rasi_periods(order, first, ads, birth_jd, cfg, levels)
    return _two_cycles(p1, order, first, ads, birth_jd, cfg, levels)


KENDRADI = (0, 3, 6, 9, 1, 4, 7, 10, 2, 5, 8, 11)   # kendras, panapharas, apoklimas


def lagna_kendradi_dasha(lagna: int, signs: dict[str, int], longitudes: dict[str, float],
                         birth_jd: float, cfg: SchoolConfig = DEFAULT_CONFIG,
                         levels: int = 2, points: dict[str, float] | None = None) -> list[Period]:
    """Lagna Kendradi rasi dasha: from the stronger of the Lagna and the 7th, its
    kendras, panapharas and apoklimas, forward from an odd sign (Saturn/Ketu exception);
    Narayana years and antardashas, two cycles."""
    jc = JaiminiChart(signs, longitudes)
    seed = jc.stronger_of_pair(lagna)
    step = jc.direction(seed)
    order = [(seed + step * k) % 12 for k in KENDRADI]
    first = {s: jc.narayana_years(s) for s in order}
    p1 = _rasi_periods(order, first, jc.ad_order, birth_jd, cfg, levels)
    return _two_cycles(p1, order, first, jc.ad_order, birth_jd, cfg, levels)


def _sorted_strongest_first(jc: JaiminiChart, group: list[int]) -> list[int]:
    out: list[int] = []
    for x in group:                      # JHora's insertion sort
        j = 0
        while j < len(out) and jc.stronger(out[j], x, dignity_first=True) != x:
            j += 1
        out.insert(j, x)
    return out


def ak_kendradi_dasha(lagna: int, signs: dict[str, int], longitudes: dict[str, float],
                      birth_jd: float, cfg: SchoolConfig = DEFAULT_CONFIG,
                      levels: int = 2, points: dict[str, float] | None = None) -> list[Period]:
    """Atma Karaka Kendradi rasi dasha: from the stronger of the Atma Karaka's sign and
    its 7th, the kendras, then panapharas, then apoklimas (forward), each group ordered
    strongest first; Narayana years and antardashas, two cycles."""
    from .jaimini import chara_karakas
    jc = JaiminiChart(signs, longitudes)
    ak = chara_karakas(longitudes, cfg.chara_karakas)["AK"]
    seed = jc.stronger_of_pair(jc.signs[ak])
    order: list[int] = []
    for g in range(3):
        order += _sorted_strongest_first(jc, [(seed + g + 3 * k) % 12 for k in range(4)])
    first = {s: jc.narayana_years(s) for s in order}
    p1 = _rasi_periods(order, first, jc.ad_order, birth_jd, cfg, levels)
    return _two_cycles(p1, order, first, jc.ad_order, birth_jd, cfg, levels)


def sudasa_dasha(lagna: int, signs: dict[str, int], longitudes: dict[str, float],
                 birth_jd: float, cfg: SchoolConfig = DEFAULT_CONFIG,
                 levels: int = 2, points: dict[str, float] | None = None) -> list[Period]:
    """Sudasa: from the strongest kendra from the Sree Lagna, its kendras; then from the
    strongest of the next four signs, and so on; direction by the Sree Lagna's sign
    (Saturn/Ketu exception). Narayana years; the first dasa is scaled by the part of
    its sign the Sree Lagna has still to cross. Two cycles. Antardashas: consecutive
    signs from the stronger of the dasa sign and its 7th, forward if it is odd
    (Saturn/Ketu exception; JHora's default). Needs points SL and La (longitudes)."""
    jc = JaiminiChart(signs, longitudes, points.get("La", lagna * 30.0))
    sl_lon = points["SL"]
    sl = int(sl_lon // 30)
    step = jc.direction(sl)
    def strongest(xs: list[int]) -> int:
        b = xs[0]
        for x in xs[1:]:
            b = jc.stronger(b, x)
        return b
    g1 = strongest([(sl + 3 * k) % 12 for k in range(4)])
    # As JHora, the first candidate is not reduced mod 12 (Pisces + 1 = "sign 12").
    g2 = strongest([g1 + 1] + [(g1 + 1 + 3 * k) % 12 for k in range(1, 4)]) % 12
    g3 = strongest([g2 + 1] + [(g2 + 1 + 3 * k) % 12 for k in range(1, 4)]) % 12
    order = [(g + step * 3 * k) % 12 for g in (g1, g2, g3) for k in range(4)]
    balance = 1 - (sl_lon % 30) / 30
    first = {s: float(jc.narayana_years(s)) for s in order}
    first[order[0]] *= balance
    def ads(s: int) -> list[int]:
        b = jc.stronger_of_pair(s)
        st = jc.direction(b)
        return [(b + st * k) % 12 for k in range(12)]
    p1 = _rasi_periods(order, first, ads, birth_jd, cfg, levels)
    return _two_cycles(p1, order, first, ads, birth_jd, cfg, levels)


# Antardasha steps from the stronger of the dasa sign and its 7th, by the dasa
# sign's kind (JHora's tables for Trikona and Drig dasha): movable signs regularly,
# fixed by every sixth sign, dual by kendras then panapharas then apoklimas.
AD_STEPS = (
    tuple(range(12)),
    (0, 5, 10, 3, 8, 1, 6, 11, 4, 9, 2, 7),
    (0, 3, 6, 9, 4, 7, 10, 1, 8, 11, 2, 5),
)


def _stepped_ads(jc: JaiminiChart):
    def ads(md: int) -> list[int]:
        base = jc.stronger_of_pair(md)
        st = 1 if md % 2 == 0 else -1
        return [(base + st * k) % 12 for k in AD_STEPS[md % 3]]
    return ads


def trikona_dasha(lagna: int, signs: dict[str, int], longitudes: dict[str, float],
                  birth_jd: float, cfg: SchoolConfig = DEFAULT_CONFIG,
                  levels: int = 2, points: dict[str, float] | None = None) -> list[Period]:
    """Trikona dasha: from the strongest of the Lagna and its trines (compared in turn),
    regular signs forward from an odd sign, backward from an even one; Narayana years
    (JHora lists one cycle); antardashas by AD_STEPS."""
    jc = JaiminiChart(signs, longitudes)
    seed = jc.stronger(jc.stronger(lagna, (lagna + 4) % 12), (lagna + 8) % 12)
    step = 1 if seed % 2 == 0 else -1
    order = [(seed + step * k) % 12 for k in range(12)]
    return _rasi_periods(order, {s: jc.narayana_years(s) for s in order}, _stepped_ads(jc),
                         birth_jd, cfg, levels)


def _drig_group(sign: int) -> list[int]:
    m = sign % 3
    step = -1 if m == 0 else 1 if m == 1 else (1 if sign % 2 == 0 else -1)
    out, s = [sign], sign
    for _ in range(11):
        s = (s + step) % 12
        if s != sign and sees(s, sign):
            out.append(s)
    return out


def drig_dasha(lagna: int, signs: dict[str, int], longitudes: dict[str, float],
               birth_jd: float, cfg: SchoolConfig = DEFAULT_CONFIG,
               levels: int = 2, points: dict[str, float] | None = None) -> list[Period]:
    """Drig dasha (JHora's Parashara option, its default): the 9th, 10th and 11th
    houses, each followed by the signs it aspects (backward from a movable sign,
    forward from a fixed one, by oddity from a dual one); 7, 8, 9 years by sign kind;
    antardashas by AD_STEPS."""
    jc = JaiminiChart(signs, longitudes)
    order = [s for h in (8, 9, 10) for s in _drig_group((lagna + h) % 12)]
    return _rasi_periods(order, {s: MODAL_YEARS[s % 3] for s in order}, _stepped_ads(jc),
                         birth_jd, cfg, levels)


def yogardha_dasha(lagna: int, signs: dict[str, int], longitudes: dict[str, float],
                   birth_jd: float, cfg: SchoolConfig = DEFAULT_CONFIG,
                   levels: int = 2, points: dict[str, float] | None = None) -> list[Period]:
    """Yogardha dasha: from the stronger of the Lagna and the 7th, regular signs,
    forward from an odd sign (Saturn/Ketu exception); years the mean of the Narayana
    and Sthira years; Narayana antardashas; two cycles."""
    jc = JaiminiChart(signs, longitudes)
    seed = jc.stronger_of_pair(lagna)
    step = jc.direction(seed)
    order = [(seed + step * k) % 12 for k in range(12)]
    first = {s: (jc.narayana_years(s) + MODAL_YEARS[s % 3]) / 2 for s in order}
    p1 = _rasi_periods(order, first, jc.ad_order, birth_jd, cfg, levels)
    return _two_cycles(p1, order, first, jc.ad_order, birth_jd, cfg, levels)


def lagnamsaka_dasha(lagna: int, signs: dict[str, int], longitudes: dict[str, float],
                     birth_jd: float, cfg: SchoolConfig = DEFAULT_CONFIG,
                     levels: int = 2, points: dict[str, float] | None = None) -> list[Period]:
    """Lagnamsaka dasha (JHora's default, from the D-9): Narayana dasha of the rasi
    chart started from the navamsa Lagna's sign. Needs points La (longitude)."""
    from .vargas import varga_sign
    return narayana_dasha(lagna, signs, longitudes, birth_jd, cfg, levels=levels,
                          start_sign=varga_sign(points["La"], 9))


def padanaathamsa_dasha(lagna: int, signs: dict[str, int], longitudes: dict[str, float],
                        birth_jd: float, cfg: SchoolConfig = DEFAULT_CONFIG,
                        levels: int = 2, points: dict[str, float] | None = None) -> list[Period]:
    """Padanaathamsa dasha (D-9): Narayana dasha of the navamsa chart started from the
    navamsa sign of the lord of the Arudha Lagna (plain lords; the Arudha Lagna as in
    bhava_arudhas). Degrees for the tie-breaks stay those of the rasi chart."""
    from .vargas import varga_sign
    jc = JaiminiChart(signs, longitudes)
    al = jc.bhava_arudhas(lagna)[0]
    d9 = {p: varga_sign(longitudes[p], 9) for p in GRAHAS9}
    d9_lon = {p: d9[p] * 30.0 + longitudes[p] % 30.0 for p in GRAHAS9}
    return narayana_dasha(lagna, d9, d9_lon, birth_jd, cfg, levels=levels,
                          start_sign=d9[LORD[al]])


def _count_to(sign: int, at: int, forward: bool) -> int:
    """Signs from `sign` to `at`, 1..12 (12 when they coincide)."""
    return ((at - sign) % 12 if forward else (sign - at) % 12) or 12


def _parasara_co_lord(jc: JaiminiChart, a: str, b: str) -> str:
    """JHora's co-lord for Parashara's Chara dasha: the other one if one occupies the
    sign; more grahas with it; movable over fixed over dual; the longer count from the
    sign (with the exaltation/debilitation year); the first (Saturn, Mars) on a tie."""
    own = 10 if a == "Sa" else 7
    sa, sb = jc.signs[a], jc.signs[b]
    if sa == own and sb != own:
        return b
    if sb == own and sa != own:
        return a
    ka, kb = jc.occupants(sa), jc.occupants(sb)
    if ka != kb:
        return a if ka > kb else b
    if sa % 3 != sb % 3:
        return a if sa % 3 < sb % 3 else b
    def yrs(p: str, at: int) -> int:
        n = _count_to(own, at, (own // 3) % 2 == 0)
        if EXALT[p] == at and n < 12:
            n += 1
        if DEBIL[p] == at and n > 0:
            n -= 1
        return n
    return a if yrs(b, sb) <= yrs(a, sa) else b


def chara_parasara_dasha(lagna: int, signs: dict[str, int], longitudes: dict[str, float],
                         birth_jd: float, cfg: SchoolConfig = DEFAULT_CONFIG,
                         levels: int = 2, points: dict[str, float] | None = None,
                         exaltation_adjust: bool = True) -> list[Period]:
    """Chara dasha of Parashara as JHora 8.0: from the Lagna, regular signs forward from
    Ar, Le, Vi, Li, Aq, Pi and backward from the others; years the count from the sign
    to its lord (forward from Ar, Ta, Ge, Li, Sc, Sg), 12 in the sign itself, +1 exalted
    and -1 debilitated (JHora's "Chara dasa exaltation exception", on by default); two
    cycles; antardashas by AD_STEPS."""
    jc = JaiminiChart(signs, longitudes)
    lords = {10: _parasara_co_lord(jc, "Sa", "Ra"), 7: _parasara_co_lord(jc, "Ma", "Ke")}
    step = 1 if lagna in FORWARD else -1
    order = [(lagna + step * k) % 12 for k in range(12)]
    def years(s: int) -> int:
        p = lords.get(s, LORD[s])
        at = jc.signs[p]
        n = _count_to(s, at, (s // 3) % 2 == 0)
        if exaltation_adjust:
            if EXALT[p] == at and n < 12:
                n += 1
            if DEBIL[p] == at and n > 0:
                n -= 1
        return n
    first = {s: years(s) for s in order}
    p1 = _rasi_periods(order, first, _stepped_ads(jc), birth_jd, cfg, levels)
    return _two_cycles(p1, order, first, _stepped_ads(jc), birth_jd, cfg, levels)


RANGACHARYA_STEPS = (
    tuple(range(12)),
    (0, 5, 10, 3, 8, 1, 6, 11, 4, 9, 2, 7),
    (0, 4, 8, 1, 5, 9, 2, 6, 10, 3, 7, 11),
)


def chara_rangacharya_dasha(lagna: int, signs: dict[str, int], longitudes: dict[str, float],
                            birth_jd: float, cfg: SchoolConfig = DEFAULT_CONFIG,
                            levels: int = 2, points: dict[str, float] | None = None) -> list[Period]:
    """Iranganti Rangacharya's Chara dasha as JHora 8.0: from the Lagna, forward from an
    odd sign, backward from an even one; movable signs regularly, fixed by every sixth,
    dual by trines; years: one more than the count from the sign to its lord (plain
    lords), backward when the lord is in an odd sign, 12 in the sign itself; two
    cycles; antardashas from the dasa sign by the same steps."""
    jc = JaiminiChart(signs, longitudes)
    step = 1 if lagna % 2 == 0 else -1
    order = [(lagna + step * k) % 12 for k in RANGACHARYA_STEPS[lagna % 3]]
    def years(s: int) -> int:
        at = jc.signs[LORD[s]]
        if at == s:
            return 12
        n = (s - at) % 12 if at % 2 == 0 else (at - s) % 12
        return (n or 12) + 1
    ads = lambda s: [(s + (1 if s % 2 == 0 else -1) * k) % 12 for k in RANGACHARYA_STEPS[s % 3]]
    first = {s: years(s) for s in order}
    p1 = _rasi_periods(order, first, ads, birth_jd, cfg, levels)
    return _two_cycles(p1, order, first, ads, birth_jd, cfg, levels)


def mandooka_knrao_dasha(lagna: int, signs: dict[str, int], longitudes: dict[str, float],
                         birth_jd: float, cfg: SchoolConfig = DEFAULT_CONFIG,
                         levels: int = 2, points: dict[str, float] | None = None) -> list[Period]:
    """K. N. Rao's Mandooka dasha as JHora 8.0: from the Lagna (its 7th if the Lagna is
    an even sign), kendras then panapharas then apoklimas, forward from an odd sign;
    years the inclusive count from the sign to its lord (plain lords; forward from an
    odd sign), 12 in the sign itself and 10 for the 7th; antardashas from the dasa sign
    in the same pattern."""
    jc = JaiminiChart(signs, longitudes)
    start = lagna if lagna % 2 == 0 else (lagna + 6) % 12
    step = 1 if start % 2 == 0 else -1
    order = [(start + step * k) % 12 for k in KENDRADI]
    def years(s: int) -> int:
        n = _count_to(s, jc.signs[LORD[s]], s % 2 == 0) % 12 + 1
        return 12 if n == 1 else 10 if n == 7 else n
    return _rasi_periods(order, {s: years(s) for s in order},
                         lambda s: [(s + step * k) % 12 for k in KENDRADI], birth_jd, cfg, levels)


# name -> (function, label). Each takes (lagna sign, graha signs, graha longitudes,
# birth jd, cfg, levels=, points=) where points maps "La" and the special lagnas
# (HL, VL, SL, ...) to longitudes.
RASI_DASHAS = {
    "narayana": (narayana_dasha, "Narayana"),
    "lagnamsaka": (lagnamsaka_dasha, "Lagnamsaka (from D-9)"),
    "padanaathamsa": (padanaathamsa_dasha, "Padanaathamsa (D-9)"),
    "sudasa": (sudasa_dasha, "Sudasa"),
    "drig": (drig_dasha, "Drig"),
    "lagna_kendradi": (lagna_kendradi_dasha, "Lagna Kendradi"),
    "ak_kendradi": (ak_kendradi_dasha, "Atma Karaka Kendradi"),
    "trikona": (trikona_dasha, "Trikona"),
    "chara_parasara": (chara_parasara_dasha, "Chara (Parashara)"),
    "chara_rangacharya": (chara_rangacharya_dasha, "Chara (Iranganti Rangacharya)"),
    "yogardha": (yogardha_dasha, "Yogardha"),
    "shoola": (shoola_dasha, "Shoola"),
    "niryana_shoola": (niryana_shoola_dasha, "Niryana Shoola"),
    "brahma": (brahma_dasha, "Brahma"),
    "sthira": (sthira_dasha, "Sthira"),
    "mandooka_knrao": (mandooka_knrao_dasha, "Mandooka (K. N. Rao)"),
    "navamsa": (navamsa_dasha, "Navamsa"),
    "varnada": (varnada_dasha, "Varnada"),
}


def rasi_dasha(name: str, chart, cfg: SchoolConfig = DEFAULT_CONFIG, levels: int = 2,
               points: dict[str, float] | None = None) -> list[Period]:
    """A rasi dasha of RASI_DASHAS for a jyotishnet_engine.chart.Chart. `points`
    overrides chart points (longitudes), e.g. {"SL": ...}."""
    signs = {k: g.sign for k, g in chart.grahas.items()}
    lons = {k: g.longitude for k, g in chart.grahas.items()}
    pts = {"La": chart.lagna.longitude, **{k: p.longitude for k, p in chart.special.items()},
           **(points or {})}
    fn = RASI_DASHAS[name][0]
    return fn(chart.lagna.sign, signs, lons, chart.jd_ut, cfg, levels=levels, points=pts)

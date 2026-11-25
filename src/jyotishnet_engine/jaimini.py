# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Rahul Sathe
"""Jaimini building blocks and Chara dasha (K. N. Rao's method).

- Rasi drishti (sign aspects): a movable sign aspects the fixed signs except the
  one next to it, a fixed sign aspects the movable signs except the one next to
  it, and a dual sign aspects the other dual signs.
- Stronger co-lord of Scorpio (Mars/Ketu) and Aquarius (Saturn/Rahu), by the
  usual Jaimini rules in order:
    0. If one lord occupies the sign, the other is taken.
    1. The lord with more planets (and the Lagna) in its sign.
    2. The lord conjoined or aspected (rasi drishti) by more of Jupiter,
       Mercury and its own dispositor.
    3. The exalted lord.
    4. The lord in a stronger kind of sign: dual > fixed > movable.
    5. The lord further advanced in its sign (Rahu and Ketu count backwards).
- Chara dasha after K. N. Rao: mahadashas of signs from the Lagna, forward when
  the 9th from the Lagna is a savya (odd-footed) sign, otherwise backward. The
  length is the count from the sign to its lord (forward for savya signs,
  backward for apasavya), minus one; 12 if the lord is in the sign itself;
  otherwise one year more if the lord is exalted and one less if debilitated
  (Mercury in Virgo counts as exalted, per BPHS; PyJHora treats it as own sign). The second cycle gives each sign
  12 minus its first-cycle years. Antardashas are 12 equal parts starting next to
  the mahadasha sign and ending with it.

The antardasha direction table and the second-cycle rule differ between
authors; see docs/DECISIONS.md #3.

Chara karakas: the grahas ranked by degrees within their sign, highest first, Rahu
counted backwards (30 - degrees). Eight karakas (Sun to Saturn and Rahu; AK, AmK,
BK, MK, PiK, PK, GK, DK; JHora's default) or seven (Sun to Saturn; no PiK).
"""

from __future__ import annotations

from .config import DEFAULT_CONFIG, SchoolConfig
from .constants import EXALTATION, SIGN_LORD
from .dasha import Period, YearClock, _assign_jd

SAVYA = frozenset({0, 1, 2, 6, 7, 8})          # odd-footed: Ar Ta Ge Li Sc Sg
CO_LORDS = {7: ("Ma", "Ke"), 10: ("Sa", "Ra")}
# Node dignities used in Jaimini (exalted / debilitated signs).
NODE_EXALTED = {"Ra": {1, 2}, "Ke": {7, 8}}
NODE_DEBILITATED = {"Ra": {7, 8}, "Ke": {1, 2}}
# Antardasha runs forward from these mahadasha signs, backward from the others
# (K. N. Rao, as implemented in PyJHora).
KNRAO_AD_FORWARD = frozenset({0, 4, 5, 6, 10, 11})
CO_LORD_PLANETS = ("Su", "Mo", "Ma", "Me", "Ju", "Ve", "Sa", "Ra", "Ke")


KARAKAS_8 = ("AK", "AmK", "BK", "MK", "PiK", "PK", "GK", "DK")
# Seven portfolios (BPHS ch. 32): no separate PK; the MK also signifies children.
KARAKAS_7 = ("AK", "AmK", "BK", "MK", "PiK", "GK", "DK")
SEVEN = ("Su", "Mo", "Ma", "Me", "Ju", "Ve", "Sa")


def _karaka_degree(longitudes: dict[str, float], p: str) -> float:
    d = longitudes[p] % 30.0
    return 30.0 - d if p == "Ra" else d          # Rahu moves backwards


def chara_karakas(longitudes: dict[str, float], n: int | str = 8) -> dict[str, str]:
    """{karaka: graha} by degrees in the sign (Rahu counted as 30 deg minus his degree).

    n = 8: Sun to Rahu (Jagannatha Hora's default). n = 7: Sun to Saturn, the MK also
    being the PK (BPHS 32). n = "parasara": BPHS 32 as P. V. R. Narasimha Rao reads it
    ("Parasara's Teachings on Chara Karakas", 2008, procedure steps 1-6,
    https://www.vedicastrologer.org/articles/c_karaka.pdf): 7 karakas, or 8 with Rahu
    when two of Sun..Saturn are in the same whole degree; the AK by full longitude, the
    others by whole degrees; planets in the same degree compete for as many portfolios,
    all but the lowest of which stay empty (to be judged from the fixed karaka, a
    strength judgment not made here) and the lowest goes to the most advanced of them.
    """
    if n == "parasara":
        return _parasara_karakas(longitudes)
    if n not in (7, 8):
        raise ValueError("chara karakas: n must be 7, 8 or 'parasara'")
    grahas = list(SEVEN) + (["Ra"] if n == 8 else [])
    ranked = sorted(grahas, key=lambda p: _karaka_degree(longitudes, p), reverse=True)
    k = dict(zip(KARAKAS_8 if n == 8 else KARAKAS_7, ranked))
    if n == 7:
        k["PK"] = k["MK"]
    return k


def _parasara_karakas(longitudes: dict[str, float]) -> dict[str, str]:
    whole = {p: int(_karaka_degree(longitudes, p)) for p in (*SEVEN, "Ra")}
    eight = len({whole[p] for p in SEVEN}) < 7
    grahas = list(SEVEN) + (["Ra"] if eight else [])
    names = KARAKAS_8 if eight else KARAKAS_7
    ak = max(grahas, key=lambda p: _karaka_degree(longitudes, p))
    rest = sorted((p for p in grahas if p != ak),
                  key=lambda p: (whole[p], _karaka_degree(longitudes, p)), reverse=True)
    k, slot, i = {"AK": ak}, 1, 0
    while i < len(rest) and slot < len(names):
        group = [p for p in rest[i:] if whole[p] == whole[rest[i]]]
        slot += len(group) - 1                   # the higher portfolios stay empty
        if slot < len(names):
            k[names[slot]] = group[0]            # the most advanced in that degree
        slot, i = slot + 1, i + len(group)
    if not eight and "MK" in k:
        k["PK"] = k["MK"]
    return k


def rasi_drishti(sign: int) -> set[int]:
    """Signs aspected by `sign` (Jaimini rasi drishti)."""
    m = sign % 3
    if m == 2:                                   # dual aspects the other duals
        return {s for s in range(12) if s % 3 == 2 and s != sign}
    target = 1 if m == 0 else 0                  # movable -> fixed, fixed -> movable
    adjacent = {(sign + 1) % 12, (sign - 1) % 12}
    return {s for s in range(12) if s % 3 == target and s not in adjacent}


def _exalted(p: str, sign: int) -> bool:
    return sign in NODE_EXALTED[p] if p in NODE_EXALTED else EXALTATION[p][0] == sign


def _debilitated(p: str, sign: int) -> bool:
    return sign in NODE_DEBILITATED[p] if p in NODE_DEBILITATED else (EXALTATION[p][0] + 6) % 12 == sign


def stronger_co_lord(sign: int, signs: dict[str, int], degrees: dict[str, float],
                     lagna: int) -> tuple[str, str]:
    """Stronger lord of Scorpio or Aquarius and the rule that decided it."""
    a, b = CO_LORDS[sign]
    sa, sb = signs[a], signs[b]
    if sa == sign and sb != sign:
        return b, "other lord occupies the sign"
    if sb == sign and sa != sign:
        return a, "other lord occupies the sign"

    def company(p: str) -> int:
        s = signs[p]
        return sum(1 for q in CO_LORD_PLANETS if q != p and signs[q] == s) + (lagna == s)

    def helpers(p: str) -> int:
        s = signs[p]
        aspecting = {x for x in range(12) if s in rasi_drishti(x)}
        n = 0
        for q in ("Ju", "Me", SIGN_LORD[s]):
            if q != p and (signs[q] == s or signs[q] in aspecting):
                n += 1
        return n

    for rule, key in (("more planets in its sign", company),
                      ("more of Jupiter, Mercury and dispositor", helpers),
                      ("exalted", lambda p: int(_exalted(p, signs[p]))),
                      ("stronger kind of sign", lambda p: signs[p] % 3)):
        ka, kb = key(a), key(b)
        if ka != kb:
            return (a if ka > kb else b), rule

    def advance(p: str) -> float:
        d = degrees[p] % 30.0
        return 30.0 - d if p in ("Ra", "Ke") else d
    return (a if advance(a) > advance(b) else b), "more advanced in its sign"


def jhora_co_lord(sign: int, signs: dict[str, int], degrees: dict[str, float]) -> str:
    """JHora 8.0's co-lord for K. N. Rao's Chara dasha: if one co-lord occupies the
    sign, the other; else the one with more grahas (Sun to Ketu) in its sign; else the
    higher degree in its sign (nodes not reversed); else the first (Saturn, Mars)."""
    a, b = CO_LORDS[sign]
    sa, sb = signs[a], signs[b]
    if sa == sign and sb != sign:
        return b
    if sb == sign and sa != sign:
        return a
    count = lambda s: sum(1 for q in CO_LORD_PLANETS if signs[q] == s)
    ca, cb = count(sa), count(sb)
    if ca != cb:
        return a if ca > cb else b
    return b if degrees[a] % 30.0 < degrees[b] % 30.0 else a


def sign_lord(sign: int, signs: dict[str, int], degrees: dict[str, float], lagna: int,
              rule: str = "knrao") -> str:
    if sign in CO_LORDS:
        if rule == "jhora":
            return jhora_co_lord(sign, signs, degrees)
        return stronger_co_lord(sign, signs, degrees, lagna)[0]
    return SIGN_LORD[sign]


def chara_years(sign: int, signs: dict[str, int], degrees: dict[str, float], lagna: int,
                exaltation_adjust: bool = True, co_lord_rule: str = "knrao") -> int:
    """First-cycle Chara dasha years of `sign` (K. N. Rao). With exaltation_adjust
    an exalted lord adds a year and a debilitated one takes one away (K. N. Rao's
    text); JHora 8.0 uses the plain count (SchoolConfig.chara_exaltation_adjust)."""
    lord = sign_lord(sign, signs, degrees, lagna, co_lord_rule)
    at = signs[lord]
    count = ((at - sign) % 12 if sign in SAVYA else (sign - at) % 12) + 1
    years = count - 1
    if years <= 0:
        return 12                     # lord in the sign itself: 12 years, no adjustment
    if not exaltation_adjust:
        return years
    if _exalted(lord, at):
        years += 1
    elif _debilitated(lord, at):
        years -= 1
    return years


def chara_dasha(lagna: int, signs: dict[str, int], degrees: dict[str, float], birth_jd: float,
                cfg: SchoolConfig = DEFAULT_CONFIG, cycles: int = 2,
                levels: int = 2) -> list[Period]:
    """K. N. Rao's Chara dasha from birth. Each Period's `lord` is the sign
    abbreviation index as a string ("0" = Aries) and `name` the sign name."""
    from .constants import SIGNS
    step = 1 if (lagna + 8) % 12 in SAVYA else -1
    order = [(lagna + step * i) % 12 for i in range(12)]
    first = {s: chara_years(s, signs, degrees, lagna, cfg.chara_exaltation_adjust,
                            cfg.chara_co_lord_rule) for s in order}
    out: list[Period] = []
    t = 0.0
    for c in range(cycles):
        for s in order:
            yrs = first[s] if c == 0 else 12 - first[s]
            if yrs <= 0:
                continue
            md = Period(str(s), 0, 0, 1, name=SIGNS[s], start_years=t, end_years=t + yrs)
            if levels > 1:
                ad_step = 1 if s in KNRAO_AD_FORWARD else -1
                u = t
                for i in range(12):
                    a = (s + ad_step * (i + 1)) % 12
                    md.children.append(Period(str(a), 0, 0, 2, name=SIGNS[a],
                                              start_years=u, end_years=u + yrs / 12))
                    u += yrs / 12
            out.append(md)
            t += yrs
    _assign_jd(out, YearClock(birth_jd, cfg))
    return out

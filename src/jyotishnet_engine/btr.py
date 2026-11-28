# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Rahul Sathe
"""Rectification helpers: score known life events against a candidate birth time.

For each event (type + date) and a candidate birth time, the Vimshottari mahadasha
and antardasha running on the event date are scored under one of two rule sets:

classical (default; rules/btr_classical.yaml, every condition cites its verse in
BPHS or Phaladeepika, see docs/research/BPHS-dasha-events.md):
- the antardasha lord gives the event (+1), the mahadasha lord gives it (+0.5):
  e.g. for marriage a planet that lords, occupies or aspects the 7th, or Venus
  (Phaladeepika 10.13, 19.26); for children the lords of 1, 5, 7, Jupiter and
  planets in or aspecting the 5th (Phaladeepika 12.25);
- the antardasha's quality, from its lord's place from the Lagna and from the
  mahadasha lord and its dignity (BPHS ch. 47, 52-60; Phaladeepika 20.14, 20.29):
  good +0.5, mixed +0.25 (reversed for check-only adverse events);
- Jupiter's transit on the date where a text gives one (+0.5).
The maximum depends on the event type; strong at 75% of it, partial at 37.5%.

modern (the R1 rules, rules/btr_events.yaml; not stated in BPHS): a lord is linked
when, in D1 or the event's varga, it lords or occupies an event house or is the
karaka; antardasha lord linked +1, mahadasha lord +0.5, Jupiter-Saturn double
transit on an event house +0.5; maximum 2.

`fit_curve` sums the scores over a window of candidate times and marks the best
fit. It also asks whether that best fit means anything: the same chart is scored
on many sets of random dates for the same event types, and the share of sets
whose best total reaches the real one is reported as a p-value (`significance`).
A best fit that random dates often match carries no information about the birth
time. `indicative_periods` lists antardashas that point to an event, for the four
event types that may be shown as indicative periods. Events marked check_only
(death, illness) are scored but never offered as predictions.

These are aids for an astrologer, not proofs; the rule files are drafts pending
expert review.
"""

from __future__ import annotations

import random
import zlib
from bisect import bisect_right
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from functools import lru_cache
from pathlib import Path

import yaml

from .chart import Chart, build_chart
from .config import DEFAULT_CONFIG, SchoolConfig
from .constants import GRAHA_DRISHTI, GRAHA_NAMES, SIGN_LORD, SIGNS
from .dasha import Period, running, vimshottari
from .ephemeris import body_longitude
from .timeutil import BirthData

RULES_FILE = Path(__file__).parent / "rules" / "btr_events.yaml"
GRAHAS = ("Su", "Mo", "Ma", "Me", "Ju", "Ve", "Sa", "Ra", "Ke")


@dataclass(frozen=True)
class EventRule:
    id: str
    name: str
    d1_houses: tuple[int, ...]
    varga: int
    varga_houses: tuple[int, ...]
    karaka: str
    check_only: bool = False
    indicative: bool = False
    source: dict = field(default_factory=dict)
    status: str = "draft"
    notes: str = ""


@lru_cache(maxsize=1)
def event_rules() -> dict[str, EventRule]:
    rows = yaml.safe_load(RULES_FILE.read_text(encoding="utf-8"))
    out = {}
    for r in rows:
        out[r["id"]] = EventRule(
            id=r["id"], name=r["name"], d1_houses=tuple(r["d1_houses"]), varga=r["varga"],
            varga_houses=tuple(r["varga_houses"]), karaka=r["karaka"],
            check_only=bool(r.get("check_only", False)), indicative=bool(r.get("indicative", False)),
            source=r.get("source", {}), status=r.get("status", "draft"), notes=r.get("notes", ""))
    return out


def required_vargas() -> list[int]:
    return sorted({1} | {r.varga for r in event_rules().values()})


# ------------------------------------------------------------------ linking

def _links_in(chart: Chart, varga: int, houses: tuple[int, ...], planet: str) -> list[str]:
    """Reasons `planet` is linked to `houses` in the given varga of `chart`."""
    if not houses:
        return []
    key = varga
    lagna = chart.lagna.vargas[key]
    reasons = []
    for h in houses:
        sign = (lagna + h - 1) % 12
        if SIGN_LORD[sign] == planet:
            reasons.append(f"lords D{varga} house {h}")
        if chart.grahas[planet].vargas[key] == sign:
            reasons.append(f"in D{varga} house {h}")
    return reasons


def links(chart: Chart, rule: EventRule, planet: str) -> list[str]:
    reasons = _links_in(chart, 1, rule.d1_houses, planet)
    if rule.varga != 1:
        reasons += _links_in(chart, rule.varga, rule.varga_houses, planet)
    if planet == rule.karaka:
        reasons.append("natural karaka")
    return reasons


def _aspects_or_occupies(planet: str, planet_sign: int, target_sign: int) -> bool:
    d = (target_sign - planet_sign) % 12 + 1
    return d == 1 or d in GRAHA_DRISHTI[planet]


def double_transit(natal: Chart, rule: EventRule, transit_signs: dict[str, int]) -> list[int]:
    """D1 event houses that Jupiter and Saturn both occupy or aspect."""
    return _double_transit(natal.lagna.sign, rule, transit_signs)


def _double_transit(lagna_sign: int, rule: EventRule, transit_signs: dict[str, int]) -> list[int]:
    hit = []
    for h in rule.d1_houses:
        sign = (lagna_sign + h - 1) % 12
        if (_aspects_or_occupies("Ju", transit_signs["Ju"], sign)
                and _aspects_or_occupies("Sa", transit_signs["Sa"], sign)):
            hit.append(h)
    return hit


# ------------------------------------------------------------------ classical rules

RULE_SETS = ("classical", "modern")
CLASSICAL_FILE = Path(__file__).parent / "rules" / "btr_classical.yaml"


@dataclass(frozen=True)
class ClassicalRule:
    id: str
    polarity: str                          # "good" or "adverse"
    significators: tuple[dict, ...]
    transit: dict | None
    notes: str = ""
    status: str = "draft"

    @property
    def max_score(self) -> float:
        return (1.5 if self.significators else 0.0) + 0.5 + (0.5 if self.transit else 0.0)


@lru_cache(maxsize=1)
def classical_rules() -> dict[str, ClassicalRule]:
    rows = yaml.safe_load(CLASSICAL_FILE.read_text(encoding="utf-8"))
    return {r["id"]: ClassicalRule(r["id"], r["polarity"], tuple(r.get("significators") or ()),
                                   r.get("transit"), r.get("notes", ""), r.get("status", "draft"))
            for r in rows}


def significator_reasons(chart: Chart, rule: ClassicalRule, planet: str) -> list[str]:
    """Why `planet` gives the event in its dasha, by the rule's cited conditions (D1)."""
    p = chart.grahas[planet]
    out = []
    for c in rule.significators:
        kind, cite = c["kind"], c["cite"]
        if kind == "graha":
            if planet == c["graha"]:
                out.append(f"is {GRAHA_NAMES[planet]} ({cite})")
            continue
        for h in c["houses"]:
            lord = chart.house_lords[h]
            if kind == "lord" and lord == planet:
                out.append(f"lords house {h} ({cite})")
            elif kind == "occupies" and p.house == h:
                out.append(f"in house {h} ({cite})")
            elif kind == "aspects" and h in p.aspects_houses and p.house != h:
                out.append(f"aspects house {h} ({cite})")
            elif kind == "joined_lord" and lord != planet and chart.grahas[lord].sign == p.sign:
                out.append(f"with the lord of house {h} ({cite})")
    return out


KENDRA_TRIKONA_11 = {1, 4, 5, 7, 9, 10, 11}
GOOD_FROM_DASHA_LORD = {1, 3, 4, 5, 7, 9, 10, 11}
DUSTHANA = {6, 8, 12}
COMBUST_ORB = {"Mo": 12.0, "Ma": 17.0, "Me": 14.0, "Ju": 11.0, "Ve": 10.0, "Sa": 15.0}
COMBUST_ORB_RETRO = {"Me": 12.0, "Ve": 8.0}


def _combust(chart: Chart, planet: str) -> bool:
    if planet not in COMBUST_ORB:
        return False
    p = chart.grahas[planet]
    orb = (COMBUST_ORB_RETRO if p.retrograde else COMBUST_ORB).get(planet, COMBUST_ORB[planet])
    return abs((p.longitude - chart.grahas["Su"].longitude + 180.0) % 360.0 - 180.0) < orb


def antardasha_quality(chart: Chart, maha: str, antar: str) -> tuple[str, list[str], list[str]]:
    """Good, bad or mixed antardasha by the antardasha lord's place and dignity.

    Good: in a kendra, trikona or the 11th from the Lagna (BPHS ch. 52-60 throughout,
    e.g. 52.4, 53.22; PD 20.14); exalted, moolatrikona or own sign (BPHS 47.7; PD 20.14);
    in a kendra, trikona, 3rd or 11th from the mahadasha lord (BPHS 54.17, 59.40).
    Bad: in the 6th, 8th or 12th from the Lagna (BPHS 47.6; PD 20.14) or from the
    mahadasha lord (PD 20.29); debilitated or in an enemy's sign (BPHS 47.6; PD 20.14);
    combust (BPHS 47.6). Good with no bad is good, bad with no good is bad, else mixed."""
    p, m = chart.grahas[antar], chart.grahas[maha]
    good, bad = [], []
    if p.house in KENDRA_TRIKONA_11:
        good.append(f"in house {p.house} from the Lagna (BPHS 52-60; PD 20.14)")
    if p.house in DUSTHANA:
        bad.append(f"in house {p.house} from the Lagna (BPHS 47.6; PD 20.14)")
    if antar != maha:
        rel = (p.sign - m.sign) % 12 + 1
        if rel in GOOD_FROM_DASHA_LORD:
            good.append(f"{rel} from the mahadasha lord (BPHS 54.17, 59.40)")
        if rel in DUSTHANA:
            bad.append(f"{rel} from the mahadasha lord (PD 20.29)")
    if p.dignity in ("exalted", "moolatrikona", "own"):
        good.append(f"{p.dignity} (BPHS 47.7; PD 20.14)")
    if p.dignity in ("debilitated", "enemy"):
        bad.append(f"{'in an enemy sign' if p.dignity == 'enemy' else 'debilitated'} (BPHS 47.6; PD 20.14)")
    if _combust(chart, antar):
        bad.append("combust (BPHS 47.6)")
    q = "good" if good and not bad else "bad" if bad and not good else "mixed"
    return q, good, bad


def transit_target_signs(chart: Chart, rule: ClassicalRule) -> frozenset[int]:
    """Signs in which Jupiter on the event date meets the rule's transit condition."""
    t = rule.transit
    if not t:
        return frozenset()
    if t["kind"] == "jupiter_trine_lord_sign_or_navamsa":      # PD 10.14
        lord = chart.grahas[chart.house_lords[t["house"]]]
        bases = {lord.sign, lord.vargas[9]}
        return frozenset((b + k) % 12 for b in bases for k in (0, 4, 8))
    if t["kind"] == "jupiter_from_moon":                         # PD 26.19-20
        mo = chart.grahas["Mo"].sign
        return frozenset((mo + h - 1) % 12 for h in t["houses"])
    raise ValueError(f"unknown transit kind {t['kind']}")


def _quality_points(rule: ClassicalRule, quality: str | None) -> float:
    if quality is None:
        return 0.0
    want, other = ("good", "bad") if rule.polarity == "good" else ("bad", "good")
    return 0.5 if quality == want else 0.0 if quality == other else 0.25


# ------------------------------------------------------------------ scoring

@dataclass
class EventCheck:
    event: str
    name: str
    date: str
    mahadasha: str | None
    antardasha: str | None
    maha_links: list[str]
    antar_links: list[str]
    double_transit_houses: list[int]
    score: float
    verdict: str
    check_only: bool
    rule_set: str = "modern"
    max_score: float = 2.0
    quality: str | None = None              # classical: good, bad or mixed antardasha
    quality_reasons: list[str] = field(default_factory=list)
    transit: list[str] = field(default_factory=list)


def verdict(score: float, max_score: float = 2.0) -> str:
    """strong at 75% of the event's maximum or more, partial at 37.5%, else weak."""
    return "strong" if score >= 0.75 * max_score else "partial" if score >= 0.375 * max_score else "weak"


def event_max(etype: str, rule_set: str) -> float:
    return classical_rules()[etype].max_score if rule_set == "classical" else 2.0


def _event_jd(birth: BirthData, d: date, cfg: SchoolConfig) -> float:
    return BirthData(datetime(d.year, d.month, d.day, 12, 0), birth.latitude, birth.longitude,
                     tz_name=birth.tz_name, utc_offset_hours=birth.utc_offset_hours).jd_ut()


@lru_cache(maxsize=65536)
def _transit_signs_jd(jd: float, cfg: SchoolConfig) -> dict[str, int]:
    return {p: int(body_longitude(jd, p, cfg) // 30) for p in ("Ju", "Sa")}


@dataclass
class _Candidate:
    """One candidate birth time, reduced to what scoring an event needs."""
    offset_s: int
    rule_set: str
    lagna_sign: int
    starts: list[float]                     # antardasha starts, ascending
    ends: list[float]
    lords: list[tuple[str, str]]            # (mahadasha, antardasha) lords
    linked: dict[str, frozenset[str]]       # event type -> grahas that give it
    quality: dict[tuple[str, str], str]     # classical: (maha, antar) -> good/bad/mixed
    transit: dict[str, frozenset[int]]      # classical: event type -> Jupiter signs that hit

    def lords_at(self, jd: float) -> tuple[str | None, str | None]:
        i = bisect_right(self.starts, jd) - 1
        if i < 0 or jd >= self.ends[i]:
            return None, None
        return self.lords[i]


def _from_chart(chart: Chart, offset_s: int, cfg: SchoolConfig, rule_set: str) -> _Candidate:
    if rule_set not in RULE_SETS:
        raise ValueError(f"rule_set must be one of {RULE_SETS}")
    periods = vimshottari(chart.grahas["Mo"].longitude, chart.jd_ut, cfg, levels=2)
    flat = sorted((ad.start_jd, ad.end_jd, md.lord, ad.lord) for md in periods for ad in md.children)
    if rule_set == "modern":
        linked = {k: frozenset(g for g in GRAHAS if links(chart, r, g)) for k, r in event_rules().items()}
        quality, transit = {}, {}
    else:
        cr = classical_rules()
        linked = {k: frozenset(g for g in GRAHAS if significator_reasons(chart, r, g)) for k, r in cr.items()}
        quality = {(m, a): antardasha_quality(chart, m, a)[0] for m in GRAHAS for a in GRAHAS}
        transit = {k: transit_target_signs(chart, r) for k, r in cr.items()}
    return _Candidate(offset_s, rule_set, chart.lagna.sign, [f[0] for f in flat], [f[1] for f in flat],
                      [(f[2], f[3]) for f in flat], linked, quality, transit)


def _candidate(birth: BirthData, offset_s: int, cfg: SchoolConfig, vargas: list[int],
               rule_set: str) -> _Candidate:
    chart = build_chart(birth.shifted(minutes=offset_s / 60.0), cfg, vargas)
    return _from_chart(chart, offset_s, cfg, rule_set)


def _score(c: _Candidate, etype: str, jd: float, signs: dict[str, int]) -> float:
    """The score check_events gives this event at this candidate time."""
    md, ad = c.lords_at(jd)
    lk = c.linked[etype]
    s = (1.0 if ad in lk else 0.0) + (0.5 if md in lk else 0.0)
    if c.rule_set == "modern":
        return s + (0.5 if _double_transit(c.lagna_sign, event_rules()[etype], signs) else 0.0)
    rule = classical_rules()[etype]
    q = c.quality.get((md, ad)) if md and ad else None
    return s + _quality_points(rule, q) + (0.5 if signs["Ju"] in c.transit[etype] else 0.0)


def check_events(birth: BirthData, events: list[tuple[str, date]],
                 cfg: SchoolConfig = DEFAULT_CONFIG, chart: Chart | None = None,
                 rule_set: str = "classical") -> list[EventCheck]:
    """Score each (event type, date) for the birth time in `birth`."""
    rules = event_rules()
    chart = chart or build_chart(birth, cfg, required_vargas())
    cand = _from_chart(chart, 0, cfg, rule_set)
    out = []
    for etype, d in events:
        rule = rules[etype]
        jd = _event_jd(birth, d, cfg)
        md, ad = cand.lords_at(jd)
        signs = _transit_signs_jd(jd, cfg)
        score = _score(cand, etype, jd, signs)
        mx = event_max(etype, rule_set)
        if rule_set == "modern":
            ml = links(chart, rule, md) if md else []
            al = links(chart, rule, ad) if ad else []
            out.append(EventCheck(etype, rule.name, d.isoformat(), md, ad, ml, al,
                                  _double_transit(chart.lagna.sign, rule, signs), score,
                                  verdict(score, mx), rule.check_only, rule_set, mx))
            continue
        cr = classical_rules()[etype]
        ml = significator_reasons(chart, cr, md) if md else []
        al = significator_reasons(chart, cr, ad) if ad else []
        q, good, bad = antardasha_quality(chart, md, ad) if md and ad else (None, [], [])
        tr = []
        if cr.transit and signs["Ju"] in cand.transit[etype]:
            tr = [f"Jupiter in {SIGNS[signs['Ju']]} ({cr.transit['cite']})"]
        out.append(EventCheck(etype, rule.name, d.isoformat(), md, ad, ml, al, [], score,
                              verdict(score, mx), rule.check_only, rule_set, mx, q,
                              [f"good: {r}" for r in good] + [f"bad: {r}" for r in bad], tr))
    return out


def _best_total(cands: list[_Candidate], scored: list[tuple[str, float, dict[str, int]]]) -> float:
    return max(sum(_score(c, e, jd, sg) for e, jd, sg in scored) for c in cands)


# Random dates for the significance test: each event keeps its type and gets a date
# drawn uniformly over the years the real events span, widened by five years each
# side and never before birth.
NULL_MARGIN_DAYS = 5 * 365


def significance(birth: BirthData, events: list[tuple[str, date]], cands: list[_Candidate],
                 real_best: float, shuffles: int, cfg: SchoolConfig) -> dict:
    """How often random event dates fit this chart as well as the real ones.

    The statistic is the best total over the whole window, so the test pays for
    looking at many candidate times (a best fit is always found somewhere)."""
    birth_day = birth.local_datetime.date()
    days = [d.toordinal() for _, d in events]
    lo = max(birth_day.toordinal() + 1, min(days) - NULL_MARGIN_DAYS)
    hi = max(lo, max(days) + NULL_MARGIN_DAYS)
    seed = zlib.crc32(repr((birth.local_datetime.isoformat(), birth.latitude, birth.longitude,
                            sorted((t, d.isoformat()) for t, d in events))).encode())
    rng = random.Random(seed)
    null = []
    for _ in range(shuffles):
        scored = []
        for etype, _d in events:
            jd = _event_jd(birth, date.fromordinal(rng.randint(lo, hi)), cfg)
            scored.append((etype, jd, _transit_signs_jd(jd, cfg)))
        null.append(_best_total(cands, scored))
    at_least = sum(1 for x in null if x >= real_best)
    p = (1 + at_least) / (shuffles + 1)
    null.sort()
    return {
        "shuffles": shuffles,
        "random_at_least": at_least,
        "p_value": round(p, 4),
        "random_best_median": null[len(null) // 2],
        "random_best_p95": null[min(len(null) - 1, int(0.95 * len(null)))],
        "verdict": "unlikely by chance" if p <= 0.05 else "weak" if p <= 0.2 else "no signal",
        "null_dates": [date.fromordinal(lo).isoformat(), date.fromordinal(hi).isoformat()],
    }


def fit_curve(birth: BirthData, events: list[tuple[str, date]], window_min: float = 30.0,
              step_s: int = 30, cfg: SchoolConfig = DEFAULT_CONFIG, shuffles: int = 200,
              rule_set: str = "classical") -> dict:
    """Total event score at each candidate time in +/- window_min around the recorded
    time, the best fit, and (shuffles > 0) whether random dates fit as well."""
    vargas = required_vargas()
    n = int(window_min * 60 // step_s)
    cands = [_candidate(birth, i * step_s, cfg, vargas, rule_set) for i in range(-n, n + 1)]
    scored = []
    for etype, d in events:
        jd = _event_jd(birth, d, cfg)
        scored.append((etype, jd, _transit_signs_jd(jd, cfg)))
    maxes = [event_max(e, rule_set) for e, _ in events]
    points = []
    verdicts = []
    for c in cands:
        per = [_score(c, e, jd, sg) for e, jd, sg in scored]
        points.append({"offset_s": c.offset_s, "score": sum(per)})
        verdicts.append([verdict(x, m) for x, m in zip(per, maxes)])
    best = max(points, key=lambda p: (p["score"], -abs(p["offset_s"]))) if points else None
    helps = [len({v[j] for v in verdicts}) > 1 for j in range(len(events))]
    return {
        "rule_set": rule_set,
        "points": points,
        "best": dict(best) if best else None,
        "helps_decide": helps,
        "max_score": sum(maxes),
        "significance": (significance(birth, events, cands, best["score"], shuffles, cfg)
                         if events and shuffles > 0 and best else None),
    }


def indicative_periods(birth: BirthData, cfg: SchoolConfig = DEFAULT_CONFIG,
                       max_age_years: float = 90.0, chart: Chart | None = None,
                       rule_set: str = "classical", min_age_years: float = 16.0) -> dict[str, list[dict]]:
    """Antardashas that point to an event, for the event types allowed as indicative
    periods (never death or illness).

    classical: the antardasha lord gives the event by the cited rules and the
    antardasha is good (its lord well placed and dignified, nothing against it).
    modern: both the mahadasha and the antardasha lords are linked to the event.

    Only periods from `min_age_years` (default 16, the user's choice: the texts give no
    age limit) to `max_age_years` are listed; a period running at the lower age is
    clipped to start there."""
    chart = chart or build_chart(birth, cfg, required_vargas())
    periods = vimshottari(chart.grahas["Mo"].longitude, chart.jd_ut, cfg, levels=2)
    limit = chart.jd_ut + max_age_years * 365.25
    first = chart.jd_ut + min_age_years * 365.25
    out: dict[str, list[dict]] = {}
    for rule in event_rules().values():
        if not rule.indicative or rule.check_only:
            continue
        cr = classical_rules()[rule.id] if rule_set == "classical" else None
        rows = []
        for md in periods:
            ml = significator_reasons(chart, cr, md.lord) if cr else links(chart, rule, md.lord)
            if not cr and not ml:
                continue
            for ad in md.children:
                if ad.start_jd > limit or ad.end_jd <= first:
                    continue
                al = significator_reasons(chart, cr, ad.lord) if cr else links(chart, rule, ad.lord)
                if not al:
                    continue
                row = {"mahadasha": md.lord, "antardasha": ad.lord,
                       "start_jd": max(ad.start_jd, first), "end_jd": ad.end_jd,
                       "maha_links": ml, "antar_links": al}
                if cr:
                    q, good, _bad = antardasha_quality(chart, md.lord, ad.lord)
                    if q != "good":
                        continue
                    row["quality_reasons"] = good
                rows.append(row)
        out[rule.id] = rows
    return out

# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Rahul Sathe
"""Rectification helpers: score known life events against a candidate birth time.

For each event (type + date) and a candidate birth time:
- the Vimshottari mahadasha and antardasha running on the event date;
- whether each of those lords is linked to the event's houses, in D1 or in the
  governing varga: it lords one of the houses, occupies one, or is the natural
  karaka;
- whether Jupiter and Saturn both occupy or aspect one of the event's D1 houses
  on that date (double transit);
- score = antardasha lord linked (+1) + mahadasha lord linked (+0.5) + double
  transit (+0.5), maximum 2; strong >= 1.5, partial >= 0.75, else weak.

`fit_curve` sums the scores over a window of candidate times and marks the best
fit; `indicative_periods` lists antardashas whose both lords are linked to an
event, for the four event types that may be shown as indicative periods. Events
marked check_only (death, illness) are scored but never offered as predictions.

These are classical aids for an astrologer, not proofs; the rule files are
drafts pending expert review.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from functools import lru_cache
from pathlib import Path

import yaml

from .chart import Chart, build_chart
from .config import DEFAULT_CONFIG, SchoolConfig
from .constants import GRAHA_DRISHTI, SIGN_LORD
from .dasha import Period, running, vimshottari
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
    hit = []
    for h in rule.d1_houses:
        sign = (natal.lagna.sign + h - 1) % 12
        if (_aspects_or_occupies("Ju", transit_signs["Ju"], sign)
                and _aspects_or_occupies("Sa", transit_signs["Sa"], sign)):
            hit.append(h)
    return hit


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


def verdict(score: float) -> str:
    return "strong" if score >= 1.5 else "partial" if score >= 0.75 else "weak"


def _event_jd(birth: BirthData, d: date, cfg: SchoolConfig) -> float:
    return BirthData(datetime(d.year, d.month, d.day, 12, 0), birth.latitude, birth.longitude,
                     tz_name=birth.tz_name, utc_offset_hours=birth.utc_offset_hours).jd_ut()


@lru_cache(maxsize=4096)
def _transit_signs(lat: float, lon: float, tz_name: str, offset: float | None, d: date,
                   cfg_key: str, cfg: SchoolConfig) -> dict[str, int]:
    c = build_chart(BirthData(datetime(d.year, d.month, d.day, 12, 0), lat, lon,
                              tz_name=tz_name, utc_offset_hours=offset), cfg, [1])
    return {p: c.grahas[p].sign for p in ("Ju", "Sa")}


def check_events(birth: BirthData, events: list[tuple[str, date]],
                 cfg: SchoolConfig = DEFAULT_CONFIG, chart: Chart | None = None) -> list[EventCheck]:
    """Score each (event type, date) for the birth time in `birth`."""
    rules = event_rules()
    chart = chart or build_chart(birth, cfg, required_vargas())
    periods = vimshottari(chart.grahas["Mo"].longitude, chart.jd_ut, cfg, levels=2)
    out = []
    for etype, d in events:
        rule = rules[etype]
        chain = running(periods, _event_jd(birth, d, cfg))
        md = chain[0].lord if chain else None
        ad = chain[1].lord if len(chain) > 1 else None
        ml = links(chart, rule, md) if md else []
        al = links(chart, rule, ad) if ad else []
        ts = _transit_signs(birth.latitude, birth.longitude, birth.tz_name, birth.utc_offset_hours,
                            d, cfg.key(), cfg)
        dt = double_transit(chart, rule, ts)
        score = (1.0 if al else 0.0) + (0.5 if ml else 0.0) + (0.5 if dt else 0.0)
        out.append(EventCheck(etype, rule.name, d.isoformat(), md, ad, ml, al, dt, score,
                              verdict(score), rule.check_only))
    return out


@dataclass
class FitPoint:
    offset_s: int
    score: float
    verdicts: list[str]


def fit_curve(birth: BirthData, events: list[tuple[str, date]], window_min: float = 30.0,
              step_s: int = 30, cfg: SchoolConfig = DEFAULT_CONFIG) -> dict:
    """Total event score at each candidate time in +/- window_min around the recorded time."""
    vargas = required_vargas()
    n = int(window_min * 60 // step_s)
    points: list[FitPoint] = []
    for i in range(-n, n + 1):
        b = birth.shifted(minutes=i * step_s / 60.0)
        checks = check_events(b, events, cfg, build_chart(b, cfg, vargas))
        points.append(FitPoint(i * step_s, sum(c.score for c in checks), [c.verdict for c in checks]))
    best = max(points, key=lambda p: (p.score, -abs(p.offset_s))) if points else None
    helps = []
    for j in range(len(events)):
        helps.append(len({p.verdicts[j] for p in points}) > 1)
    return {
        "points": [{"offset_s": p.offset_s, "score": p.score} for p in points],
        "best": {"offset_s": best.offset_s, "score": best.score} if best else None,
        "helps_decide": helps,
        "max_score": 2.0 * len(events),
    }


def indicative_periods(birth: BirthData, cfg: SchoolConfig = DEFAULT_CONFIG,
                       max_age_years: float = 90.0, chart: Chart | None = None) -> dict[str, list[dict]]:
    """Antardashas whose maha and antar lords are both linked to an event, for the
    event types allowed as indicative periods (never death or illness)."""
    chart = chart or build_chart(birth, cfg, required_vargas())
    periods = vimshottari(chart.grahas["Mo"].longitude, chart.jd_ut, cfg, levels=2)
    limit = chart.jd_ut + max_age_years * 365.25
    out: dict[str, list[dict]] = {}
    for rule in event_rules().values():
        if not rule.indicative or rule.check_only:
            continue
        rows = []
        for md in periods:
            ml = links(chart, rule, md.lord)
            if not ml:
                continue
            for ad in md.children:
                if ad.start_jd > limit or ad.end_jd < chart.jd_ut:
                    continue
                al = links(chart, rule, ad.lord)
                if al:
                    rows.append({"mahadasha": md.lord, "antardasha": ad.lord,
                                 "start_jd": max(ad.start_jd, chart.jd_ut), "end_jd": ad.end_jd,
                                 "maha_links": ml, "antar_links": al})
        out[rule.id] = rows
    return out

# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Rahul Sathe
"""Rule-based readings (M3.4; design doc, Layer 4 #4 and #5, without the network).

    fact sheet  ->  ranked factors  ->  cited sentences  ->  verifier  ->  safety filter

- The fact sheet holds engine facts only (placements, lordships, dignities, aspects,
  yogas, Shadbala, combustion, running dasha, birth-time stability), each with an id.
- Factors for a topic (rules/readings/topics.yaml) are ranked by classical weighting:
  the house lords, occupants, aspects, the karaka, the governing varga, the topic's
  yogas and the running dasha lords. Each says whether it supports or obstructs the
  topic by classical rules, from the facts it cites. A high rank means "important to
  examine for this topic", not "this will happen".
- Each sentence is written from one factor, cites the fact ids it rests on, and
  carries its claims in structured form. The verifier re-derives every claim from
  the chart (not from the fact sheet), checks that each claim is backed by a cited
  fact and that every planet, sign and house the sentence names is among its claims;
  a sentence that fails is dropped and reported.
- The safety filter drops any sentence about death, longevity, accidents, illness or
  pregnancy, and anything about the sex of a child; technical-only topics (health)
  list factors without text. Medical, legal and financial topics carry a disclaimer.
- Factors that depend on house numbering in a varga whose Lagna changes sign within
  `stability_min` minutes of the recorded birth time are marked uncertain.

Interpretive wording is framed as traditional interpretation ("classical texts read
..."), never as a statement about the person.
"""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field
from datetime import date, datetime, time, timedelta, timezone
from functools import lru_cache
from pathlib import Path

import yaml

from .chart import BirthData, Chart, build_chart
from .config import DEFAULT_CONFIG, SchoolConfig
from .constants import (EXALTATION, GRAHA_DRISHTI, GRAHA_NAMES, NATURAL_ENEMIES, NATURAL_FRIENDS,
                        OWN_SIGNS, SIGN_LORD, SIGNS)
from .dasha import running, vimshottari
from .i18n import Join, M, graha, sign as sign_name
from .i18n import ordinal as _ordinal

TOPICS_FILE = Path(__file__).parent / "rules" / "readings" / "topics.yaml"
GRAHAS = ["Su", "Mo", "Ma", "Me", "Ju", "Ve", "Sa", "Ra", "Ke"]
KENDRA_TRIKONA = {1, 4, 5, 7, 9, 10}
DUSTHANA = {6, 8, 12}
COMBUST_ORB = {"Mo": 12.0, "Ma": 17.0, "Me": 14.0, "Ju": 11.0, "Ve": 10.0, "Sa": 15.0}
COMBUST_ORB_RETRO = {"Me": 12.0, "Ve": 8.0}
WEIGHTS = {"lord": 1.0, "dasha_maha": 1.0, "yoga": 0.9, "occupant": 0.8, "dasha_antar": 0.8,
           "karaka": 0.7, "aspect": 0.6, "varga_lord": 0.6, "varga_occupant": 0.5}

SEX_OF_CHILD = M("the sex of a child is never predicted")
NO_HARM = M("no death, illness, accident or pregnancy content in drafts")
BLOCKED = [
    (re.compile(r"\b(son|sons|daughter|daughters|boy|girl|male child|female child|sex of)\b", re.I),
     SEX_OF_CHILD),
    (re.compile(r"\b(death|die|dies|dying|longevity|lifespan|life span|maraka|accident\w*|illness\w*|"
                r"disease\w*|surgery|pregnan\w*|miscarriage|abortion)\b", re.I),
     NO_HARM),
]
# The same filter on the Hindi and Marathi text of each sentence: words beginning with
# these stems (death, longevity, accident, illness, surgery, pregnancy, son, daughter).
_DEVA = "\u0900-\u097F"
BLOCKED_DEVA = [
    (re.compile(rf"(?<![{_DEVA}])(पुत्र|पुत्री|बेटा|बेटे|बेटी|लड़का|लड़की|मुलगा|मुलगे|मुलगी|लिंग)"), SEX_OF_CHILD),
    (re.compile(rf"(?<![{_DEVA}])(मृत्यु|मृत्यू|मौत|मरण|मारक|आयु|आयुष्य|दुर्घटना|अपघात|रोग|बीमार|आजार|व्याधि|"
                rf"शस्त्रक्रिया|गर्भ)"), NO_HARM),
]
DISCLAIMERS = {
    "financial": M("Classical indications for study, not financial advice."),
    "legal": M("Classical indications for study, not legal advice."),
    "medical": M("Technical factors for the astrologer's own judgment; not medical advice. "
                 "No illness is predicted and no text is drafted for this topic."),
}


def ordinal(n: int) -> M:
    return _ordinal(n)


def name(p: str) -> M:
    return graha(p)


def sign_dignity(planet: str, sign: int) -> str:
    """Dignity by sign alone (vargas): exalted, debilitated, own, friend, enemy, neutral."""
    if planet in ("Ra", "Ke"):
        return "node"
    ex = EXALTATION[planet][0]
    if sign == ex:
        return "exalted"
    if sign == (ex + 6) % 12:
        return "debilitated"
    if sign in OWN_SIGNS[planet]:
        return "own"
    lord = SIGN_LORD[sign]
    if lord in NATURAL_FRIENDS[planet]:
        return "friend"
    if lord in NATURAL_ENEMIES[planet]:
        return "enemy"
    return "neutral"


DIGNITY_WORDS = {"exalted": M("exalted"), "moolatrikona": M("in its moolatrikona sign"),
                 "own": M("in its own sign"), "friend": M("in a friend's sign"),
                 "enemy": M("in an enemy's sign"), "debilitated": M("debilitated"), "neutral": "", "node": ""}
# A dignity as one word (facts and reasons): "Venus is friend in D9".
DIGNITY_NAME = {"exalted": M("exalted"), "moolatrikona": M("moolatrikona"), "own": M("own"),
                "friend": M("friend"), "enemy": M("enemy"), "debilitated": M("debilitated"),
                "neutral": M("neutral"), "node": M("node")}
READS = {"supports": 1.0, "obstructs": -1.0, "mixed": 0.0}
# How the workbench names a factor's reading, for every topic.
DIRECTION_LABELS = {"supports": "favours the native", "obstructs": "against the native", "mixed": "mixed"}
DIGNITY_SCORE = {"exalted": 1.0, "moolatrikona": 1.0, "own": 1.0, "friend": 0.5, "neutral": 0.0,
                 "enemy": -0.5, "debilitated": -1.0, "node": 0.0}


# ---------------------------------------------------------------------- topics

@dataclass(frozen=True)
class Topic:
    id: str
    name: str
    group: str
    houses: tuple[int, ...]
    karaka: str
    varga: int | None
    yogas: dict
    source: dict
    status: str = "draft"
    technical_only: bool = False
    disclaimer: str | None = None
    note: str = ""
    theme: str = ""
    house_rules: dict = field(default_factory=dict)  # per-house overrides of the general rules, cited

    def label(self, direction: str) -> str:
        return DIRECTION_LABELS[direction]


@lru_cache(maxsize=1)
def topics() -> dict[str, Topic]:
    out = {}
    for raw in yaml.safe_load(TOPICS_FILE.read_text()):
        raw["houses"] = tuple(raw["houses"])
        t = Topic(**raw)
        out[t.id] = t
    return out


# ------------------------------------------------------------------ fact sheet

@dataclass
class Fact:
    id: str
    kind: str
    data: dict
    text: str


@dataclass
class Factor:
    key: str
    role: str
    subject: str                  # planet code or yoga id
    varga: int
    direction: str                # supports | obstructs | mixed
    weight: float
    score: float
    reasons: list[str]
    facts: list[str]
    uncertain: bool = False


@dataclass
class Sentence:
    text: str
    cites: list[str]
    claims: list[dict]
    factor: str
    uncertain: bool = False


@dataclass
class Reading:
    topic: dict
    facts: list[Fact]
    factors: list[Factor]
    sentences: list[Sentence]
    dropped: list[dict] = field(default_factory=list)
    disclaimers: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    # Current-period scope: the running mahadasha and antardasha, tied to the topic or not.
    periods: list[dict] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


class Sheet:
    """The fact sheet and the chart it was built from."""

    def __init__(self, chart: Chart, birth: BirthData, cfg: SchoolConfig, vargas: list[int]):
        self.chart, self.birth, self.cfg, self.vargas = chart, birth, cfg, vargas
        self.facts: dict[str, Fact] = {}
        from .yogas import Context
        ctx = Context.from_chart(chart)
        self.benefics = set(ctx.benefics)
        self._yoga_results = None
        self._shadbala = None

    def add(self, fid: str, kind: str, data: dict, text: str) -> str:
        if fid not in self.facts:
            self.facts[fid] = Fact(fid, kind, data, text)
        return fid

    # --- chart helpers
    def lagna(self, v: int) -> int:
        return self.chart.lagna.vargas[v]

    def sign(self, p: str, v: int) -> int:
        return self.chart.grahas[p].vargas[v]

    def house(self, p: str, v: int) -> int:
        return (self.sign(p, v) - self.lagna(v)) % 12 + 1

    def lord(self, h: int, v: int) -> str:
        return SIGN_LORD[(self.lagna(v) + h - 1) % 12]

    def dignity(self, p: str, v: int) -> str:
        if v == 1:
            return self.chart.grahas[p].dignity or "neutral"
        return sign_dignity(p, self.sign(p, v))

    # --- facts
    def placement(self, p: str, v: int) -> str:
        s, h = self.sign(p, v), self.house(p, v)
        return self.add(f"place.D{v}.{p}", "placement", {"planet": p, "varga": v, "sign": s, "house": h},
                        M("{p} is in {s}, the {h} house of D{v}.", p=name(p), s=sign_name(s), h=ordinal(h), v=v))

    def dignity_fact(self, p: str, v: int) -> str:
        d = self.dignity(p, v)
        return self.add(f"dignity.D{v}.{p}", "dignity", {"planet": p, "varga": v, "dignity": d},
                        M("{p} is {d} in D{v}.", p=name(p), d=DIGNITY_NAME[d], v=v))

    def lordship(self, h: int, v: int) -> str:
        s = (self.lagna(v) + h - 1) % 12
        lo = SIGN_LORD[s]
        return self.add(f"lord.D{v}.H{h}", "lordship", {"varga": v, "house": h, "sign": s, "lord": lo},
                        M("The {h} house of D{v} is {s}, ruled by {lo}.", h=ordinal(h), v=v, s=sign_name(s),
                          lo=name(lo)))

    def aspect(self, p: str, h: int) -> str:
        return self.add(f"aspect.D1.{p}.H{h}", "aspect", {"planet": p, "house": h, "varga": 1},
                        M("{p} aspects the {h} house (graha drishti).", p=name(p), h=ordinal(h)))

    def strength(self, p: str) -> str | None:
        if p in ("Ra", "Ke"):
            return None
        if self._shadbala is None:
            from .shadbala import REQUIRED_RUPAS, shadbala
            full = build_chart(self.birth, self.cfg, [1, 2, 3, 7, 9, 12, 30])
            self._shadbala = {q: s.rupas / REQUIRED_RUPAS[q] for q, s in shadbala(full, self.birth, self.cfg).items()}
        r = round(self._shadbala[p], 2)
        return self.add(f"shadbala.{p}", "strength", {"planet": p, "ratio": r, "meets": r >= 1.0},
                        M("{p} has {r:.2f} times its required Shadbala.", p=name(p), r=r))

    def combust(self, p: str) -> str | None:
        if p not in COMBUST_ORB:
            return None
        g = self.chart.grahas
        orb = (COMBUST_ORB_RETRO if g[p].retrograde else COMBUST_ORB).get(p, COMBUST_ORB[p])
        sep = abs((g[p].longitude - g["Su"].longitude + 180.0) % 360.0 - 180.0)
        return self.add(f"combust.{p}", "combust", {"planet": p, "combust": sep < orb, "separation": round(sep, 2)},
                        M("{p} is {sep:.1f} deg from the Sun ({state}).", p=name(p), sep=sep,
                          state=M("combust") if sep < orb else M("not combust")))

    def yoga(self, yid: str) -> str | None:
        if self._yoga_results is None:
            from .yogas import find_yogas
            self._yoga_results = {y.id: y for y in find_yogas(self.chart, include_absent=True)}
        y = self._yoga_results.get(yid)
        if y is None or not y.present or y.cancelled:
            return None
        return self.add(f"yoga.{yid}", "yoga", {"yoga": yid, "name": y.name, "present": True},
                        M("{y} yoga is present ({ev}); source: {text}, {section}.", y=y.name,
                          ev=Join("; ", y.evidence), text=str(y.source.get("text")),
                          section=str(y.source.get("section"))))


# ------------------------------------------------------------- planet condition

KENDRA_TRIKONA_WORD = M("kendra or trikona")
DUSTHANA_WORD = M("dusthana")
BENEFIC, MALEFIC = M("natural benefic"), M("natural malefic")


def _condition(sh: Sheet, p: str, v: int = 1, lord_rule: dict | None = None) -> tuple[float, list[str], list[str]]:
    """Net classical condition of a planet as a significator: dignity, house, strength,
    combustion. Returns (net, reasons, fact ids). `lord_rule` (a topic's house rule for
    its lord) replaces the general kendra/trikona and dusthana points where it says so."""
    net, why, facts = 0.0, [], []
    d = sh.dignity(p, v)
    facts += [sh.placement(p, v), sh.dignity_fact(p, v)]
    if DIGNITY_SCORE[d]:
        net += DIGNITY_SCORE[d]
        why.append(M("{d} in D{v}", d=DIGNITY_NAME[d], v=v))
    h = sh.house(p, v)
    place = "kendra_trikona" if h in KENDRA_TRIKONA else "dusthana" if h in DUSTHANA else None
    rule = (lord_rule or {}).get(place) if place else None
    if rule:
        net += READS[rule["reads"]]
        kind = KENDRA_TRIKONA_WORD if place == "kendra_trikona" else DUSTHANA_WORD
        why.append(M("in the {h} house ({kind}; {cite})", h=ordinal(h), kind=kind, cite=M(rule["cite"])))
    elif h in KENDRA_TRIKONA:
        net += 1.0
        why.append(M("in the {h} house ({kind})", h=ordinal(h), kind=KENDRA_TRIKONA_WORD))
    elif h in DUSTHANA:
        net -= 1.0
        why.append(M("in the {h} house ({kind})", h=ordinal(h), kind=DUSTHANA_WORD))
    if v == 1:
        f = sh.strength(p)
        if f:
            facts.append(f)
            meets = sh.facts[f].data["meets"]
            net += 0.5 if meets else -0.5
            why.append(M("meets its required Shadbala") if meets else M("below its required Shadbala"))
        f = sh.combust(p)
        if f and sh.facts[f].data["combust"]:
            facts.append(f)
            net -= 1.0
            why.append(M("combust"))
    return net, why, facts


def _house_rule(sh: Sheet, hr: dict, kind: str, p: str) -> dict | None:
    """A topic's rule for a planet occupying or aspecting one of its houses: by planet,
    else by natural benefic or malefic. None: the general rule applies."""
    r = hr.get(kind) or {}
    return r.get(p) or r.get("benefic" if p in sh.benefics else "malefic")


def _occupant(sh: Sheet, hr: dict, p: str, v: int) -> tuple[float, list[str]]:
    """General rule: a natural benefic in the house supports it, a malefic obstructs it,
    adjusted by dignity. A topic's house rule, where it has one, gives the reading instead."""
    rule = _house_rule(sh, hr, "occupant", p)
    if rule:
        return READS[rule["reads"]], [M(rule["cite"])]
    return (1.0 if p in sh.benefics else -1.0) + DIGNITY_SCORE[sh.dignity(p, v)], []


def _direction(net: float) -> str:
    return "supports" if net > 0.25 else "obstructs" if net < -0.25 else "mixed"


def _factor(key, role, subject, v, net, why, facts, uncertain) -> Factor:
    conf = min(1.0, abs(net) / 2.0)
    w = WEIGHTS[role]
    return Factor(key, role, subject, v, _direction(net), w, round(w * (0.6 + 0.4 * conf), 3), why,
                  list(dict.fromkeys(facts)), uncertain)


# --------------------------------------------------------------------- ranking

def _stability(sh: Sheet, window_min: float) -> dict[int, float | None]:
    """Minutes from the recorded time to the nearest Lagna sign change in each varga
    (None: none within the window)."""
    from .boundaries import boundary_map
    changes, _ = boundary_map(sh.birth, window_min=window_min, step_s=10.0, cfg=sh.cfg,
                              vargas=sh.vargas, track_moon=False, track_special=False, track_pada=False)
    out: dict[int, float | None] = {v: None for v in sh.vargas}
    for c in changes:
        m = re.fullmatch(r"D(\d+)\.lagna", c.key)
        if m and int(m.group(1)) in out:
            v = int(m.group(1))
            d = abs(c.offset_min)
            out[v] = d if out[v] is None else min(out[v], d)
    for v, d in out.items():
        sh.add(f"stability.D{v}", "stability", {"varga": v, "window_min": window_min,
                                                "lagna_change_min": None if d is None else round(d, 1)},
               M("The D{v} Lagna keeps its sign within ±{w:g} min.", v=v, w=window_min) if d is None else
               M("The D{v} Lagna changes sign {d:.1f} min from the recorded time within ±{w:g} min.",
                 v=v, d=d, w=window_min))
    return out


def rank(sh: Sheet, topic: Topic, at_jd: float | None, unstable: set[int]) -> list[Factor]:
    out: list[Factor] = []
    u1 = 1 in unstable
    for h in topic.houses:
        hr = topic.house_rules.get(h, {})
        lo = sh.lord(h, 1)
        net, why, facts = _condition(sh, lo, 1, hr.get("lord"))
        out.append(_factor(f"lord.D1.H{h}", "lord", lo, 1, net, [M("lord of the {h}", h=ordinal(h))] + why,
                           [sh.lordship(h, 1)] + facts, u1))
        for p in GRAHAS:
            nature = BENEFIC if p in sh.benefics else MALEFIC
            if sh.house(p, 1) == h:
                net, why = _occupant(sh, hr, p, 1)
                out.append(_factor(f"occupant.D1.H{h}.{p}", "occupant", p, 1, net,
                                   [M("in the {h}", h=ordinal(h)), nature] + why,
                                   [sh.placement(p, 1), sh.dignity_fact(p, 1)], u1))
            elif p in GRAHA_DRISHTI and (h - sh.house(p, 1)) % 12 + 1 in GRAHA_DRISHTI[p]:
                rule = _house_rule(sh, hr, "aspect", p)
                net = READS[rule["reads"]] if rule else (1.0 if p in sh.benefics else -1.0)
                out.append(_factor(f"aspect.D1.H{h}.{p}", "aspect", p, 1, net,
                                   [M("aspects the {h}", h=ordinal(h)), nature] + ([M(rule["cite"])] if rule else []),
                                   [sh.aspect(p, h), sh.placement(p, 1)], u1))
        v = topic.varga
        if v:
            lo_v = sh.lord(h, v)
            net, why, facts = _condition(sh, lo_v, v, hr.get("lord"))
            out.append(_factor(f"lord.D{v}.H{h}", "varga_lord", lo_v, v, net,
                               [M("lord of the {h} in D{v}", h=ordinal(h), v=v)] + why, [sh.lordship(h, v)] + facts,
                               v in unstable))
            for p in GRAHAS:
                if sh.house(p, v) == h:
                    net, why = _occupant(sh, hr, p, v)
                    out.append(_factor(f"occupant.D{v}.H{h}.{p}", "varga_occupant", p, v, net,
                                       [M("in the {h} of D{v}", h=ordinal(h), v=v),
                                        BENEFIC if p in sh.benefics else MALEFIC] + why,
                                       [sh.placement(p, v), sh.dignity_fact(p, v)], v in unstable))
    k = topic.karaka
    net, why, facts = _condition(sh, k)
    out.append(_factor(f"karaka.{k}", "karaka", k, 1, net, [M("natural karaka of the topic")] + why, facts, u1))
    for direction, ids in (("supports", topic.yogas.get("supports", [])), ("obstructs", topic.yogas.get("obstructs", []))):
        for yid in ids:
            f = sh.yoga(yid)
            if f:
                out.append(_factor(f"yoga.{yid}", "yoga", yid, 1, 2.0 if direction == "supports" else -2.0,
                                   [sh.facts[f].data["name"]], [f], u1))
    if at_jd is not None:
        periods = running(vimshottari(sh.chart.grahas["Mo"].longitude, sh.chart.jd_ut, sh.cfg, levels=2), at_jd)
        for per, role in zip(periods[:2], ("dasha_maha", "dasha_antar")):
            links = _links(sh, topic, per.lord)
            if not links:
                continue
            fid = sh.add(f"dasha.L{per.level}", "dasha",
                         {"system": "vimshottari", "level": per.level, "lord": per.lord,
                          "start": _date(per.start_jd), "end": _date(per.end_jd), "at": _date(at_jd)},
                         M("The Vimshottari {level} of {p} runs {a} to {b}.", level=_level(per.level),
                           p=name(per.lord), a=_date(per.start_jd), b=_date(per.end_jd)))
            net, why, facts = _condition(sh, per.lord)
            out.append(_factor(f"{role}.{per.lord}", role, per.lord, 1, net,
                               [M("running mahadasha lord") if per.level == 1 else M("running antardasha lord")]
                               + [x for x, _ in links] + why,
                               [fid] + [f for _, f in links] + facts, u1))
    out.sort(key=lambda f: (-f.score, f.key))
    return out


def _links(sh: Sheet, topic: Topic, p: str) -> list[tuple[str, str]]:
    """How a dasha lord is tied to the topic: lordship, occupancy, karaka (D1 and the varga)."""
    out = []
    for v in [1] + ([topic.varga] if topic.varga else []):
        for h in topic.houses:
            if sh.lord(h, v) == p:
                out.append((M("lord of the {h} in D{v}", h=ordinal(h), v=v), sh.lordship(h, v)))
            if sh.house(p, v) == h:
                out.append((M("in the {h} in D{v}", h=ordinal(h), v=v), sh.placement(p, v)))
    if p == topic.karaka:
        out.append((M("natural karaka"), sh.placement(p, 1)))
    return out


def _level(level: int) -> M:
    return M("mahadasha") if level == 1 else M("antardasha")


def _date(jd: float) -> str:
    from .timeutil import jd_to_datetime
    return jd_to_datetime(jd).date().isoformat()


# ------------------------------------------------------------------- sentences

def _theme(topic: Topic) -> M:
    return M(topic.theme or topic.name[0].lower() + topic.name[1:])


def _verdict(direction: str, what: M, topic: Topic) -> M:
    t = _theme(topic)
    if direction == "supports":
        return M("classical texts read {what} as favouring the native in matters of {t}", what=what, t=t)
    if direction == "obstructs":
        return M("classical texts read {what} as against the native in matters of {t}", what=what, t=t)
    return M("classical texts give {what} mixed results for the native in matters of {t}", what=what, t=t)


def _place_phrase(sh: Sheet, p: str, v: int, in_v: bool = False) -> tuple[M, list[dict]]:
    s, h, d = sh.sign(p, v), sh.house(p, v), sh.dignity(p, v)
    dw = DIGNITY_WORDS[d]
    where = (M("in the {h} house of the D{v} chart in {s}", h=ordinal(h), v=v, s=sign_name(s)) if in_v
             else M("in the {h} house in {s}", h=ordinal(h), s=sign_name(s)))
    if dw:
        where = M("{where}, {dignity}", where=where, dignity=dw)
    claims = [{"kind": "placement", "planet": p, "varga": v, "sign": s, "house": h},
              {"kind": "dignity", "planet": p, "varga": v, "dignity": d}]
    return where, claims


def write(sh: Sheet, topic: Topic, f: Factor) -> Sentence:
    p, v = f.subject, f.varga
    in_v = v != 1
    claims: list[dict] = [{"kind": "direction", "factor": f.key, "direction": f.direction}]
    if f.role in ("lord", "varga_lord"):
        h = int(f.key.split(".H")[1])
        where, c = _place_phrase(sh, p, v)
        claims += [{"kind": "lordship", "varga": v, "house": h, "lord": p}] + c
        extra = []
        for fid in f.facts:
            fa = sh.facts[fid]
            if fa.kind == "strength":
                extra.append(M("meets its required Shadbala") if fa.data["meets"]
                             else M("is below its required Shadbala"))
                claims.append({"kind": "strength", "planet": p, "meets": fa.data["meets"]})
            if fa.kind == "combust" and fa.data["combust"]:
                extra.append(M("is combust"))
                claims.append({"kind": "combust", "planet": p, "combust": True})
        head = (M("The lord of the {h} house of the D{v} chart, {p}, is {where}", h=ordinal(h), v=v, p=name(p),
                  where=where) if in_v else
                M("The lord of the {h} house, {p}, is {where}", h=ordinal(h), p=name(p), where=where))
        if extra:
            head = M("{head}, and {more}", head=head, more=Join(M(" and "), extra))
        text = M("{head}; {verdict}.", head=head, verdict=_verdict(f.direction, M("a house lord placed so"), topic))
    elif f.role in ("occupant", "varga_occupant"):
        where, c = _place_phrase(sh, p, v, in_v)
        claims += c
        kind = M("a natural benefic") if p in sh.benefics else M("a natural malefic")
        text = M("{p}, {kind}, is {where}; {verdict}.", p=name(p), kind=kind, where=where,
                 verdict=_verdict(f.direction, M("such an occupant of the house"), topic))
    elif f.role == "aspect":
        h = int(f.key.split(".H")[1].split(".")[0])
        claims.append({"kind": "aspect", "planet": p, "house": h})
        kind = M("a natural benefic") if p in sh.benefics else M("a natural malefic")
        text = M("{p}, {kind}, aspects the {h} house; {verdict}.", p=name(p), kind=kind, h=ordinal(h),
                 verdict=_verdict(f.direction, M("its aspect on the house"), topic))
    elif f.role == "karaka":
        where, c = _place_phrase(sh, p, 1)
        claims += c
        text = M("{p}, the natural karaka for {t}, is {where}; {verdict}.", p=name(p), t=_theme(topic),
                 where=where, verdict=_verdict(f.direction, M("the karaka placed so"), topic))
    elif f.role == "yoga":
        yname = sh.facts[f.facts[0]].data["name"]
        claims.append({"kind": "yoga", "yoga": p, "present": True})
        label = yname if "yoga" in yname.lower() else M("{y} yoga", y=yname)
        text = M("{label} is present; {verdict}.", label=label, verdict=_verdict(f.direction, M("this yoga"), topic))
    else:  # dasha
        dfa = next(sh.facts[x] for x in f.facts if sh.facts[x].kind == "dasha")
        d = dfa.data
        claims.append({"kind": "dasha", "level": d["level"], "lord": p, "start": d["start"], "end": d["end"],
                       "at": d["at"]})
        level = _level(d["level"])
        links = [label for label, _ in _links(sh, topic, p)]
        for fid in f.facts:
            fa = sh.facts[fid]
            if fa.kind == "lordship" and fa.data["lord"] == p:
                claims.append({"kind": "lordship", "varga": fa.data["varga"], "house": fa.data["house"], "lord": p})
            if fa.kind == "placement" and fa.data["planet"] == p:
                claims.append({"kind": "placement", **{k: fa.data[k] for k in ("planet", "varga", "sign", "house")}})
        how = {"supports": M("favouring the native by the lord's condition"),
               "obstructs": M("against the native by the lord's condition"),
               "mixed": M("with mixed results for the native")}[f.direction]
        text = M("The Vimshottari {level} of {p} runs from {a} to {b}, and {p} is tied to the topic ({links}); "
                 "classical texts associate the period of a linked lord with matters of {t} coming forward, {how}.",
                 level=level, p=name(p), a=d["start"], b=d["end"], links=Join("; ", links), t=_theme(topic), how=how)
    return Sentence(text, list(f.facts), claims, f.key, f.uncertain)


# -------------------------------------------------------------------- verifier

_HOUSE_RE = re.compile(r"\b(\d{1,2})(?:st|nd|rd|th) house\b")
_ORD_RE = re.compile(r"\b(\d{1,2})(?:st|nd|rd|th)\b")


def recheck(chart: Chart, claim: dict, at_jd: float | None, cfg: SchoolConfig, birth: BirthData,
            topic: Topic | None = None, factors: dict | None = None) -> bool:
    """Re-derive one claim from the chart, independently of the fact sheet."""
    k = claim["kind"]
    g = chart.grahas
    if k == "placement":
        v, p = claim["varga"], claim["planet"]
        s = g[p].vargas[v]
        return s == claim["sign"] and (s - chart.lagna.vargas[v]) % 12 + 1 == claim["house"]
    if k == "lordship":
        v = claim["varga"]
        return SIGN_LORD[(chart.lagna.vargas[v] + claim["house"] - 1) % 12] == claim["lord"]
    if k == "dignity":
        p, v = claim["planet"], claim["varga"]
        d = (g[p].dignity or "neutral") if v == 1 else sign_dignity(p, g[p].vargas[v])
        return d == claim["dignity"]
    if k == "aspect":
        p = claim["planet"]
        return (claim["house"] - g[p].house) % 12 + 1 in GRAHA_DRISHTI.get(p, [])
    if k == "combust":
        p = claim["planet"]
        orb = (COMBUST_ORB_RETRO if g[p].retrograde else COMBUST_ORB).get(p, COMBUST_ORB.get(p, 0.0))
        sep = abs((g[p].longitude - g["Su"].longitude + 180.0) % 360.0 - 180.0)
        return (sep < orb) == claim["combust"]
    if k == "strength":
        from .shadbala import REQUIRED_RUPAS, shadbala
        full = build_chart(birth, cfg, [1, 2, 3, 7, 9, 12, 30])
        s = shadbala(full, birth, cfg)[claim["planet"]]
        return (round(s.rupas / REQUIRED_RUPAS[claim["planet"]], 2) >= 1.0) == claim["meets"]
    if k == "yoga":
        from .yogas import find_yogas
        return any(y.id == claim["yoga"] and y.present and not y.cancelled for y in find_yogas(chart))
    if k == "dasha":
        if at_jd is None:
            return False
        per = running(vimshottari(g["Mo"].longitude, chart.jd_ut, cfg, levels=2), at_jd)
        return any(q.level == claim["level"] and q.lord == claim["lord"] and _date(q.start_jd) == claim["start"]
                   and _date(q.end_jd) == claim["end"] for q in per)
    if k == "direction":
        f = (factors or {}).get(claim["factor"])
        return f is not None and f.direction == claim["direction"]
    return False


def _backed(claim: dict, facts: list[Fact]) -> bool:
    if claim["kind"] == "direction":
        return True
    body = {k: v for k, v in claim.items() if k != "kind"}
    kinds = {"placement": "placement", "lordship": "lordship", "dignity": "dignity", "aspect": "aspect",
             "combust": "combust", "strength": "strength", "yoga": "yoga", "dasha": "dasha"}
    for f in facts:
        if f.kind == kinds[claim["kind"]] and all(f.data.get(k) == v for k, v in body.items()):
            return True
    return False


def verify(s: Sentence, sh: Sheet, at_jd: float | None, topic: Topic, factors: dict) -> str | None:
    """None if the sentence is grounded, else why it is not."""
    if not s.cites:
        return "cites no fact"
    missing = [c for c in s.cites if c not in sh.facts]
    if missing:
        return f"cites unknown facts {missing}"
    cited = [sh.facts[c] for c in s.cites]
    for c in s.claims:
        if not _backed(c, cited):
            return f"claim not backed by a cited fact: {c}"
        if not recheck(sh.chart, c, at_jd, sh.cfg, sh.birth, topic, factors):
            return f"claim not true of the chart: {c}"
    planets = {c["planet"] for c in s.claims if "planet" in c} | {c["lord"] for c in s.claims if "lord" in c}
    for p in GRAHAS:
        if re.search(rf"\b{name(p)}\b", s.text) and p not in planets:
            return f"names {name(p)} without a claim"
    signs = {c["sign"] for c in s.claims if "sign" in c}
    for i, sname in enumerate(SIGNS):
        if re.search(rf"\b{sname}\b", s.text) and i not in signs:
            return f"names {sname} without a claim"
    houses = {c["house"] for c in s.claims if "house" in c} | set(topic.houses)
    for m in _HOUSE_RE.finditer(s.text):
        if int(m.group(1)) not in houses:
            return f"names the {m.group(0)} without a claim"
    return None


def safety(text: str) -> M | None:
    for rx, why in BLOCKED:
        if rx.search(text):
            return why
    if isinstance(text, M):                    # the same sentence in Hindi and Marathi
        for lang in ("hi", "mr"):
            local = text.render(lang)
            for rx, why in BLOCKED_DEVA:
                if rx.search(local):
                    return why
    return None


# ------------------------------------------------------------------------- main

def reading(birth: BirthData, topic_id: str, at: date | datetime | None = None,
            cfg: SchoolConfig = DEFAULT_CONFIG, stability_min: float = 5.0, limit: int = 12) -> Reading:
    """The ranked factors and a cited, verified, filtered draft for one topic.
    `at`: a date for the current-period scope (the running Vimshottari periods)."""
    t = topics().get(topic_id)
    if t is None:
        raise ValueError(f"Unknown topic {topic_id!r}")
    vargas = [1] + ([t.varga] if t.varga else [])
    chart = build_chart(birth, cfg, vargas)
    sh = Sheet(chart, birth, cfg, vargas)
    for v in vargas:
        sh.add(f"lagna.D{v}", "lagna", {"varga": v, "sign": sh.lagna(v)},
               M("The D{v} Lagna is {s}.", v=v, s=sign_name(sh.lagna(v))))
    at_jd = None
    if at is not None:
        from .timeutil import datetime_to_jd
        if isinstance(at, datetime):
            moment = at if at.tzinfo else at.replace(tzinfo=timezone.utc)
        else:
            moment = datetime.combine(at, time(12), tzinfo=timezone.utc)
        at_jd = datetime_to_jd(moment)
    stab = _stability(sh, stability_min) if stability_min > 0 else {v: None for v in vargas}
    unstable = {v for v, d in stab.items() if d is not None}
    factors = rank(sh, t, at_jd, unstable)[:limit]
    by_key = {f.key: f for f in factors}

    sentences, dropped = [], []
    if t.technical_only:
        dropped.append({"text": None, "reason": M("technical topic: factors only, no drafted text")})
    else:
        for f in factors:
            s = write(sh, t, f)
            why = verify(s, sh, at_jd, t, by_key)
            if why:
                dropped.append({"text": s.text, "reason": M("verifier: {why}", why=why)})
                continue
            why = safety(s.text)
            if why:
                dropped.append({"text": s.text, "reason": M("safety filter: {why}", why=why)})
                continue
            sentences.append(s)

    periods = []
    if at_jd is not None:
        for per in running(vimshottari(chart.grahas["Mo"].longitude, chart.jd_ut, cfg, levels=2), at_jd)[:2]:
            key = f"{'dasha_maha' if per.level == 1 else 'dasha_antar'}.{per.lord}"
            periods.append({"level": per.level, "lord": per.lord, "start": _date(per.start_jd),
                            "end": _date(per.end_jd), "tied": [label for label, _ in _links(sh, t, per.lord)],
                            "factor": key if key in by_key else None})

    notes = []
    if t.note:
        notes.append(M(t.note))
    for v, d in stab.items():
        if d is not None:
            notes.append(M("The D{v} Lagna changes sign {d:.1f} min from the recorded birth time: factors that "
                           "count houses in D{v} are marked uncertain.", v=v, d=d))
    notes.append(M("A high rank means important to examine for this topic, not that something will happen."))
    used = {fid for f in factors for fid in f.facts} | {fid for fid in sh.facts if fid.startswith(("lagna.", "stability."))}
    return Reading(
        topic={"id": t.id, "name": t.name, "group": t.group, "houses": list(t.houses), "karaka": t.karaka,
               "varga": t.varga, "source": t.source, "status": t.status, "theme": _theme(t),
               "labels": {d: t.label(d) for d in READS}},
        facts=[f for fid, f in sh.facts.items() if fid in used],
        factors=factors, sentences=sentences, dropped=dropped,
        disclaimers=[DISCLAIMERS[t.disclaimer]] if t.disclaimer else [], notes=notes, periods=periods)


def utc_date_of(birth: BirthData, d: date) -> datetime:
    """Local noon of a date at the birth place, as UTC."""
    off = (birth.local_datetime - birth.utc().replace(tzinfo=None)).total_seconds() / 3600
    return (datetime.combine(d, time(12)) - timedelta(hours=off)).replace(tzinfo=timezone.utc)

# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Rahul Sathe
"""Declarative yoga rule engine.

Rules live in YAML files under `rules/yogas/`. Each rule has an id, name, group,
source citation, review status and a `when` condition built from the predicates
below; there is no arbitrary code in rule files. Evaluating a rule returns
whether it is present and the chart factors that made it so.

Condition syntax (YAML):
    all: [cond, ...]      any: [cond, ...]      not: cond
    <predicate>: {args}

Points are referred to as planet codes (Su..Ke), "La" for the Lagna, or
"lord:N" for the lord of house N (whole-sign, from the Lagna).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Callable

import yaml

from .chart import Chart
from .constants import (
    EXALTATION, GRAHA_DRISHTI, MOOLATRIKONA, NATURAL_FRIENDS, OWN_SIGNS, SIGN_LORD, SIGNS, modality,
)

RULES_DIR = Path(__file__).parent / "rules" / "yogas"
GRAHAS7 = ["Su", "Mo", "Ma", "Me", "Ju", "Ve", "Sa"]
GRAHAS9 = GRAHAS7 + ["Ra", "Ke"]
KENDRAS = [1, 4, 7, 10]
TRIKONAS = [1, 5, 9]
DUSTHANAS = [6, 8, 12]
ORD = {1: "1st", 2: "2nd", 3: "3rd"}


def ordinal(n: int) -> str:
    return ORD.get(n, f"{n}th")


# --------------------------------------------------------------------- context

@dataclass
class Context:
    lagna: int                         # sign 0..11
    signs: dict[str, int]              # graha -> sign
    degrees: dict[str, float]          # graha -> longitude
    moon_benefic: bool = True
    mercury_benefic: bool = True

    @classmethod
    def from_chart(cls, chart: Chart) -> "Context":
        signs = {k: p.sign for k, p in chart.grahas.items()}
        degs = {k: p.longitude for k, p in chart.grahas.items()}
        arc = abs((degs["Mo"] - degs["Su"] + 180) % 360 - 180)
        moon_benefic = arc >= 90.0              # Shukla to Krishna Ashtami (JHora's rule)
        # Same rule as Shadbala (majority of natural benefics vs malefics with Mercury).
        from .shadbala import mercury_is_malefic
        return cls(chart.lagna.sign, signs, degs, moon_benefic,
                   not mercury_is_malefic(signs, moon_benefic))

    @classmethod
    def from_signs(cls, lagna: int, signs: dict[str, int], **kw) -> "Context":
        """Build a context from signs only (for tests); degrees at 15 deg of each sign."""
        full = dict(signs)
        if "Ra" in full and "Ke" not in full:
            full["Ke"] = (full["Ra"] + 6) % 12
        return cls(lagna, full, {k: s * 30 + 15.0 for k, s in full.items()}, **kw)

    # --- helpers
    def sign_of(self, point: str) -> int:
        if point == "La":
            return self.lagna
        if point.startswith("lord:"):
            return self.signs[self.lord(int(point[5:]))]
        return self.signs[point]

    def lord(self, house: int) -> str:
        return SIGN_LORD[(self.lagna + house - 1) % 12]

    def house(self, planet: str, ref: str = "La") -> int:
        return (self.sign_of(planet) - self.sign_of(ref)) % 12 + 1

    @property
    def benefics(self) -> list[str]:
        out = ["Ju", "Ve"]
        if self.mercury_benefic:
            out.append("Me")
        if self.moon_benefic:
            out.append("Mo")
        return out

    @property
    def malefics(self) -> list[str]:
        return [p for p in GRAHAS9 if p not in self.benefics]

    @staticmethod
    def label(spec, exclude=()) -> str:
        """Readable name of a planet group, for evidence strings."""
        if isinstance(spec, list):
            return "/".join(spec)
        name = {"grahas7": "planets", "grahas9": "planets or nodes", "benefics": "benefics",
                "malefics": "malefics", "malefics7": "malefics",
                "benefics_no_moon": "benefics other than the Moon"}.get(spec, spec)
        return f"{name} other than {'/'.join(exclude)}" if exclude else name

    def group(self, spec) -> list[str]:
        if isinstance(spec, list):
            return list(spec)
        return {"grahas7": GRAHAS7, "grahas9": GRAHAS9, "benefics": self.benefics,
                "malefics": self.malefics,
                "malefics7": [p for p in self.malefics if p in GRAHAS7],
                "benefics_no_moon": [p for p in self.benefics if p != "Mo"]}[spec]

    def dignity(self, planet: str) -> str:
        if planet in ("Ra", "Ke"):
            return "node"
        sign = self.signs[planet]
        deg = self.degrees[planet] % 30
        ex_sign, _ = EXALTATION[planet]
        if sign == ex_sign:
            return "exalted"
        if sign == (ex_sign + 6) % 12:
            return "debilitated"
        mt_sign, a, b = MOOLATRIKONA[planet]
        if sign == mt_sign and a <= deg < b:
            return "moolatrikona"
        if sign in OWN_SIGNS[planet]:
            return "own"
        return "other"

    def aspects(self, a: str, b: str) -> bool:
        """Graha drishti of planet a on the sign of point b (whole-sign)."""
        if a not in GRAHA_DRISHTI:
            return False
        h = (self.sign_of(b) - self.signs[a]) % 12 + 1
        return h in GRAHA_DRISHTI[a]

    def name(self, point: str) -> str:
        if point == "La":
            return "Lagna"
        if point.startswith("lord:"):
            return f"{ordinal(int(point[5:]))} lord ({self.lord(int(point[5:]))})"
        return point


def _resolve(ctx: Context, point: str) -> str:
    return ctx.lord(int(point[5:])) if point.startswith("lord:") else point


# ------------------------------------------------------------------ predicates

Result = tuple[bool, list[str]]
PREDICATES: dict[str, Callable[[Context, dict], Result]] = {}


def predicate(fn: Callable[[Context, dict], Result]) -> Callable[[Context, dict], Result]:
    PREDICATES[fn.__name__] = fn
    return fn


@predicate
def dignity(ctx: Context, a: dict) -> Result:
    """Dignity in: exalted, moolatrikona, own, debilitated, or "friend" (sign of a natural friend)."""
    p = _resolve(ctx, a["planet"])
    d = ctx.dignity(p)
    if d == "other" and p in NATURAL_FRIENDS and SIGN_LORD[ctx.signs[p]] in NATURAL_FRIENDS[p]:
        d = "friend"
    return d in a["in"], [f"{ctx.name(a['planet'])} {d} in {SIGNS[ctx.signs[p]]}"]


@predicate
def in_house(ctx: Context, a: dict) -> Result:
    """Point (or every point in `planets`) in one of `houses` counted from `from`."""
    ref = a.get("from", "La")
    pts = a.get("planets", [a.get("planet")])
    ev, ok = [], True
    for pt in pts:
        h = ctx.house(_resolve(ctx, pt), ref)
        ok &= h in a["houses"]
        ev.append(f"{ctx.name(pt)} in {ordinal(h)} from {ctx.name(ref)}")
    return ok, ev


@predicate
def occupants(ctx: Context, a: dict) -> Result:
    """Count planets of a group in given houses from a reference.

    mode: "any" (at least one), "none", "all" (every planet of the group is there),
    or min/max counts.
    """
    ref = a.get("from", "La")
    grp = [p for p in ctx.group(a.get("of", "grahas7")) if p not in a.get("exclude", [])]
    if ref in grp:
        grp.remove(ref)
    there = [p for p in grp if ctx.house(p, ref) in a["houses"]]
    mode = a.get("mode", "any")
    if mode == "any":
        ok = bool(there)
    elif mode == "none":
        ok = not there
    elif mode == "all":
        ok = len(there) == len(grp)
    else:
        raise ValueError(mode)
    if "min" in a:
        ok = ok and len(there) >= a["min"]
    hs = "/".join(ordinal(h) for h in a["houses"])
    desc = ", ".join(there) if there else "none"
    who = ctx.label(a.get("of", "grahas7"), a.get("exclude", ()))
    return ok, [f"{who} in the {hs} from {ctx.name(ref)}: {desc}"]


@predicate
def conjunct(ctx: Context, a: dict) -> Result:
    pts = [_resolve(ctx, p) for p in a["planets"]]
    s = {ctx.signs[p] for p in pts}
    return len(s) == 1, [f"{' + '.join(a['planets'])} together in {SIGNS[ctx.signs[pts[0]]]}"
                         if len(s) == 1 else f"{' and '.join(a['planets'])} not conjunct"]


def _relations(ctx: Context, x: str, y: str) -> list[str]:
    out = []
    if ctx.signs[x] == ctx.signs[y]:
        out.append("conjunction")
    if ctx.aspects(x, y) and ctx.aspects(y, x):
        out.append("mutual_aspect")
    elif ctx.aspects(x, y) or ctx.aspects(y, x):
        out.append("aspect")
    if SIGN_LORD[ctx.signs[x]] == y and SIGN_LORD[ctx.signs[y]] == x:
        out.append("exchange")
    return out


@predicate
def related(ctx: Context, a: dict) -> Result:
    """Sambandha between two points: conjunction, mutual aspect, exchange (or aspect)."""
    x, y = _resolve(ctx, a["a"]), _resolve(ctx, a["b"])
    types = a.get("types", ["conjunction", "mutual_aspect", "exchange"])
    if x == y:
        return a.get("same_planet_counts", True), [f"{ctx.name(a['a'])} is also {ctx.name(a['b'])}"]
    found = [r for r in _relations(ctx, x, y) if r in types]
    return bool(found), [f"{ctx.name(a['a'])} and {ctx.name(a['b'])}: {', '.join(found) or 'no relation'}"]


@predicate
def lords_related(ctx: Context, a: dict) -> Result:
    """Any lord of `houses_a` related to any lord of `houses_b` (distinct houses)."""
    types = a.get("types", ["conjunction", "mutual_aspect", "exchange"])
    ev = []
    for ha in a["houses_a"]:
        for hb in a["houses_b"]:
            if ha == hb:
                continue
            x, y = ctx.lord(ha), ctx.lord(hb)
            if x == y:
                if a.get("same_planet_counts", False):
                    ev.append(f"{x} lords both the {ordinal(ha)} and {ordinal(hb)}")
                continue
            found = [r for r in _relations(ctx, x, y) if r in types]
            if found:
                ev.append(f"{ordinal(ha)} lord {x} and {ordinal(hb)} lord {y}: {', '.join(found)}")
    return bool(ev), sorted(set(ev))


@predicate
def lord_in_house(ctx: Context, a: dict) -> Result:
    lord = ctx.lord(a["house"])
    h = ctx.house(lord, a.get("from", "La"))
    return h in a["houses"], [f"{ordinal(a['house'])} lord {lord} in {ordinal(h)}"]


@predicate
def same_lord_owns(ctx: Context, a: dict) -> Result:
    """One planet lords a house from `houses_a` and another from `houses_b` (yogakaraka)."""
    ev = []
    for p in GRAHAS7:
        owned = [h for h in range(1, 13) if ctx.lord(h) == p]
        ka = [h for h in owned if h in a["houses_a"] and h != 1]
        kb = [h for h in owned if h in a["houses_b"] and h != 1]
        if ka and kb:
            ev.append(f"{p} lords the {'/'.join(map(ordinal, ka))} and {'/'.join(map(ordinal, kb))}")
    return bool(ev), ev


@predicate
def parivartana(ctx: Context, a: dict) -> Result:
    """Sign exchange between two house lords, classified Maha / Khala / Dainya."""
    ev = []
    dusthana = {6, 8, 12}
    for h1 in range(1, 13):
        for h2 in range(h1 + 1, 13):
            x, y = ctx.lord(h1), ctx.lord(h2)
            if x == y:
                continue
            if ctx.house(x) == h2 and ctx.house(y) == h1:
                pair = {h1, h2}
                kind = "dainya" if pair & dusthana else ("khala" if 3 in pair else "maha")
                if kind == a["kind"]:
                    ev.append(f"{ordinal(h1)} lord {x} and {ordinal(h2)} lord {y} exchange signs")
    return bool(ev), ev


@predicate
def sign_count(ctx: Context, a: dict) -> Result:
    grp = ctx.group(a.get("of", "grahas7"))
    n = len({ctx.signs[p] for p in grp})
    return n == a["count"], [f"the seven planets occupy {n} signs" if a.get("of", "grahas7") == "grahas7"
                             else f"{ctx.label(a['of'])} occupy {n} signs"]


@predicate
def all_in_modality(ctx: Context, a: dict) -> Result:
    grp = ctx.group(a.get("of", "grahas7"))
    want = {"movable": 0, "fixed": 1, "dual": 2}[a["modality"]]
    ok = all(modality(ctx.signs[p]) == want for p in grp)
    return ok, [f"all seven planets in {a['modality']} signs" if ok else "planets in mixed modalities"]


@predicate
def houses_exactly(ctx: Context, a: dict) -> Result:
    """The group occupies exactly these houses (every listed house has someone, nothing elsewhere)."""
    grp = ctx.group(a.get("of", "grahas7"))
    hs = {ctx.house(p) for p in grp}
    want = set(a["houses"])
    ok = hs == want if a.get("all_occupied", True) else hs <= want
    return ok, [f"the seven planets in houses {', '.join(map(str, sorted(hs)))}"]


@predicate
def distinct_houses(ctx: Context, a: dict) -> Result:
    """Every planet of the group is in one of `houses`, and they occupy `count` distinct houses."""
    grp = ctx.group(a["of"])
    hs = [ctx.house(p) for p in grp]
    ok = all(h in a["houses"] for h in hs) and len(set(hs)) == a["count"]
    return ok, [f"{'/'.join(grp)} in houses {', '.join(map(str, sorted(set(hs))))}"]


@predicate
def houses_occupied_by(ctx: Context, a: dict) -> Result:
    """At least `min` of `houses` hold a planet from the group (from the Lagna)."""
    grp = ctx.group(a["of"])
    held = sorted({ctx.house(p) for p in grp if ctx.house(p) in a["houses"]})
    return len(held) >= a["min"], [f"{ctx.label(a['of'])} in houses {', '.join(map(str, held)) or 'none'}"]


@predicate
def debilitation_cancelled(ctx: Context, a: dict) -> Result:
    """Neecha bhanga: a debilitated planet whose debilitation-sign lord or exaltation-sign
    lord is in a kendra from the Lagna or the Moon."""
    ev = []
    for p in GRAHAS7:
        if ctx.dignity(p) != "debilitated":
            continue
        deb_lord = SIGN_LORD[ctx.signs[p]]
        ex_lord = SIGN_LORD[EXALTATION[p][0]]
        for who, role in ((deb_lord, "lord of its debilitation sign"), (ex_lord, "lord of its exaltation sign")):
            for ref in ("La", "Mo"):
                if who != p and who != ref and ctx.house(who, ref) in KENDRAS:
                    ev.append(f"{p} debilitated; {who} ({role}) in a kendra from {ctx.name(ref)}")
    return bool(ev), sorted(set(ev))


@predicate
def kartari(ctx: Context, a: dict) -> Result:
    """Point hemmed between a group in the 2nd and 12th from it."""
    ref = a.get("of_point", "La")
    grp = [p for p in ctx.group(a["by"]) if p != ref]
    h2 = [p for p in grp if ctx.house(p, ref) == 2]
    h12 = [p for p in grp if ctx.house(p, ref) == 12]
    return bool(h2 and h12), [f"{ctx.label(a['by'])} in the 2nd from {ctx.name(ref)}: {', '.join(h2) or 'none'}; "
                            f"in the 12th: {', '.join(h12) or 'none'}"]


# ------------------------------------------------------------------- evaluator

def evaluate(cond, ctx: Context) -> Result:
    if not isinstance(cond, dict) or len(cond) != 1:
        raise ValueError(f"Bad condition: {cond!r}")
    (key, val), = cond.items()
    if key == "all":
        ev, ok = [], True
        for c in val:
            r, e = evaluate(c, ctx)
            ok &= r
            ev += e
        return ok, ev
    if key == "any":
        hits = []
        for c in val:
            r, e = evaluate(c, ctx)
            if r:
                hits += e
        return bool(hits), hits
    if key == "not":
        r, e = evaluate(val, ctx)
        return not r, [f"not: {x}" for x in e]
    if key not in PREDICATES:
        raise ValueError(f"Unknown predicate {key!r}")
    return PREDICATES[key](ctx, val or {})


@dataclass(frozen=True)
class Rule:
    id: str
    name: str
    group: str
    summary: str
    when: dict
    source: dict
    status: str = "draft"
    notes: str = ""
    cancelled_by: dict | None = None


@dataclass
class YogaResult:
    id: str
    name: str
    group: str
    present: bool
    cancelled: bool
    evidence: list[str] = field(default_factory=list)
    summary: str = ""
    source: dict = field(default_factory=dict)
    status: str = "draft"


def load_rules(folder: Path | None = None) -> list[Rule]:
    """Load every rule file in `folder` (default: the packaged rules, cached)."""
    if folder is None:
        return list(_default_rules())
    return _load(folder)


@lru_cache(maxsize=1)
def _default_rules() -> tuple[Rule, ...]:
    return tuple(_load(RULES_DIR))


def _load(folder: Path) -> list[Rule]:
    rules: list[Rule] = []
    seen: set[str] = set()
    for path in sorted(folder.glob("*.yaml")):
        for raw in yaml.safe_load(path.read_text()) or []:
            r = Rule(**raw)
            if r.id in seen:
                raise ValueError(f"Duplicate yoga id {r.id}")
            seen.add(r.id)
            rules.append(r)
    return rules


def find_yogas(chart_or_ctx: Chart | Context, rules: list[Rule] | None = None,
               include_absent: bool = False) -> list[YogaResult]:
    ctx = chart_or_ctx if isinstance(chart_or_ctx, Context) else Context.from_chart(chart_or_ctx)
    out = []
    for r in rules or load_rules():
        present, ev = evaluate(r.when, ctx)
        cancelled = False
        if present and r.cancelled_by:
            cancelled, cev = evaluate(r.cancelled_by, ctx)
            if cancelled:
                ev = ev + [f"Cancelled: {x}" for x in cev]
        if present or include_absent:
            out.append(YogaResult(r.id, r.name, r.group, present, cancelled, ev, r.summary,
                                  r.source, r.status))
    return out

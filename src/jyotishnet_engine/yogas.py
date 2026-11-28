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
    EXALTATION, GRAHA_DRISHTI, MOOLATRIKONA, NATURAL_ENEMIES, NATURAL_FRIENDS, OWN_SIGNS,
    SIGN_LORD, SIGNS, modality,
)
from .i18n import Code, Join, M
from .i18n import ordinal as _ordinal
from .i18n import sign as sign_name

RULES_DIR = Path(__file__).parent / "rules" / "yogas"
GRAHAS7 = ["Su", "Mo", "Ma", "Me", "Ju", "Ve", "Sa"]
GRAHAS9 = GRAHAS7 + ["Ra", "Ke"]
KENDRAS = [1, 4, 7, 10]
TRIKONAS = [1, 5, 9]
DUSTHANAS = [6, 8, 12]


def ordinal(n: int) -> M:
    return _ordinal(n)


def codes(points) -> list[Code]:
    return [Code(p) for p in points]


# Words in evidence strings, as the English has always spelled them.
DIGNITY = {"exalted": M("exalted"), "debilitated": M("debilitated"), "moolatrikona": M("moolatrikona"),
           "own": M("own"), "friend": M("friend"), "enemy": M("enemy"), "other": M("other"), "node": M("node")}
RELATION = {"conjunction": M("conjunction"), "mutual_aspect": M("mutual_aspect"), "aspect": M("aspect"),
            "exchange": M("exchange")}
MODALITY = {"movable": M("movable"), "fixed": M("fixed"), "dual": M("dual")}
NONE = M("none")


# Combustion orbs (degrees from the Sun; Surya Siddhanta as given in BPHS commentaries);
# Mercury and Venus have smaller orbs when retrograde.
COMBUST_ORB = {"Mo": 12.0, "Ma": 17.0, "Me": 14.0, "Ju": 11.0, "Ve": 10.0, "Sa": 15.0}
COMBUST_ORB_RETRO = {"Me": 12.0, "Ve": 8.0}


@dataclass(frozen=True)
class YogaOptions:
    """School choices inside yoga rules (docs/DECISIONS.md, Yoga strength conditions).

    strong_lord: when a rule asks for a strong planet (BPHS's "balavan" Lagna lord in
        Lakshmi and Kahala yogas): "dignity" = exalted, moolatrikona or own sign, or in a
        kendra or trikona from the Lagna, and not debilitated; "shadbala" = Shadbala at
        least the planet's required rupas (BPHS ch. 27).
    gajakesari: "bphs" = Jupiter in a kendra from the Moon (BPHS; also Jagannatha Hora
        8.0's yoga list); "phaladeepika" = also a benefic other than the Moon conjoining
        or aspecting Jupiter, and Jupiter not debilitated, combust or in an enemy's sign
        (Phaladeepika ch. 6; B. V. Raman, Three Hundred Important Combinations, no. 1).
    """
    strong_lord: str = "dignity"
    gajakesari: str = "bphs"

    def __post_init__(self) -> None:
        if self.strong_lord not in ("dignity", "shadbala"):
            raise ValueError('strong_lord must be "dignity" or "shadbala"')
        if self.gajakesari not in ("bphs", "phaladeepika"):
            raise ValueError('gajakesari must be "bphs" or "phaladeepika"')


# --------------------------------------------------------------------- context

@dataclass
class Context:
    lagna: int                         # sign 0..11
    signs: dict[str, int]              # graha -> sign
    degrees: dict[str, float]          # graha -> longitude
    moon_benefic: bool = True
    mercury_benefic: bool = True
    options: YogaOptions = field(default_factory=YogaOptions)
    retrograde: dict[str, bool] = field(default_factory=dict)
    shadbala_ratio: dict[str, float] | None = None    # rupas / required, for strong_lord="shadbala"

    @classmethod
    def from_chart(cls, chart: Chart, options: YogaOptions | None = None, birth=None,
                   cfg=None) -> "Context":
        """`birth` (and `cfg`) are needed only for options.strong_lord == "shadbala"."""
        options = options or YogaOptions()
        signs = {k: p.sign for k, p in chart.grahas.items()}
        degs = {k: p.longitude for k, p in chart.grahas.items()}
        arc = abs((degs["Mo"] - degs["Su"] + 180) % 360 - 180)
        moon_benefic = arc >= 90.0              # Shukla to Krishna Ashtami (JHora's rule)
        # Mercury is malefic in a sign with Mars, Saturn, Rahu, Ketu or a malefic Moon.
        # (Shadbala follows JHora's own convention instead; see ShadbalaOptions.)
        from .shadbala import ShadbalaOptions, mercury_is_malefic
        ratio = None
        if options.strong_lord == "shadbala":
            if birth is None:
                raise ValueError('strong_lord="shadbala" needs the birth data')
            from .chart import build_chart
            from .config import DEFAULT_CONFIG
            from .shadbala import REQUIRED_RUPAS, shadbala
            cfg = cfg or DEFAULT_CONFIG
            full = build_chart(birth, cfg, [1, 2, 3, 7, 9, 12, 30])
            ratio = {p: s.rupas / REQUIRED_RUPAS[p] for p, s in shadbala(full, birth, cfg).items()}
        retro = {k: bool(p.retrograde) for k, p in chart.grahas.items()}
        return cls(chart.lagna.sign, signs, degs, moon_benefic,
                   not mercury_is_malefic(signs, moon_benefic, ShadbalaOptions(mercury_rule="any")),
                   options, retro, ratio)

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
    def label(spec, exclude=()) -> M:
        """Readable name of a planet group, for evidence strings."""
        if isinstance(spec, list):
            return Join("/", codes(spec))
        name = {"grahas7": M("planets"), "grahas9": M("planets or nodes"), "benefics": M("benefics"),
                "malefics": M("malefics"), "malefics7": M("malefics"),
                "benefics_no_moon": M("benefics other than the Moon")}.get(spec, spec)
        return M("{name} other than {ex}", name=name, ex=Join("/", codes(exclude))) if exclude else name

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

    def name(self, point: str) -> M:
        if point == "La":
            return M("Lagna")
        if point.startswith("lord:"):
            return M("{n} lord ({p})", n=ordinal(int(point[5:])), p=Code(self.lord(int(point[5:]))))
        return Code(point)


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
    """Dignity in: exalted, moolatrikona, own, debilitated, or "friend" / "enemy" (sign of
    a natural friend / enemy)."""
    p = _resolve(ctx, a["planet"])
    d = ctx.dignity(p)
    if d == "other" and p in NATURAL_FRIENDS and SIGN_LORD[ctx.signs[p]] in NATURAL_FRIENDS[p]:
        d = "friend"
    elif d == "other" and p in NATURAL_ENEMIES and SIGN_LORD[ctx.signs[p]] in NATURAL_ENEMIES[p]:
        d = "enemy"
    return d in a["in"], [M("{p} {d} in {s}", p=ctx.name(a["planet"]), d=DIGNITY[d], s=sign_name(ctx.signs[p]))]


@predicate
def in_house(ctx: Context, a: dict) -> Result:
    """Point (or every point in `planets`) in one of `houses` counted from `from`."""
    ref = a.get("from", "La")
    pts = a.get("planets", [a.get("planet")])
    ev, ok = [], True
    for pt in pts:
        h = ctx.house(_resolve(ctx, pt), ref)
        ok &= h in a["houses"]
        ev.append(M("{p} in {h} from {ref}", p=ctx.name(pt), h=ordinal(h), ref=ctx.name(ref)))
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
    hs = Join("/", [ordinal(h) for h in a["houses"]])
    desc = Join(", ", codes(there)) if there else NONE
    who = ctx.label(a.get("of", "grahas7"), a.get("exclude", ()))
    return ok, [M("{who} in the {hs} from {ref}: {desc}", who=who, hs=hs, ref=ctx.name(ref), desc=desc)]


@predicate
def conjunct(ctx: Context, a: dict) -> Result:
    pts = [_resolve(ctx, p) for p in a["planets"]]
    s = {ctx.signs[p] for p in pts}
    return len(s) == 1, [M("{ps} together in {s}", ps=Join(" + ", codes(a["planets"])), s=sign_name(ctx.signs[pts[0]]))
                         if len(s) == 1 else M("{ps} not conjunct", ps=Join(M(" and "), codes(a["planets"])))]


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
        return a.get("same_planet_counts", True), [M("{a} is also {b}", a=ctx.name(a["a"]), b=ctx.name(a["b"]))]
    found = [r for r in _relations(ctx, x, y) if r in types]
    return bool(found), [M("{a} and {b}: {rel}", a=ctx.name(a["a"]), b=ctx.name(a["b"]),
                           rel=Join(", ", [RELATION[r] for r in found]) if found else M("no relation"))]


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
                    ev.append(M("{x} lords both the {a} and {b}", x=Code(x), a=ordinal(ha), b=ordinal(hb)))
                continue
            found = [r for r in _relations(ctx, x, y) if r in types]
            if found:
                ev.append(M("{a} lord {x} and {b} lord {y}: {rel}", a=ordinal(ha), x=Code(x), b=ordinal(hb),
                            y=Code(y), rel=Join(", ", [RELATION[r] for r in found])))
    return bool(ev), sorted(set(ev))


@predicate
def lord_in_house(ctx: Context, a: dict) -> Result:
    lord = ctx.lord(a["house"])
    h = ctx.house(lord, a.get("from", "La"))
    return h in a["houses"], [M("{n} lord {p} in {h}", n=ordinal(a["house"]), p=Code(lord), h=ordinal(h))]


@predicate
def same_lord_owns(ctx: Context, a: dict) -> Result:
    """One planet lords a house from `houses_a` and another from `houses_b` (yogakaraka)."""
    ev = []
    for p in GRAHAS7:
        owned = [h for h in range(1, 13) if ctx.lord(h) == p]
        ka = [h for h in owned if h in a["houses_a"] and h != 1]
        kb = [h for h in owned if h in a["houses_b"] and h != 1]
        if ka and kb:
            ev.append(M("{p} lords the {a} and {b}", p=Code(p), a=Join("/", map(ordinal, ka)),
                        b=Join("/", map(ordinal, kb))))
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
                    ev.append(M("{a} lord {x} and {b} lord {y} exchange signs", a=ordinal(h1), x=Code(x),
                                b=ordinal(h2), y=Code(y)))
    return bool(ev), ev


@predicate
def sign_count(ctx: Context, a: dict) -> Result:
    grp = ctx.group(a.get("of", "grahas7"))
    n = len({ctx.signs[p] for p in grp})
    return n == a["count"], [M("the seven planets occupy {n} signs", n=n) if a.get("of", "grahas7") == "grahas7"
                             else M("{who} occupy {n} signs", who=ctx.label(a["of"]), n=n)]


@predicate
def all_in_modality(ctx: Context, a: dict) -> Result:
    grp = ctx.group(a.get("of", "grahas7"))
    want = {"movable": 0, "fixed": 1, "dual": 2}[a["modality"]]
    ok = all(modality(ctx.signs[p]) == want for p in grp)
    return ok, [M("all seven planets in {m} signs", m=MODALITY[a["modality"]]) if ok
                else M("planets in mixed modalities")]


@predicate
def houses_exactly(ctx: Context, a: dict) -> Result:
    """The group occupies exactly these houses (every listed house has someone, nothing elsewhere)."""
    grp = ctx.group(a.get("of", "grahas7"))
    hs = {ctx.house(p) for p in grp}
    want = set(a["houses"])
    ok = hs == want if a.get("all_occupied", True) else hs <= want
    return ok, [M("the seven planets in houses {hs}", hs=", ".join(map(str, sorted(hs))))]


@predicate
def distinct_houses(ctx: Context, a: dict) -> Result:
    """Every planet of the group is in one of `houses`, and they occupy `count` distinct houses."""
    grp = ctx.group(a["of"])
    hs = [ctx.house(p) for p in grp]
    ok = all(h in a["houses"] for h in hs) and len(set(hs)) == a["count"]
    return ok, [M("{who} in houses {hs}", who=Join("/", codes(grp)), hs=", ".join(map(str, sorted(set(hs)))))]


@predicate
def houses_occupied_by(ctx: Context, a: dict) -> Result:
    """At least `min` of `houses` hold a planet from the group (from the Lagna)."""
    grp = ctx.group(a["of"])
    held = sorted({ctx.house(p) for p in grp if ctx.house(p) in a["houses"]})
    return len(held) >= a["min"], [M("{who} in houses {hs}", who=ctx.label(a["of"]),
                                     hs=", ".join(map(str, held)) if held else NONE)]


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
        for who, role in ((deb_lord, M("lord of its debilitation sign")), (ex_lord, M("lord of its exaltation sign"))):
            for ref in ("La", "Mo"):
                if who != p and who != ref and ctx.house(who, ref) in KENDRAS:
                    ev.append(M("{p} debilitated; {who} ({role}) in a kendra from {ref}", p=Code(p), who=Code(who),
                                role=role, ref=ctx.name(ref)))
    return bool(ev), sorted(set(ev))


@predicate
def kartari(ctx: Context, a: dict) -> Result:
    """Point hemmed between a group in the 2nd and 12th from it."""
    ref = a.get("of_point", "La")
    grp = [p for p in ctx.group(a["by"]) if p != ref]
    h2 = [p for p in grp if ctx.house(p, ref) == 2]
    h12 = [p for p in grp if ctx.house(p, ref) == 12]
    return bool(h2 and h12), [M("{who} in the 2nd from {ref}: {a}; in the 12th: {b}", who=ctx.label(a["by"]),
                                ref=ctx.name(ref), a=Join(", ", codes(h2)) if h2 else NONE,
                                b=Join(", ", codes(h12)) if h12 else NONE)]


@predicate
def strong(ctx: Context, a: dict) -> Result:
    """The planet is strong, by YogaOptions.strong_lord."""
    p = _resolve(ctx, a["planet"])
    who = ctx.name(a["planet"])
    if ctx.options.strong_lord == "shadbala":
        if ctx.shadbala_ratio is None:
            raise ValueError('strong_lord="shadbala" needs a context built with the birth data')
        r = ctx.shadbala_ratio[p]
        return r >= 1.0, [M("{p} Shadbala {r:.2f} of its required rupas", p=who, r=r)]
    d = ctx.dignity(p)
    h = ctx.house(p)
    if d == "debilitated":
        return False, [M("{p} debilitated in {s}", p=who, s=sign_name(ctx.signs[p]))]
    if d in ("exalted", "moolatrikona", "own"):
        return True, [M("{p} strong: {d} in {s}", p=who, d=DIGNITY[d], s=sign_name(ctx.signs[p]))]
    if h in KENDRAS or h in TRIKONAS:
        return True, [M("{p} strong: in the {h} house", p=who, h=ordinal(h))]
    return False, [M("{p} not strong: {d} sign, {h} house", p=who, d=DIGNITY[d], h=ordinal(h))]


@predicate
def combust(ctx: Context, a: dict) -> Result:
    """The planet within its combustion orb of the Sun."""
    p = _resolve(ctx, a["planet"])
    orb = (COMBUST_ORB_RETRO if ctx.retrograde.get(p) else COMBUST_ORB).get(p, COMBUST_ORB[p])
    sep = abs((ctx.degrees[p] - ctx.degrees["Su"] + 180.0) % 360.0 - 180.0)
    return sep < orb, [M("{p} {sep:.1f} deg from the Sun (combust within {orb:g})", p=ctx.name(a["planet"]),
                         sep=sep, orb=orb)]


@predicate
def joined_or_aspected(ctx: Context, a: dict) -> Result:
    """A planet of the group (other than the planet itself) in its sign or aspecting it."""
    p = _resolve(ctx, a["planet"])
    grp = [q for q in ctx.group(a["by"]) if q != p]
    hits = [q for q in grp if ctx.signs[q] == ctx.signs[p] or ctx.aspects(q, p)]
    return bool(hits), [M("{who} with or aspecting {p}: {hits}", who=ctx.label(a["by"]), p=ctx.name(a["planet"]),
                          hits=Join(", ", codes(hits)) if hits else NONE)]


@predicate
def option(ctx: Context, a: dict) -> Result:
    """A YogaOptions setting has the given value (for school variants inside a rule)."""
    (name, value), = a.items()
    return getattr(ctx.options, name) == value, []


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
        hits, misses, ok = [], [], False
        for c in val:
            r, e = evaluate(c, ctx)
            if r:
                ok = True
                hits += e
            else:
                misses += e
        return ok, hits if ok else misses        # when nothing holds, say why
    if key == "not":
        r, e = evaluate(val, ctx)
        return not r, [M("not: {x}", x=x) for x in e]
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
               include_absent: bool = False, options: YogaOptions | None = None,
               birth=None, cfg=None) -> list[YogaResult]:
    ctx = (chart_or_ctx if isinstance(chart_or_ctx, Context)
           else Context.from_chart(chart_or_ctx, options, birth, cfg))
    out = []
    for r in rules or load_rules():
        present, ev = evaluate(r.when, ctx)
        cancelled = False
        if present and r.cancelled_by:
            cancelled, cev = evaluate(r.cancelled_by, ctx)
            if cancelled:
                ev = ev + [M("Cancelled: {x}", x=x) for x in cev]
        if present or include_absent:
            out.append(YogaResult(r.id, M(r.name), r.group, present, cancelled, ev, M(r.summary),
                                  r.source, r.status))
    return out

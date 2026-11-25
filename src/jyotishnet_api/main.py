# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Rahul Sathe
"""FastAPI service exposing Layer 0 (design doc, Implementation: API gateway + calc engine).

Run: uvicorn jyotishnet_api.main:app --reload
"""

from __future__ import annotations

import os
from datetime import date as date_type, datetime

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from jyotishnet_engine.jaimini_jhora import RASI_DASHAS, rasi_dasha
from jyotishnet_engine import (
    Ayanamsa, BirthData, HouseSystem, NodeType, SchoolConfig, SunriseMode,
    boundary_map, build_chart, running, vimshottari, yogini,
    ashtottari,
)
from jyotishnet_engine.constants import MODEL_VARGAS, SHODASHAVARGA
from jyotishnet_engine.timeutil import jd_to_datetime, zone_warnings

app = FastAPI(title="JyotishNet API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o for o in os.environ.get(
        "JYOTISHNET_CORS", "http://localhost:3000,http://127.0.0.1:3000").split(",") if o],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


class ConfigIn(BaseModel):
    ayanamsa: Ayanamsa = Ayanamsa.LAHIRI
    node_type: NodeType = NodeType.MEAN
    house_system: HouseSystem = HouseSystem.WHOLE_SIGN
    sunrise: SunriseMode = SunriseMode.DISC_CENTER_NO_REFRACTION
    dasha_year_mode: str = Field("solar", pattern="^(solar|fixed)$")
    dasha_year_days: float = 365.25
    node_special_aspects: bool = False
    true_positions: bool = True
    rudramsa_scheme: str = Field("rath", pattern="^(rath|raman)$")
    d108_scheme: str = Field("navamsa", pattern="^(navamsa|rasi)$")
    nadiamsa_scheme: str = Field("chandra_kala", pattern="^(chandra_kala|uniform)$")
    arudha_exceptions: bool = True
    chara_exaltation_adjust: bool = False
    chara_parasara_exaltation_adjust: bool = True
    chara_co_lord_rule: str = Field("jhora", pattern="^(jhora|knrao)$")
    arudha_node_lords: bool = True
    chara_karakas: int | str = Field(8, description='8 (JHora), 7, or "parasara" (BPHS 32 as P. V. R. Narasimha Rao)')

    def to_config(self) -> SchoolConfig:
        if self.chara_karakas not in (7, 8, "parasara"):
            raise HTTPException(422, 'chara_karakas must be 7, 8 or "parasara"')
        return SchoolConfig(**self.model_dump())


class BirthIn(BaseModel):
    local_datetime: datetime = Field(description="Local clock time as recorded, no zone")
    latitude: float = Field(ge=-66, le=66, description="North positive; polar latitudes unsupported")
    longitude: float = Field(ge=-180, le=180, description="East positive")
    tz_name: str = "Asia/Kolkata"
    utc_offset_hours: float | None = None
    altitude_m: float = 0.0

    def to_birth(self) -> BirthData:
        return BirthData(self.local_datetime.replace(tzinfo=None), self.latitude, self.longitude,
                         self.tz_name, self.utc_offset_hours, self.altitude_m)

    def warnings(self) -> list[str]:
        b = self.to_birth()
        offset = (b.local_datetime - b.utc().replace(tzinfo=None)).total_seconds() / 3600
        return zone_warnings(b.local_datetime, b.latitude, b.longitude, offset)


class ChartRequest(BaseModel):
    birth: BirthIn
    config: ConfigIn = ConfigIn()
    vargas: list[int] = Field(default_factory=lambda: list(SHODASHAVARGA))


class DashaRequest(BaseModel):
    birth: BirthIn
    config: ConfigIn = ConfigIn()
    system: str = Field("vimshottari", pattern="^(vimshottari|ashtottari|yogini|chara|" + "|".join(RASI_DASHAS) + ")$")
    levels: int = Field(3, ge=1, le=3)
    at: datetime | None = Field(None, description="UTC moment for the running-period lookup")


class AshtakavargaRequest(BaseModel):
    birth: BirthIn
    config: ConfigIn = ConfigIn()
    variant: str = Field("pvr", pattern="^(bphs|pvr)$")
    occupancy: str = Field("grahas7", pattern="^(grahas7|grahas9|all)$")
    virgo_multiplier: int = Field(5, ge=5, le=6)


class BoundaryRequest(BaseModel):
    birth: BirthIn
    config: ConfigIn = ConfigIn()
    window_min: float = Field(60.0, gt=0, le=120)
    step_s: float = Field(10.0, ge=1, le=30)
    vargas: list[int] = Field(default_factory=lambda: list(MODEL_VARGAS))


def _iso(jd: float) -> str:
    return jd_to_datetime(jd).isoformat()


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/v1/chart")
def chart(req: ChartRequest) -> dict:
    try:
        c = build_chart(req.birth.to_birth(), req.config.to_config(), req.vargas)
    except ValueError as e:
        raise HTTPException(422, str(e)) from e
    out = c.to_dict()
    out["sunrise_utc"] = _iso(c.sunrise_jd)
    out["warnings"] = req.birth.warnings()
    return out


class BirthCheck(BaseModel):
    birth: BirthIn


@app.post("/v1/birth/warnings")
def birth_warnings(req: BirthCheck) -> dict:
    """Warnings about the birth record's time zone (India before 1956: war time,
    Bombay and Calcutta city times, local mean time). Never changes a chart."""
    return {"warnings": req.birth.warnings()}


def _period_json(p, depth: int) -> dict:
    d = {"lord": p.lord, "start": _iso(p.start_jd), "end": _iso(p.end_jd), "level": p.level}
    if p.name:
        d["name"] = p.name
    if depth > 1 and p.children:
        d["children"] = [_period_json(c, depth - 1) for c in p.children]
    return d


@app.post("/v1/dasha")
def dasha(req: DashaRequest) -> dict:
    birth = req.birth.to_birth()
    cfg = req.config.to_config()
    c = build_chart(birth, cfg, [1])
    moon = c.grahas["Mo"].longitude
    if req.system == "vimshottari":
        periods = vimshottari(moon, c.jd_ut, cfg, levels=req.levels)
    elif req.system == "chara":
        from jyotishnet_engine.jaimini import chara_dasha
        periods = chara_dasha(c.lagna.sign, {k: p.sign for k, p in c.grahas.items()},
                              {k: p.longitude for k, p in c.grahas.items()}, c.jd_ut, cfg,
                              levels=min(req.levels, 2))
    elif req.system in RASI_DASHAS:
        periods = rasi_dasha(req.system, c, cfg, levels=min(req.levels, 2))
    elif req.system == "ashtottari":
        periods = ashtottari(moon, c.jd_ut, cfg, levels=req.levels)
    else:
        periods = yogini(moon, c.jd_ut, cfg, levels=min(req.levels, 2))
    out = {"system": req.system, "periods": [_period_json(p, req.levels) for p in periods]}
    if req.system == "ashtottari":
        from jyotishnet_engine.dasha import ashtottari_applicable
        out["applicable"] = ashtottari_applicable(
            c.lagna.sign, {k: p.sign for k, p in c.grahas.items()})
    if req.at:
        from jyotishnet_engine.timeutil import datetime_to_jd
        out["running"] = [{"lord": p.lord, "name": p.name, "level": p.level,
                           "start": _iso(p.start_jd), "end": _iso(p.end_jd)}
                          for p in running(periods, datetime_to_jd(req.at))]
    return out


@app.post("/v1/boundaries")
def boundaries(req: BoundaryRequest) -> dict:
    changes, segments = boundary_map(req.birth.to_birth(), req.window_min, req.step_s,
                                     cfg=req.config.to_config(), vargas=req.vargas)
    return {
        "changes": [{"key": c.key, "offset_min": round(c.offset_min, 4), "utc": _iso(c.jd_ut),
                     "before": c.before, "after": c.after} for c in changes],
        "segments": [{"start_min": round(s.start_min, 4), "end_min": round(s.end_min, 4)}
                     for s in segments],
    }


@app.post("/v1/ashtakavarga")
def ashtakavarga_endpoint(req: AshtakavargaRequest) -> dict:
    from dataclasses import asdict
    from jyotishnet_engine.ashtakavarga import ashtakavarga
    c = build_chart(req.birth.to_birth(), req.config.to_config(), [1])
    av = ashtakavarga(c, req.variant, req.virgo_multiplier, req.occupancy)
    out = asdict(av)
    out.pop("prastara")
    return out


@app.post("/v1/shadbala")
def shadbala_endpoint(req: ChartRequest) -> dict:
    from jyotishnet_engine.shadbala import REQUIRED_RUPAS, shadbala
    birth, cfg = req.birth.to_birth(), req.config.to_config()
    c = build_chart(birth, cfg, [1, 2, 3, 7, 9, 12, 30])
    out = {}
    for p, s in shadbala(c, birth, cfg).items():
        out[p] = {
            "sthana": s.sthana, "dig": s.dig, "kala": s.kala, "cheshta": s.cheshta,
            "naisargika": s.naisargika, "drik": s.drik, "total_virupas": s.total,
            "rupas": s.rupas, "required_rupas": REQUIRED_RUPAS[p],
            "cheshta_counted": s.cheshta_counted, "ishta": s.ishta, "kashta": s.kashta,
            "ratio": s.rupas / REQUIRED_RUPAS[p],
        }
    from jyotishnet_engine.shadbala import planetary_wars
    wars = [{"planets": [a, b], "separation_deg": d} for a, b, d in planetary_wars(
        {p: c.grahas[p].longitude for p in ("Ma", "Me", "Ju", "Ve", "Sa")})]
    from jyotishnet_engine.bhavabala import bhava_bala
    houses = [{"house": h.house, "sign": h.sign, "lord": h.lord, "lord_virupas": h.adhipati,
               "dig": h.dig, "drik": h.drik, "total_virupas": h.total, "rupas": h.rupas}
              for h in bhava_bala(c, birth, cfg)]
    from jyotishnet_engine.avasthas import avasthas
    states = {p: {"baladi": a.baladi, "jagradadi": a.jagradadi, "moods": list(a.moods)}
              for p, a in avasthas(c).items()}
    return {"planets": out, "wars": wars, "houses": houses, "avasthas": states}


class TransitRequest(BaseModel):
    birth: BirthIn
    transit: BirthIn = Field(description="The transit moment (usually at the birth place)")
    config: ConfigIn = ConfigIn()
    years: float = Field(100.0, ge=1, le=150, description="Saturn spells from birth for this long")


@app.post("/v1/transits")
def transits_endpoint(req: TransitRequest) -> dict:
    """Gochara of the nine grahas against the natal chart (houses from the natal Moon,
    vedha, tara, murthi, Ashtakavarga and kakshya), Saturn's phase (Sade Sati,
    Kantaka, Ashtama) and its spells over the given years from birth."""
    from dataclasses import asdict as _asdict

    from jyotishnet_engine.transits import gochara, sade_sati_phase, saturn_spells
    cfg = req.config.to_config()
    try:
        natal = build_chart(req.birth.to_birth(), cfg, [1])
        tr = build_chart(req.transit.to_birth(), cfg, [1])
    except ValueError as e:
        raise HTTPException(422, str(e)) from e
    moon_sign = natal.grahas["Mo"].sign
    spells = saturn_spells(moon_sign, natal.jd_ut, natal.jd_ut + req.years * 365.25, cfg)
    return {
        "planets": {p: _asdict(t) for p, t in gochara(natal, tr, cfg).items()},
        "saturn_phase": sade_sati_phase(tr.grahas["Sa"].sign, moon_sign),
        "saturn_spells": [{"phase": s.phase, "start": _iso(s.start_jd), "end": _iso(s.end_jd)}
                          for s in spells],
    }


class AvasthaRequest(ChartRequest):
    compound: bool = Field(False, description="Jagradadi by compound (natural + temporal) "
                                              "relationship instead of natural (JHora's default)")


@app.post("/v1/avasthas")
def avasthas_endpoint(req: AvasthaRequest) -> dict:
    from jyotishnet_engine.avasthas import avasthas
    birth, cfg = req.birth.to_birth(), req.config.to_config()
    c = build_chart(birth, cfg, [1])
    return {"planets": {p: {"baladi": a.baladi, "jagradadi": a.jagradadi, "moods": list(a.moods)}
                        for p, a in avasthas(c, req.compound).items()}}


class VimshopakaRequest(ChartRequest):
    saptavarga_weights: str = Field("bphs", pattern="^(bphs|jhora)$",
                                    description="bphs (D7 2.5, D9 4.5, D12 2, D30 1) or jhora "
                                                "(D7 1, D9 2.5, D12 4.5, D30 2)")


@app.post("/v1/vimshopaka")
def vimshopaka_endpoint(req: VimshopakaRequest) -> dict:
    """Vimshopaka bala (points out of 20) in the Shad-, Sapta-, Dasha- and
    Shodashavarga schemes, for the nine grahas."""
    from jyotishnet_engine.vimshopaka import SCHEMES, VimshopakaOptions, scheme_weights, vimshopaka
    birth, cfg = req.birth.to_birth(), req.config.to_config()
    opts = VimshopakaOptions(saptavarga_weights=req.saptavarga_weights)
    c = build_chart(birth, cfg, [1])
    return {"planets": vimshopaka(c, cfg, opts),
            "weights": {s: {f"D{n}": w for n, w in scheme_weights(s, opts).items()} for s in SCHEMES}}


class YogaRequest(ChartRequest):
    include_absent: bool = False


@app.post("/v1/yogas")
def yogas_endpoint(req: YogaRequest) -> dict:
    from dataclasses import asdict
    from jyotishnet_engine.yogas import find_yogas
    c = build_chart(req.birth.to_birth(), req.config.to_config(), [1])
    ys = find_yogas(c, include_absent=req.include_absent)
    return {
        "yogas": [asdict(y) for y in ys],
        "note": "Rules are drafts pending expert review; see each rule's source and status.",
    }


# ------------------------------------------------------------------ rectification helpers

class EventIn(BaseModel):
    type: str
    date: date_type


class BtrRequest(BaseModel):
    birth: BirthIn
    config: ConfigIn = ConfigIn()
    events: list[EventIn] = Field(default_factory=list, max_length=20)


class BtrCurveRequest(BtrRequest):
    window_min: float = Field(30.0, gt=0, le=120)
    step_s: int = Field(30, ge=10, le=600)


def _events(req: BtrRequest) -> list[tuple[str, date_type]]:
    from jyotishnet_engine.btr import event_rules
    rules = event_rules()
    bad = [e.type for e in req.events if e.type not in rules]
    if bad:
        raise HTTPException(422, f"Unknown event type(s): {', '.join(bad)}. Known: {', '.join(rules)}")
    return [(e.type, e.date) for e in req.events]


@app.get("/v1/dasha/systems")
def dasha_systems() -> dict:
    """Dasha systems of /v1/dasha; the Jaimini rasi dashas follow JHora 8.0's defaults."""
    return {"graha": ["vimshottari", "ashtottari", "yogini"],
            "rasi": [{"id": "chara", "label": "Chara (K. N. Rao)"}]
            + [{"id": k, "label": v[1]} for k, v in RASI_DASHAS.items()]}


@app.get("/v1/btr/events")
def btr_event_types() -> dict:
    """Event types the rectification helpers understand."""
    from dataclasses import asdict
    from jyotishnet_engine.btr import event_rules
    return {"events": [asdict(r) for r in event_rules().values()]}


@app.post("/v1/btr/check")
def btr_check(req: BtrRequest) -> dict:
    """Event check table for the birth time given."""
    from dataclasses import asdict
    from jyotishnet_engine.btr import check_events
    return {"checks": [asdict(c) for c in check_events(req.birth.to_birth(), _events(req),
                                                       req.config.to_config())]}


@app.post("/v1/btr/curve")
def btr_curve(req: BtrCurveRequest) -> dict:
    """Total event score for candidate birth times around the recorded one."""
    from jyotishnet_engine.btr import fit_curve
    if not req.events:
        return {"points": [], "best": None, "helps_decide": [], "max_score": 0}
    return fit_curve(req.birth.to_birth(), _events(req), req.window_min, req.step_s,
                     req.config.to_config())


@app.post("/v1/btr/indicative")
def btr_indicative(req: BtrRequest) -> dict:
    """Antardashas whose lords both link to marriage, children, career or relocation.
    Death and illness are never offered as indicative periods."""
    from jyotishnet_engine.btr import indicative_periods
    out = indicative_periods(req.birth.to_birth(), req.config.to_config())
    return {"periods": {k: [{**{x: v for x, v in r.items() if not x.endswith("_jd")},
                             "start": _iso(r["start_jd"]), "end": _iso(r["end_jd"])} for r in rows]
                        for k, rows in out.items()}}

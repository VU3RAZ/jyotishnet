# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Rahul Sathe
"""FastAPI service exposing Layer 0 (design doc, Implementation: API gateway + calc engine).

Run: uvicorn jyotishnet_api.main:app --reload
"""

from __future__ import annotations

from datetime import datetime

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from jyotishnet_engine import (
    Ayanamsa, BirthData, HouseSystem, NodeType, SchoolConfig, SunriseMode,
    boundary_map, build_chart, running, vimshottari, yogini,
    ashtottari,
)
from jyotishnet_engine.constants import MODEL_VARGAS, SHODASHAVARGA
from jyotishnet_engine.timeutil import jd_to_datetime

app = FastAPI(title="JyotishNet API", version="0.1.0")


class ConfigIn(BaseModel):
    ayanamsa: Ayanamsa = Ayanamsa.LAHIRI
    node_type: NodeType = NodeType.MEAN
    house_system: HouseSystem = HouseSystem.WHOLE_SIGN
    sunrise: SunriseMode = SunriseMode.DISC_CENTER_NO_REFRACTION
    dasha_year_mode: str = Field("solar", pattern="^(solar|fixed)$")
    dasha_year_days: float = 365.25
    node_special_aspects: bool = False
    true_positions: bool = True

    def to_config(self) -> SchoolConfig:
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


class ChartRequest(BaseModel):
    birth: BirthIn
    config: ConfigIn = ConfigIn()
    vargas: list[int] = Field(default_factory=lambda: list(SHODASHAVARGA))


class DashaRequest(BaseModel):
    birth: BirthIn
    config: ConfigIn = ConfigIn()
    system: str = Field("vimshottari", pattern="^(vimshottari|ashtottari|yogini|chara)$")
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
    return out


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
        out["running"] = [{"lord": p.lord, "level": p.level, "end": _iso(p.end_jd)}
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
            "ratio": s.rupas / REQUIRED_RUPAS[p],
        }
    from jyotishnet_engine.shadbala import planetary_wars
    wars = [{"planets": [a, b], "separation_deg": d} for a, b, d in planetary_wars(
        {p: c.grahas[p].longitude for p in ("Ma", "Me", "Ju", "Ve", "Sa")})]
    return {"planets": out, "wars": wars}


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

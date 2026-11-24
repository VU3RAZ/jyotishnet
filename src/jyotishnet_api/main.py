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
)
from jyotishnet_engine.constants import MODEL_VARGAS, SHODASHAVARGA
from jyotishnet_engine.timeutil import jd_to_datetime

app = FastAPI(title="JyotishNet API", version="0.1.0")


class ConfigIn(BaseModel):
    ayanamsa: Ayanamsa = Ayanamsa.LAHIRI
    node_type: NodeType = NodeType.MEAN
    house_system: HouseSystem = HouseSystem.WHOLE_SIGN
    sunrise: SunriseMode = SunriseMode.DISC_CENTER_NO_REFRACTION
    dasha_year_days: float = 365.25
    node_special_aspects: bool = False

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
    system: str = Field("vimshottari", pattern="^(vimshottari|yogini)$")
    levels: int = Field(3, ge=1, le=3)
    at: datetime | None = Field(None, description="UTC moment for the running-period lookup")


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
    else:
        periods = yogini(moon, c.jd_ut, cfg, levels=min(req.levels, 2))
    out = {"system": req.system, "periods": [_period_json(p, req.levels) for p in periods]}
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

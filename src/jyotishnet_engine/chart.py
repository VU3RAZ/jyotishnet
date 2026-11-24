# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Rahul Sathe
"""Chart builder: one call produces everything Layer 0 knows about a moment."""

from __future__ import annotations

from dataclasses import dataclass, field, asdict

from .config import DEFAULT_CONFIG, SchoolConfig
from .constants import (
    GRAHA_DRISHTI, GRAHAS, NODE_SPECIAL_DRISHTI, SHODASHAVARGA, SIGN_LORD, SIGNS,
)
from .dignity import dignity
from .ephemeris import ascendant, ayanamsa, house_cusps, planets
from .nakshatra import nakshatra_of
from .special_lagnas import special_lagnas
from .timeutil import BirthData
from .vargas import is_vargottama, nadiamsa, varga_sign


@dataclass
class Point:
    code: str
    longitude: float
    sign: int
    degree: float
    nakshatra: str
    pada: int
    nakshatra_lord: str
    house: int                       # whole-sign house from the Lagna, 1..12
    vargas: dict[int, int]
    speed: float | None = None
    retrograde: bool | None = None
    dignity: str | None = None
    vargottama: bool | None = None
    aspects_houses: list[int] = field(default_factory=list)
    # D150: {"division", "index", "name"} (see vargas.nadiamsa)
    nadiamsa: dict = field(default_factory=dict)


@dataclass
class Chart:
    jd_ut: float
    ayanamsa: float
    config_key: str
    lagna: Point
    grahas: dict[str, Point]
    special: dict[str, Point]
    house_lords: dict[int, str]
    house_cusps: list[float]
    sunrise_jd: float

    def to_dict(self) -> dict:
        return asdict(self)

    def varga_chart(self, n: int) -> dict:
        """Signs of Lagna and grahas in Dn, plus house of each graha from the Dn Lagna."""
        lg = self.lagna.vargas[n]
        return {
            "lagna": lg,
            "grahas": {
                k: {"sign": p.vargas[n], "house": (p.vargas[n] - lg) % 12 + 1}
                for k, p in self.grahas.items()
            },
        }


def _point(code: str, lon: float, lagna_sign: int, vargas: list[int],
           cfg: SchoolConfig = DEFAULT_CONFIG) -> Point:
    nk = nakshatra_of(lon)
    sign = int(lon // 30)
    return Point(
        code=code, longitude=lon, sign=sign, degree=lon - sign * 30,
        nakshatra=nk.name, pada=nk.pada, nakshatra_lord=nk.lord,
        house=(sign - lagna_sign) % 12 + 1,
        vargas={n: varga_sign(lon, n, cfg.hora_scheme, cfg.rudramsa_scheme, cfg.d108_scheme)
                for n in vargas},
        nadiamsa=asdict(nadiamsa(lon, cfg.nadiamsa_scheme)),
    )


def build_chart(birth: BirthData, cfg: SchoolConfig = DEFAULT_CONFIG,
                vargas: list[int] | None = None) -> Chart:
    vargas = vargas or SHODASHAVARGA
    jd = birth.jd_ut()
    asc = ascendant(jd, birth.latitude, birth.longitude, cfg)
    lagna_sign = int(asc // 30)
    lagna = _point("La", asc, lagna_sign, vargas, cfg)

    grahas: dict[str, Point] = {}
    for code, pos in planets(jd, cfg).items():
        p = _point(code, pos.longitude, lagna_sign, vargas, cfg)
        p.speed = pos.speed
        p.retrograde = pos.retrograde if code not in ("Ra", "Ke") else True
        p.dignity = dignity(code, pos.longitude)
        p.vargottama = is_vargottama(pos.longitude)
        drishti = GRAHA_DRISHTI[code]
        if code in ("Ra", "Ke") and cfg.node_special_aspects:
            drishti = NODE_SPECIAL_DRISHTI
        p.aspects_houses = [((p.house - 1 + d - 1) % 12) + 1 for d in drishti]
        grahas[code] = p

    sl = special_lagnas(jd, birth.latitude, birth.longitude, birth.altitude_m, cfg)
    special = {
        "BL": _point("BL", sl.bhava_lagna, lagna_sign, vargas, cfg),
        "HL": _point("HL", sl.hora_lagna, lagna_sign, vargas, cfg),
        "GL": _point("GL", sl.ghati_lagna, lagna_sign, vargas, cfg),
        "PP": _point("PP", sl.pranapada, lagna_sign, vargas, cfg),
    }

    house_lords = {h: SIGN_LORD[(lagna_sign + h - 1) % 12] for h in range(1, 13)}
    return Chart(
        jd_ut=jd, ayanamsa=ayanamsa(jd, cfg), config_key=cfg.key(), lagna=lagna,
        grahas=grahas, special=special, house_lords=house_lords,
        house_cusps=house_cusps(jd, birth.latitude, birth.longitude, cfg),
        sunrise_jd=sl.sunrise_jd,
    )


def describe(chart: Chart) -> str:
    """Short human-readable summary, handy in tests and the CLI."""
    lines = [f"Lagna {SIGNS[chart.lagna.sign]} {chart.lagna.degree:.2f}"]
    for k in GRAHAS:
        p = chart.grahas[k]
        r = " R" if p.retrograde and k not in ("Ra", "Ke") else ""
        lines.append(f"{k} {SIGNS[p.sign]} {p.degree:.2f}{r} H{p.house} {p.nakshatra}-{p.pada} {p.dignity}")
    return "\n".join(lines)

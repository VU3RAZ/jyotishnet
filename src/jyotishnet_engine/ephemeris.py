"""Thin, thread-safe wrapper over the Swiss Ephemeris.

Swiss Ephemeris keeps the sidereal mode as global state, so every call that
depends on it runs under one lock. Without ephemeris files it falls back to the
built-in Moshier ephemeris (sub-arcsecond for planets); set SE_EPHE_PATH or call
`set_ephemeris_path` to use the Swiss Ephemeris data files.

Licensing: Swiss Ephemeris is AGPL or commercially licensed. See README.
"""

from __future__ import annotations

from dataclasses import dataclass
import os
import threading

import swisseph as swe

from .config import Ayanamsa, NodeType, SchoolConfig, SunriseMode, HouseSystem

_LOCK = threading.RLock()
_EPHE_PATH: str | None = os.environ.get("SE_EPHE_PATH")
if _EPHE_PATH:
    swe.set_ephe_path(_EPHE_PATH)

_SIDM = {
    Ayanamsa.LAHIRI: swe.SIDM_LAHIRI,
    Ayanamsa.RAMAN: swe.SIDM_RAMAN,
    Ayanamsa.KP: swe.SIDM_KRISHNAMURTI,
    Ayanamsa.TRUE_CHITRA: swe.SIDM_TRUE_CITRA,
    Ayanamsa.YUKTESHWAR: swe.SIDM_YUKTESHWAR,
    Ayanamsa.FAGAN_BRADLEY: swe.SIDM_FAGAN_BRADLEY,
}

_HSYS = {
    HouseSystem.WHOLE_SIGN: b"W",
    HouseSystem.SRIPATI: b"S",
    HouseSystem.PLACIDUS: b"P",
    HouseSystem.KOCH: b"K",
    HouseSystem.EQUAL: b"E",
    HouseSystem.PORPHYRY: b"O",
}

_BODIES = {
    "Su": swe.SUN, "Mo": swe.MOON, "Ma": swe.MARS, "Me": swe.MERCURY,
    "Ju": swe.JUPITER, "Ve": swe.VENUS, "Sa": swe.SATURN,
}


def set_ephemeris_path(path: str | None) -> None:
    global _EPHE_PATH
    with _LOCK:
        _EPHE_PATH = path
        swe.set_ephe_path(path)


def _base_flags(cfg: SchoolConfig | None = None) -> int:
    flags = swe.FLG_SWIEPH if _EPHE_PATH else swe.FLG_MOSEPH
    if cfg is not None and cfg.true_positions:
        flags |= swe.FLG_TRUEPOS
    return flags


@dataclass(frozen=True)
class BodyPosition:
    longitude: float   # sidereal, degrees 0..360
    latitude: float
    speed: float       # degrees per day; negative = retrograde

    @property
    def retrograde(self) -> bool:
        return self.speed < 0


def norm(deg: float) -> float:
    return deg % 360.0


def ayanamsa(jd_ut: float, cfg: SchoolConfig) -> float:
    with _LOCK:
        swe.set_sid_mode(_SIDM[cfg.ayanamsa], 0, 0)
        return swe.get_ayanamsa_ut(jd_ut)


def planets(jd_ut: float, cfg: SchoolConfig) -> dict[str, BodyPosition]:
    """Sidereal positions of the nine grahas."""
    flags = _base_flags(cfg) | swe.FLG_SIDEREAL | swe.FLG_SPEED
    out: dict[str, BodyPosition] = {}
    with _LOCK:
        swe.set_sid_mode(_SIDM[cfg.ayanamsa], 0, 0)
        for code, body in _BODIES.items():
            xx, _ = swe.calc_ut(jd_ut, body, flags)
            out[code] = BodyPosition(norm(xx[0]), xx[1], xx[3])
        node = swe.MEAN_NODE if cfg.node_type == NodeType.MEAN else swe.TRUE_NODE
        xx, _ = swe.calc_ut(jd_ut, node, flags)
        out["Ra"] = BodyPosition(norm(xx[0]), xx[1], xx[3])
        out["Ke"] = BodyPosition(norm(xx[0] + 180.0), -xx[1], xx[3])
    return out


def ascendant(jd_ut: float, lat: float, lon: float, cfg: SchoolConfig) -> float:
    """Sidereal ascendant longitude."""
    with _LOCK:
        swe.set_sid_mode(_SIDM[cfg.ayanamsa], 0, 0)
        _, ascmc = swe.houses_ex(jd_ut, lat, lon, b"W", swe.FLG_SIDEREAL)
    return norm(ascmc[0])


def house_cusps(jd_ut: float, lat: float, lon: float, cfg: SchoolConfig) -> list[float]:
    """Sidereal cusps of houses 1..12 in the configured house system."""
    with _LOCK:
        swe.set_sid_mode(_SIDM[cfg.ayanamsa], 0, 0)
        cusps, _ = swe.houses_ex(jd_ut, lat, lon, _HSYS[cfg.house_system], swe.FLG_SIDEREAL)
    return [norm(c) for c in cusps[:12]]


def body_longitude(jd_ut: float, code: str, cfg: SchoolConfig) -> float:
    """Sidereal longitude of one graha (fast path for scans)."""
    flags = _base_flags(cfg) | swe.FLG_SIDEREAL
    with _LOCK:
        swe.set_sid_mode(_SIDM[cfg.ayanamsa], 0, 0)
        if code in ("Ra", "Ke"):
            node = swe.MEAN_NODE if cfg.node_type == NodeType.MEAN else swe.TRUE_NODE
            xx, _ = swe.calc_ut(jd_ut, node, flags)
            return norm(xx[0] + (180.0 if code == "Ke" else 0.0))
        xx, _ = swe.calc_ut(jd_ut, _BODIES[code], flags)
    return norm(xx[0])


def sun_longitude(jd_ut: float, cfg: SchoolConfig) -> float:
    return body_longitude(jd_ut, "Su", cfg)


def previous_sunrise(jd_ut: float, lat: float, lon: float, alt: float, cfg: SchoolConfig) -> float:
    """Julian day (UT) of the last sunrise at or before jd_ut."""
    rsmi = swe.CALC_RISE
    if cfg.sunrise == SunriseMode.DISC_CENTER_NO_REFRACTION:
        rsmi |= swe.BIT_DISC_CENTER | swe.BIT_NO_REFRACTION
    elif cfg.sunrise == SunriseMode.DISC_CENTER_REFRACTION:
        rsmi |= swe.BIT_DISC_CENTER
    geopos = (lon, lat, alt)
    with _LOCK:
        res, tret = swe.rise_trans(jd_ut - 1.0, swe.SUN, rsmi, geopos, 0.0, 0.0, _base_flags())
        if res != 0:
            raise ValueError("No sunrise found (polar day or night at this latitude).")
        rise = tret[0]
        # Step forward while the next sunrise is still before the birth moment.
        while True:
            res2, tret2 = swe.rise_trans(rise + 0.01, swe.SUN, rsmi, geopos, 0.0, 0.0, _base_flags())
            if res2 != 0 or tret2[0] > jd_ut:
                break
            rise = tret2[0]
    return rise

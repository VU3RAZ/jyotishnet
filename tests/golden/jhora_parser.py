# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Rahul Sathe
"""Parser for Jagannatha Hora "Natal Chart" text exports (tests/golden/jhora/*.txt)."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path

SIGNS = ["Ar", "Ta", "Ge", "Cn", "Le", "Vi", "Li", "Sc", "Sg", "Cp", "Aq", "Pi"]
BODY_CODES = {"Lagna": "La", "Sun": "Su", "Moon": "Mo", "Mars": "Ma", "Mercury": "Me",
              "Jupiter": "Ju", "Venus": "Ve", "Saturn": "Sa", "Rahu": "Ra", "Ketu": "Ke",
              "Bhava Lagna": "BL", "Hora Lagna": "HL", "Ghati Lagna": "GL",
              "Pranapada Lagna": "PP"}
DASHA_CODES = {"Sun": "Su", "Moon": "Mo", "Mars": "Ma", "Merc": "Me", "Jup": "Ju",
               "Ven": "Ve", "Sat": "Sa", "Rah": "Ra", "Ket": "Ke"}
PLANET_ROWS = ["As", "Su", "Mo", "Ma", "Me", "Ju", "Ve", "Sa"]


@dataclass
class JHoraChart:
    name: str
    local: datetime
    utc_offset_hours: float
    latitude: float
    longitude: float
    altitude_m: float
    ayanamsa: float
    sunrise: str
    sunset: str
    longitudes: dict[str, float] = field(default_factory=dict)
    navamsa: dict[str, int] = field(default_factory=dict)
    retrograde: dict[str, bool] = field(default_factory=dict)
    bav: dict[str, list[int]] = field(default_factory=dict)          # As, Su..Sa
    pindas: dict[str, tuple[int, int, int]] = field(default_factory=dict)  # sodhya, rasi, graha
    shadbala: dict[str, float] = field(default_factory=dict)         # virupas
    shadbala_rupas: dict[str, float] = field(default_factory=dict)
    ishta: dict[str, float] = field(default_factory=dict)            # Ishta phala
    kashta: dict[str, float] = field(default_factory=dict)           # Kashta phala
    vimshottari: list[tuple[str, str, date]] = field(default_factory=list)  # (md, ad, start)
    # {graha: {scheme: points}}; schemes dashavarga, shodashavarga, saptavarga, shadvarga
    vimshopaka: dict[str, dict[str, float]] = field(default_factory=dict)


def _dms(d: str, m: str, s: str) -> float:
    return int(d) + int(m) / 60 + float(s) / 3600


def _hms_hours(text: str) -> float:
    parts = [float(x) for x in text.split(":")]
    while len(parts) < 3:
        parts.append(0.0)
    return parts[0] + parts[1] / 60 + parts[2] / 3600


def parse(path: str | Path) -> JHoraChart:
    text = Path(path).read_text(encoding="utf-8", errors="replace")
    get = lambda label: re.search(rf"^{label}:\s+(.+)$", text, re.M).group(1).strip()

    d = datetime.strptime(get("Date"), "%B %d, %Y")
    t = [int(x) for x in get("Time").split(":")]
    local = d.replace(hour=t[0], minute=t[1], second=t[2] if len(t) > 2 else 0)

    tz = re.match(r"([\d:]+)\s+\((East|West)", get("Time Zone"))
    offset = _hms_hours(tz.group(1)) * (1 if tz.group(2) == "East" else -1)

    pm = re.match(r"""(\d+)\s+([EW])\s+(\d+)'\s+(\d+)",\s+(\d+)\s+([NS])\s+(\d+)'\s+(\d+)\"""", get("Place"))
    lon = (int(pm.group(1)) + int(pm.group(3)) / 60 + int(pm.group(4)) / 3600) * (1 if pm.group(2) == "E" else -1)
    lat = (int(pm.group(5)) + int(pm.group(7)) / 60 + int(pm.group(8)) / 3600) * (1 if pm.group(6) == "N" else -1)
    alt_m = re.search(r"^Altitude:\s+([\d.]+)", text, re.M)

    am = re.match(r"(\d+)-(\d+)-([\d.]+)", get("Ayanamsa"))
    chart = JHoraChart(
        name=Path(path).stem, local=local, utc_offset_hours=offset, latitude=lat, longitude=lon,
        altitude_m=float(alt_m.group(1)) if alt_m else 0.0,
        ayanamsa=_dms(*am.groups()), sunrise=get("Sunrise"), sunset=get("Sunset"),
    )

    body_re = re.compile(
        r"""^(Lagna|Sun|Moon|Mars|Mercury|Jupiter|Venus|Saturn|Rahu|Ketu|Bhava Lagna|Hora Lagna|Ghati Lagna|Pranapada Lagna)"""
        r"""(\s+\(R\))?(?:\s+-\s+\w+)?\s+(\d+)\s+(\w\w)\s+(\d+)'\s+([\d.]+)"\s+\S+\s+\d\s+\w\w\s+(\w\w)""", re.M)
    for m in body_re.finditer(text):
        code = BODY_CODES[m.group(1)]
        if code in chart.longitudes:
            continue
        chart.longitudes[code] = SIGNS.index(m.group(4)) * 30 + _dms(m.group(3), m.group(5), m.group(6))
        chart.navamsa[code] = SIGNS.index(m.group(7))
        chart.retrograde[code] = bool(m.group(2))

    av = text.split("Ashtakavarga of Rasi Chart:")[1]
    for row in PLANET_ROWS:
        m = re.search(rf"^{row}\s+((?:\d+\*?\s+){{11}}\d+\*?)", av, re.M)
        chart.bav[row] = [int(x.rstrip("*")) for x in m.group(1).split()]
    for row in PLANET_ROWS:
        m = re.search(rf"^{row}\s+(\d+)\s+(\d+)\s+(\d+)\s*$", av, re.M)
        chart.pindas[row] = (int(m.group(1)), int(m.group(2)), int(m.group(3)))

    for name, code in [("Sun", "Su"), ("Moon", "Mo"), ("Mars", "Ma"), ("Mercury", "Me"),
                       ("Jupiter", "Ju"), ("Venus", "Ve"), ("Saturn", "Sa")]:
        m = re.search(rf"^{name}\s+([\d.]+)\s+([\d.]+)\s+[\d.]+\s+([\d.]+)\s+([\d.]+)\s*$", text, re.M)
        chart.shadbala[code] = float(m.group(1))
        chart.shadbala_rupas[code] = float(m.group(2))
        chart.ishta[code] = float(m.group(3))
        chart.kashta[code] = float(m.group(4))

    if "Vimsopaka Dasa Varga" in text:
        block = text.split("Vimsopaka Dasa Varga")[1].split("Planet  Age")[0]
        names = {"Sun": "Su", "Moon": "Mo", "Mars": "Ma", "Mercury": "Me", "Jupiter": "Ju",
                 "Venus": "Ve", "Saturn": "Sa", "Rahu": "Ra", "Ketu": "Ke"}
        schemes = ["dashavarga", "shodashavarga", "saptavarga", "shadvarga"]
        for line in block.splitlines():
            parts = line.split()
            if parts and parts[0] in names:
                vals = [float(x) for x in parts[1:] if not x.startswith("(")]
                chart.vimshopaka[names[parts[0]]] = dict(zip(schemes, vals))

    vim = text.split("Vimsottari Dasa")[1].split("Moola Dasa")[0]
    md = None
    for line in vim.splitlines():
        head = re.match(r"^(\w+)\s{2,}", line)
        if head and head.group(1) in DASHA_CODES:
            md = DASHA_CODES[head.group(1)]
        for ad, ymd in re.findall(r"(Sun|Moon|Mars|Merc|Jup|Ven|Sat|Rah|Ket)\s+(\d{4}-\d{2}-\d{2})", line):
            chart.vimshottari.append((md, DASHA_CODES[ad], date.fromisoformat(ymd)))
    return chart


def load_all(folder: str | Path | None = None) -> list[JHoraChart]:
    folder = Path(folder) if folder else Path(__file__).parent / "jhora"
    return [parse(p) for p in sorted(folder.glob("*.txt"))]

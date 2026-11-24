# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Rahul Sathe
"""Write Jagannatha Hora .jhd chart files from a tab-separated list.

    python tools/jhora/make_jhd.py charts.tsv out_dir

Columns: name, date (YYYY-MM-DD), time (HH:MM:SS), latitude (north +),
longitude (east +), UTC offset in hours (decimal, summer time included),
place, country. Lines starting with # are ignored.

JHora's encoding: time, zone and coordinates as whole units + minutes/100 +
seconds/6000 (77 deg 12' 36" is 77.126); zone and longitude east negative,
latitude north positive; CRLF line ends.
"""

from __future__ import annotations

import sys
from pathlib import Path


def sexa(x: float) -> float:
    """Decimal units to JHora's units + minutes/100 + seconds/6000, sign kept."""
    s = round(abs(x) * 3600, 2)
    d, rem = divmod(s, 3600)
    m, sec = divmod(rem, 60)
    v = d + m / 100 + sec / 6000
    return -v if x < 0 else v


def jhd(date: str, time: str, lat: float, lon: float, offset: float, place: str, country: str) -> str:
    y, mo, d = (int(v) for v in date.split("-"))
    hh, mm, ss = (int(v) for v in time.split(":"))
    fields = [mo, d, y, f"{hh + mm / 100 + ss / 6000:.6f}", f"{sexa(-offset):.6f}",
              f"{sexa(-lon):.6f}", f"{sexa(lat):.6f}", "0.000000",
              f"{-offset:.6f}", f"{-offset:.6f}", 0, 0, place, country, 1,
              "1013.250000", "20.000000", 0]
    return "".join(f"{f}\r\n" for f in fields)


def main() -> int:
    src, out = Path(sys.argv[1]), Path(sys.argv[2])
    out.mkdir(parents=True, exist_ok=True)
    for line in src.read_text().splitlines():
        if not line.strip() or line.startswith("#"):
            continue
        name, date, time, lat, lon, off, place, country = line.split("\t")
        (out / f"{name}.jhd").write_text(
            jhd(date, time, float(lat), float(lon), float(off), place, country), newline="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

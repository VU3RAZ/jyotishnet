# SPDX-License-Identifier: AGPL-3.0-or-later
"""Yogi, Sahayogi and Avayogi against Jagannatha Hora 8.0 (Basics > right-click the
body table > "Yogi, Sahayogi and Avayogi Planets" > Copy to clipboard;
tests/golden/jhora_yogi/), on the 55 golden charts. The Yogi point is Sun + Moon
+ 93 deg 20', so it carries the Sun's and Moon's 5" each."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent / "golden"))
from jhora_parser import SIGNS, parse  # noqa: E402

from jyotishnet_engine import BirthData, DEFAULT_CONFIG, build_chart  # noqa: E402
from jyotishnet_engine.nakshatra import nakshatra_of  # noqa: E402

GOLDEN = Path(__file__).parent / "golden"
FILES = sorted((GOLDEN / "jhora_yogi").glob("*.txt"))
CODES = {"Sun": "Su", "Moon": "Mo", "Mars": "Ma", "Mercury": "Me", "Jupiter": "Ju",
         "Venus": "Ve", "Saturn": "Sa", "Rahu": "Ra", "Ketu": "Ke"}


def load(path: Path) -> dict[str, tuple[str, float | None]]:
    out = {}
    for line in path.read_text().splitlines():
        w = line.split()
        if w and w[0] in ("Yogi", "Sahayogi", "Avayogi"):
            lon = None
            if len(w) >= 6:
                deg, sign, mins, secs = w[2], w[3], w[4].rstrip("'"), w[5].rstrip('"')
                lon = SIGNS.index(sign) * 30 + int(deg) + int(mins) / 60 + float(secs) / 3600
            out[w[0]] = (CODES[w[1]], lon)
    return out


def _arc(a: float, b: float) -> float:
    d = abs(a - b) % 360.0
    return min(d, 360.0 - d)


@pytest.mark.parametrize("path", FILES, ids=[f.stem for f in FILES])
def test_yogi(path):
    c = parse(GOLDEN / "jhora" / path.name)
    b = BirthData(c.local, c.latitude, c.longitude, utc_offset_hours=c.utc_offset_hours,
                  altitude_m=c.altitude_m)
    y = build_chart(b, DEFAULT_CONFIG, [1]).yogi
    jh = load(path)
    assert _arc(y["point"], jh["Yogi"][1]) * 3600 < 10
    assert _arc(y["avayogi_point"], jh["Avayogi"][1]) * 3600 < 10
    tol = 10 / 3600
    near = lambda x: nakshatra_of(x - tol).lord != nakshatra_of(x + tol).lord   # noqa: E731
    if not near(y["point"]):
        assert y["yogi"] == jh["Yogi"][0]
    if not near(y["avayogi_point"]):
        assert y["avayogi"] == jh["Avayogi"][0]
    if int((y["point"] - tol) // 30) == int((y["point"] + tol) // 30):
        assert y["sahayogi"] == jh["Sahayogi"][0]

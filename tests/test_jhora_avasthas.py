# SPDX-License-Identifier: AGPL-3.0-or-later
"""Avasthas against Jagannatha Hora 8.0's "Basic Avasthas" table (age, alertness,
mood in D-1; tests/golden/jhora_avasthas/, Strengths > Other strengths >
right-click the Vimsopaka table)."""

import re
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent / "golden"))
from jhora_parser import parse  # noqa: E402

from jyotishnet_engine import BirthData, DEFAULT_CONFIG, build_chart  # noqa: E402
from jyotishnet_engine.avasthas import avasthas, baladi  # noqa: E402

GOLDEN = Path(__file__).parent / "golden"
FILES = sorted((GOLDEN / "jhora_avasthas").glob("*.txt"))
NAMES = {"Sun": "Su", "Moon": "Mo", "Mars": "Ma", "Mercury": "Me", "Jupiter": "Ju",
         "Venus": "Ve", "Saturn": "Sa", "Rahu": "Ra", "Ketu": "Ke"}


def load(path: Path) -> dict[str, tuple[str, str, set[str]]]:
    out = {}
    for line in path.read_text().splitlines():
        words = line.split()
        if words and words[0] in NAMES:
            states = re.findall(r"([A-Z][a-z]+) \(", line)
            out[NAMES[words[0]]] = (states[0], states[1], set(states[2:]))
    return out


@pytest.mark.parametrize("path", FILES, ids=[f.stem for f in FILES])
def test_avasthas(path):
    c = parse(GOLDEN / "jhora" / path.name)
    b = BirthData(c.local, c.latitude, c.longitude, utc_offset_hours=c.utc_offset_hours,
                  altitude_m=c.altitude_m)
    ours = avasthas(build_chart(b, DEFAULT_CONFIG))
    jh = load(path)
    assert len(jh) == 9
    for p, (age, alert, moods) in jh.items():
        assert (ours[p].baladi, ours[p].jagradadi, set(ours[p].moods)) == (age, alert, moods), p


def test_baladi_parts():
    assert baladi(0.0) == "Baala" and baladi(13.0) == "Yuva" and baladi(29.9) == "Mrita"
    assert baladi(30.0 + 1.0) == "Mrita" and baladi(30.0 + 29.0) == "Baala"   # Taurus reversed

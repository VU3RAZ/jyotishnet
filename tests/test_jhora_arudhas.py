# SPDX-License-Identifier: AGPL-3.0-or-later
"""Bhava arudhas (A1 = AL .. A12 = UL) against Jagannatha Hora 8.0's D-1 chart drawings.

tests/golden/jhora_arudhas.json holds the sign in which each arudha label appears in
JHora's North Indian rasi chart (default settings; Mandi and special lagnas hidden so
the labels show), read from screenshots of the 55 golden charts. null: the label is
hidden under other text in the drawing (29 of 660).
"""

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent / "golden"))
from jhora_parser import parse  # noqa: E402

from jyotishnet_engine import BirthData, DEFAULT_CONFIG, build_chart  # noqa: E402

SIGNS = "Ar Ta Ge Cn Le Vi Li Sc Sg Cp Aq Pi".split()
GOLDEN = Path(__file__).parent / "golden"
ARUDHAS = json.loads((GOLDEN / "jhora_arudhas.json").read_text())


def test_counts():
    assert len(ARUDHAS) == 55
    assert sum(s is None for v in ARUDHAS.values() for s in v) == 29


@pytest.mark.parametrize("name", sorted(ARUDHAS))
def test_bhava_arudhas(name):
    c = parse(GOLDEN / "jhora" / f"{name}.txt")
    ch = build_chart(BirthData(c.local, c.latitude, c.longitude, utc_offset_hours=c.utc_offset_hours,
                               altitude_m=c.altitude_m), DEFAULT_CONFIG, [1])
    mine = [SIGNS[s] for s in ch.arudhas]
    theirs = ARUDHAS[name]
    assert [m if t else None for m, t in zip(mine, theirs)] == theirs

# SPDX-License-Identifier: AGPL-3.0-or-later
"""D150 nadiamsa against Jagannatha Hora 8.0's "Amsa rulers" table for D-150
(Basics > Amsa rulers > right-click > Nadyamsa (D-150) > Copy to clipboard;
tests/golden/jhora_nadiamsa/): division, index and name of the Lagna and the
nine grahas on the 55 golden charts."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent / "golden"))
from jhora_parser import parse  # noqa: E402

from jyotishnet_engine import BirthData, DEFAULT_CONFIG, build_chart  # noqa: E402
from jyotishnet_engine.vargas import nadiamsa  # noqa: E402

GOLDEN = Path(__file__).parent / "golden"
FILES = sorted((GOLDEN / "jhora_nadiamsa").glob("*.txt"))
NAMES = {"Lagna": "La", "Sun": "Su", "Moon": "Mo", "Mars": "Ma", "Mercury": "Me",
         "Jupiter": "Ju", "Venus": "Ve", "Saturn": "Sa", "Rahu": "Ra", "Ketu": "Ke"}
TOL = {"La": 30.0, "Ra": 1.0, "Ke": 1.0}


def load(path: Path) -> dict[str, tuple[int, int, str]]:
    out = {}
    for line in path.read_text().splitlines():
        body = line[:23].replace("(R)", "").strip()
        if body in NAMES and NAMES[body] not in out:
            division, index, *name = line[23:].split()
            out[NAMES[body]] = (int(division), int(index), " ".join(name))
    return out


@pytest.mark.parametrize("path", FILES, ids=[f.stem for f in FILES])
def test_nadiamsa(path):
    c = parse(GOLDEN / "jhora" / path.name)
    b = BirthData(c.local, c.latitude, c.longitude, utc_offset_hours=c.utc_offset_hours,
                  altitude_m=c.altitude_m)
    ch = build_chart(b, DEFAULT_CONFIG, [1])
    lons = {"La": ch.lagna.longitude, **{p: g.longitude for p, g in ch.grahas.items()}}
    jh = load(path)
    assert len(jh) == 10
    for body, want in jh.items():
        tol = TOL.get(body, 5.0) / 3600
        n = nadiamsa(lons[body])
        if nadiamsa(lons[body] - tol) != n or nadiamsa(lons[body] + tol) != n:
            continue   # within the position tolerance of a nadiamsa boundary
        assert (n.division, n.index, n.name) == want, body


def test_nadiamsa_index_by_modality():
    # Division 1 of a movable, fixed and dual sign.
    assert nadiamsa(0.01).index == 1          # Aries
    assert nadiamsa(30.01).index == 150       # Taurus: reversed
    assert nadiamsa(60.01).index == 76        # Gemini: +75
    assert nadiamsa(29.99).division == 150
    assert nadiamsa(0.3, "uniform").division == 2

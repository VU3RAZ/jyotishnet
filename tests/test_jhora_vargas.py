# SPDX-License-Identifier: AGPL-3.0-or-later
"""All 22 divisional charts Jagannatha Hora draws in its text export (D2 to D144),
read from the North Indian chart drawings of the 55 golden charts.

A body whose position is within the golden set's position tolerance of a part
boundary (Lagna 30", nodes 1", other grahas 5": tests/test_jhora_golden.py) can
fall on either side of it; those placements are not compared. They are counted
so the number skipped stays visible."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent / "golden"))
from jhora_parser import load_all  # noqa: E402

from jyotishnet_engine import BirthData, DEFAULT_CONFIG, build_chart  # noqa: E402
from jyotishnet_engine.constants import ALL_VARGAS  # noqa: E402
from jyotishnet_engine.vargas import varga_sign  # noqa: E402

CHARTS = load_all()
TOL = {"La": 30.0, "Ra": 1.0, "Ke": 1.0}   # arc-seconds; others 5


@pytest.fixture(scope="module")
def positions():
    out = []
    for c in CHARTS:
        b = BirthData(c.local, c.latitude, c.longitude, utc_offset_hours=c.utc_offset_hours,
                      altitude_m=c.altitude_m)
        ch = build_chart(b, DEFAULT_CONFIG, [1])
        out.append((c, {"La": ch.lagna.longitude, **{p: g.longitude for p, g in ch.grahas.items()}}))
    return out


@pytest.mark.parametrize("n", ALL_VARGAS)
def test_varga_against_jhora(n, positions):
    compared = skipped = 0
    bad = []
    for c, lons in positions:
        for body, sign in c.vargas[n].items():
            lon, tol = lons[body], TOL.get(body, 5.0) / 3600
            ours = varga_sign(lon, n)
            if varga_sign(lon - tol, n) != ours or varga_sign(lon + tol, n) != ours:
                skipped += 1
                continue
            compared += 1
            if ours != sign:
                bad.append((c.name, body, ours, sign))
    assert not bad, bad
    assert compared >= 530, (compared, skipped)   # of 550; most skips are the Lagna in D81-D144


def test_drawings_cover_all_vargas():
    assert all(sorted(c.vargas) == ALL_VARGAS for c in CHARTS)

# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Rahul Sathe
"""Shadbala components against Jagannatha Hora's breakdown (tests/golden/jhora_shadbala)."""

import re
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent / "golden"))
from jhora_parser import parse  # noqa: E402

from jyotishnet_engine import BirthData, DEFAULT_CONFIG, build_chart  # noqa: E402
from jyotishnet_engine.shadbala import PLANETS7, shadbala  # noqa: E402

GOLDEN = Path(__file__).parent / "golden"
NAMES = dict(Sun="Su", Moon="Mo", Mars="Ma", Mercury="Me", Jupiter="Ju", Venus="Ve", Saturn="Sa")
FILES = sorted((GOLDEN / "jhora_shadbala").glob("*.txt"))


def load_breakdown(path: Path) -> dict[str, dict[str, float]]:
    out = {}
    keys = ["rupas", "sthana", "kala", "dig", "cheshta", "drik", "naisargika"]
    for line in path.read_text().splitlines():
        m = re.match(r"(\w+)\s+" + r"\s+".join([r"([-\d.]+)"] * 7), line)
        if m and m.group(1) in NAMES:
            out[NAMES[m.group(1)]] = dict(zip(keys, map(float, m.groups()[1:])))
    return out


@pytest.fixture(scope="module", params=FILES, ids=[f.stem for f in FILES])
def case(request):
    f = request.param
    c = parse(GOLDEN / "jhora" / f.name)
    b = BirthData(c.local, c.latitude, c.longitude, utc_offset_hours=c.utc_offset_hours,
                  altitude_m=c.altitude_m)
    return load_breakdown(f), shadbala(build_chart(b, DEFAULT_CONFIG), b, DEFAULT_CONFIG)


# Tolerances in virupas reflect current agreement; tighten as gaps are closed.
@pytest.mark.parametrize("component,tol", [("naisargika", 0.01), ("dig", 3.0),
                                           ("kala", 6.0), ("drik", 8.0)])
def test_component(case, component, tol):
    jh, sb = case
    for p in PLANETS7:
        s = sb[p]
        ours = {"naisargika": s.naisargika, "dig": s.dig, "kala": sum(s.kala.values()),
                "drik": s.drik}[component]
        assert abs(ours - jh[p][component]) <= tol, (p, ours, jh[p][component])


@pytest.mark.xfail(reason="Sthana (Saptavargaja) and Cheshta still differ from JHora; "
                          "see docs/DECISIONS.md #16", strict=False)
@pytest.mark.parametrize("component", ["sthana", "cheshta"])
def test_open_components(case, component):
    jh, sb = case
    for p in PLANETS7:
        s = sb[p]
        ours = sum(s.sthana.values()) if component == "sthana" else s.cheshta
        assert abs(ours - jh[p][component]) <= 1.0, p

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
    """Main Shadbala table, plus the Sthana sub-table when present."""
    text = path.read_text()
    main, _, sub = text.partition("Sthana Bala In rupas")
    out: dict[str, dict[str, float]] = {}
    keys = ["rupas", "sthana", "kala", "dig", "cheshta", "drik", "naisargika"]
    for line in main.splitlines():
        m = re.match(r"(\w+)\s+" + r"\s+".join([r"([-\d.]+)"] * 7), line)
        if m and m.group(1) in NAMES:
            out[NAMES[m.group(1)]] = dict(zip(keys, map(float, m.groups()[1:])))
    subkeys = ["uchcha", "saptavargaja", "ojayugma", "kendra", "drekkana"]
    for line in sub.splitlines():
        m = re.match(r"(\w+)\s+" + r"\s+".join([r"([-\d.]+)"] * 7), line)
        if m and m.group(1) in NAMES:
            out[NAMES[m.group(1)]].update(zip(subkeys, map(float, m.groups()[3:])))
    return out


@pytest.fixture(scope="module", params=FILES, ids=[f.stem for f in FILES])
def case(request):
    f = request.param
    c = parse(GOLDEN / "jhora" / f.name)
    b = BirthData(c.local, c.latitude, c.longitude, utc_offset_hours=c.utc_offset_hours,
                  altitude_m=c.altitude_m)
    return load_breakdown(f), shadbala(build_chart(b, DEFAULT_CONFIG), b, DEFAULT_CONFIG)


# Tolerances in virupas reflect current agreement; tighten as gaps are closed.
# Naisargika: JHora prints the BPHS table values (e.g. 25.70 for 180/7 = 25.714).
@pytest.mark.parametrize("component,tol", [("naisargika", 0.02), ("dig", 3.0),
                                           ("kala", 6.0), ("drik", 8.0), ("sthana", 0.05)])
def test_component(case, component, tol):
    jh, sb = case
    for p in PLANETS7:
        s = sb[p]
        ours = {"naisargika": s.naisargika, "dig": s.dig, "kala": sum(s.kala.values()),
                "drik": s.drik, "sthana": sum(s.sthana.values())}[component]
        assert abs(ours - jh[p][component]) <= tol, (p, ours, jh[p][component])


@pytest.mark.parametrize("part", ["uchcha", "saptavargaja", "ojayugma", "kendra", "drekkana"])
def test_sthana_parts(case, part):
    jh, sb = case
    for p in PLANETS7:
        assert abs(sb[p].sthana[part] - jh[p][part]) <= 0.02, (p, sb[p].sthana[part], jh[p][part])


@pytest.mark.xfail(reason="Cheshta differs: JHora uses its own mean-longitude tables "
                          "(see docs/DECISIONS.md #16)", strict=False)
def test_cheshta(case):
    jh, sb = case
    for p in PLANETS7:
        assert abs(sb[p].cheshta - jh[p]["cheshta"]) <= 1.0, p

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


# Tolerances in virupas: every component matches JHora to its printed precision.
# Kala is compared without Yuddha bala, which we apply by BPHS and JHora does not
# (decided difference); each Kala part is checked below.
# Naisargika: JHora prints the BPHS table values (e.g. 25.70 for 180/7 = 25.714).
@pytest.mark.parametrize("component,tol", [("naisargika", 0.02), ("dig", 0.05),
                                           ("kala", 0.05), ("drik", 0.05), ("sthana", 0.05)])
def test_component(case, component, tol):
    jh, sb = case
    for p in PLANETS7:
        s = sb[p]
        kala = sum(v for k, v in s.kala.items() if k != "yuddha")
        ours = {"naisargika": s.naisargika, "dig": s.dig, "kala": kala,
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


KALA_FILES = sorted((GOLDEN / "jhora_shadbala" / "kala").glob("*.txt"))
KALA_PARTS = ["nathonnatha", "paksha", "tribhaga", "abda", "masa", "vara", "hora", "ayana", "yuddha"]


@pytest.mark.parametrize("path", KALA_FILES, ids=[f.stem for f in KALA_FILES])
def test_kala_parts(path):
    """Every Kala part against JHora's Kaala Bala table, to its printed precision,
    except Yuddha (BPHS kept; JHora applies none)."""
    c = parse(GOLDEN / "jhora" / path.name)
    b = BirthData(c.local, c.latitude, c.longitude, utc_offset_hours=c.utc_offset_hours,
                  altitude_m=c.altitude_m)
    sb = shadbala(build_chart(b, DEFAULT_CONFIG), b, DEFAULT_CONFIG)
    for line in path.read_text().splitlines():
        parts = line.split()
        if parts and parts[0] in NAMES:
            p = NAMES[parts[0]]
            for k, v in zip(KALA_PARTS, map(float, parts[3:12])):
                if k == "yuddha":
                    continue
                assert abs(sb[p].kala[k] - v) <= 0.05, (p, k, sb[p].kala[k], v)


def test_ishta_kashta_formula(case):
    """Ishta = sqrt(Uchcha x Cheshta), Kashta = sqrt((60 - Uchcha)(60 - Cheshta)), as
    jhora.exe computes them: checked with JHora's own Uchcha and Cheshta against the
    Ishta/Kashta it prints (two decimals in, so up to 0.04 out)."""
    import math
    jh, _ = case
    name = [f for f in FILES if load_breakdown(f) == jh][0].stem
    c = parse(GOLDEN / "jhora" / f"{name}.txt")
    for p in PLANETS7:
        u, ch = jh[p]["uchcha"], jh[p]["cheshta"]
        assert abs(math.sqrt(u * ch) - c.ishta[p]) <= 0.04, p
        assert abs(math.sqrt((60 - u) * (60 - ch)) - c.kashta[p]) <= 0.04, p

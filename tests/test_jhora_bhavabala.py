# SPDX-License-Identifier: AGPL-3.0-or-later
"""Bhava bala against Jagannatha Hora 8.0's Bhava balas table (23 charts,
tests/golden/jhora_bhavabala/, Strengths > Other strengths > Bhava balas)."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent / "golden"))
from jhora_parser import parse  # noqa: E402
from test_jhora_shadbala import load_breakdown  # noqa: E402

from jyotishnet_engine import BirthData, DEFAULT_CONFIG, build_chart  # noqa: E402
from jyotishnet_engine.bhavabala import bhava_bala  # noqa: E402

GOLDEN = Path(__file__).parent / "golden"
FILES = sorted((GOLDEN / "jhora_bhavabala").glob("*.txt"))


def load_table(path: Path) -> list[dict[str, float]]:
    keys = ["total", "rupas", "lord", "dig", "drik"]
    return [dict(zip(keys, map(float, line.split()[1:6])))
            for line in path.read_text().splitlines() if line[:1].isdigit()]


@pytest.fixture(scope="module", params=FILES, ids=[f.stem for f in FILES])
def case(request):
    f = request.param
    c = parse(GOLDEN / "jhora" / f.name)
    b = BirthData(c.local, c.latitude, c.longitude, utc_offset_hours=c.utc_offset_hours,
                  altitude_m=c.altitude_m)
    return f.stem, load_table(f), bhava_bala(build_chart(b, DEFAULT_CONFIG), b, DEFAULT_CONFIG)


def test_dig_and_drik(case):
    _, jh, ours = case
    assert len(jh) == 12
    for j, h in zip(jh, ours):
        assert abs(h.dig - j["dig"]) <= 0.005, (h.house, h.dig, j["dig"])
        # Drik as planetary Drik bala's tolerance; the rest is the Lagna (within 17").
        assert abs(h.drik - j["drik"]) <= 0.05, (h.house, h.drik, j["drik"])


def test_lord_and_total(case):
    # The lord's bala is the lord's Shadbala total in JHora's own breakdown (ours
    # differs from it only by Cheshta and Yuddha, decided differences); the total
    # is the sum of the three parts.
    name, jh, ours = case
    jh_shadbala = load_breakdown(GOLDEN / "jhora_shadbala" / f"{name}.txt")
    for j, h in zip(jh, ours):
        assert abs(j["lord"] - 60 * jh_shadbala[h.lord]["rupas"]) <= 0.31, (h.house, h.lord)
        assert abs(j["total"] - (j["lord"] + j["dig"] + j["drik"])) <= 0.02
        assert abs(h.total - (h.adhipati + h.dig + h.drik)) < 1e-9

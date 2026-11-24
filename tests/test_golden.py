# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Rahul Sathe
"""Regression tests against charts transcribed from Jagannatha Hora (see tests/golden/README.md)."""

import json
from datetime import date, datetime
from pathlib import Path

import pytest

from jyotishnet_engine import BirthData, SchoolConfig, build_chart, vimshottari
from jyotishnet_engine.config import Ayanamsa, NodeType
from jyotishnet_engine.timeutil import jd_to_datetime

CASES = json.loads((Path(__file__).parent / "golden" / "jhora_golden.json").read_text())


def _cfg(c: dict) -> SchoolConfig:
    return SchoolConfig(
        ayanamsa=Ayanamsa(c.get("ayanamsa", "lahiri")),
        node_type=NodeType(c.get("node_type", "mean")),
        true_positions=c.get("true_positions", False),
        dasha_year_days=c.get("dasha_year_days", 365.25),
    )


@pytest.mark.skipif(not CASES, reason="golden set not populated yet")
@pytest.mark.parametrize("case", CASES, ids=[c["id"] for c in CASES] or None)
def test_golden(case):
    b = case["birth"]
    birth = BirthData(datetime.fromisoformat(b["local_datetime"]), b["latitude"], b["longitude"],
                      b.get("tz_name", "Asia/Kolkata"), b.get("utc_offset_hours"))
    cfg = _cfg(case.get("config", {}))
    chart = build_chart(birth, cfg)
    exp = case["expect"]
    tol = case.get("tolerance_deg", 0.01)
    pts = {"La": chart.lagna, **chart.grahas}
    for code, lon in exp.get("longitudes", {}).items():
        assert abs((pts[code].longitude - lon + 180) % 360 - 180) <= tol, code
    for n, signs in exp.get("vargas", {}).items():
        for code, sign in signs.items():
            assert pts[code].vargas[int(n)] == sign, (n, code)
    if "vimshottari_md" in exp:
        mds = vimshottari(chart.grahas["Mo"].longitude, chart.jd_ut, cfg, levels=1)
        for want, got in zip(exp["vimshottari_md"], mds):
            assert got.lord == want["lord"]
            end = jd_to_datetime(got.end_jd).date()
            assert abs((end - date.fromisoformat(want["end"])).days) <= 2

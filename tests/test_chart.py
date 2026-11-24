from datetime import datetime

import pytest

from jyotishnet_engine import BirthData, NodeType, SchoolConfig, build_chart
from jyotishnet_engine.constants import SIGN_LORD

# Reference values cross-checked against PyJHora 5.0.6 (Lahiri, mean nodes).
DELHI_1990 = BirthData(datetime(1990, 1, 15, 6, 30), 28.61, 77.21)


@pytest.fixture(scope="module")
def chart():
    return build_chart(DELHI_1990)


def test_reference_positions(chart):
    assert chart.lagna.sign == 8 and chart.lagna.degree == pytest.approx(18.349, abs=0.01)
    assert chart.grahas["Su"].sign == 9 and chart.grahas["Su"].degree == pytest.approx(0.896, abs=0.01)
    assert chart.grahas["Mo"].sign == 4 and chart.grahas["Mo"].degree == pytest.approx(18.023, abs=0.01)
    assert chart.ayanamsa == pytest.approx(23.718, abs=0.01)


def test_nodes_are_opposite(chart):
    ra, ke = chart.grahas["Ra"].longitude, chart.grahas["Ke"].longitude
    assert (ke - ra) % 360 == pytest.approx(180)


def test_houses_and_lords(chart):
    lg = chart.lagna.sign
    for code, p in chart.grahas.items():
        assert p.house == (p.sign - lg) % 12 + 1
    assert chart.house_lords[1] == SIGN_LORD[lg]


def test_jupiter_retrograde_jan_1990(chart):
    assert chart.grahas["Ju"].retrograde


def test_aspects(chart):
    ju = chart.grahas["Ju"]
    assert len(ju.aspects_houses) == 3
    assert ((ju.house + 6 - 1) % 12) + 1 in ju.aspects_houses   # 7th aspect


def test_special_lagnas_present(chart):
    assert set(chart.special) == {"BL", "HL", "GL", "PP"}
    assert chart.sunrise_jd < chart.jd_ut


def test_config_changes_result():
    a = build_chart(DELHI_1990, SchoolConfig(node_type=NodeType.MEAN))
    b = build_chart(DELHI_1990, SchoolConfig(node_type=NodeType.TRUE))
    assert a.config_key != b.config_key
    assert a.grahas["Ra"].longitude != b.grahas["Ra"].longitude


def test_explicit_offset_matches_zone():
    a = BirthData(datetime(1990, 1, 15, 6, 30), 28.61, 77.21, utc_offset_hours=5.5)
    assert a.jd_ut() == pytest.approx(DELHI_1990.jd_ut())


def test_war_time_is_applied():
    # India used UTC+6:30 during part of World War II; the zone history must apply it.
    war = BirthData(datetime(1943, 6, 1, 12, 0), 22.57, 88.36)
    assert war.utc().hour == 5 and war.utc().minute == 30

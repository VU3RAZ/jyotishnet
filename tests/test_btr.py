# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Rahul Sathe
"""Rectification helpers: event links, double transit, scoring, curve, indicative periods."""

import random
from datetime import date, datetime, timedelta

import pytest

from jyotishnet_engine import BirthData, build_chart
from jyotishnet_engine.timeutil import jd_to_datetime
from jyotishnet_engine.btr import (
    check_events, double_transit, event_rules, fit_curve, indicative_periods, links,
    required_vargas, verdict)

GANDHI = BirthData(datetime(1869, 10, 2, 7, 20), 21.6167, 69.8167, utc_offset_hours=4.654444)
EVENTS = [("marriage", date(1883, 5, 15)), ("child", date(1888, 8, 23)),
          ("career", date(1893, 5, 24)), ("father_death", date(1885, 11, 16))]


def test_rules_load_and_cite():
    rules = event_rules()
    assert len(rules) == 12
    for r in rules.values():
        assert r.source.get("text") and r.status == "draft"
        assert r.varga in required_vargas()
    assert {r.id for r in rules.values() if r.check_only} == {"father_death", "mother_death", "illness"}
    assert not any(r.indicative and r.check_only for r in rules.values())


def test_verdict_thresholds():
    assert [verdict(s) for s in (0, 0.5, 0.75, 1.0, 1.49, 1.5, 2.0)] == \
        ["weak", "weak", "partial", "partial", "partial", "strong", "strong"]


def test_links_reasons():
    c = build_chart(GANDHI, vargas=required_vargas())
    career = event_rules()["career"]
    # Libra Lagna: the 10th is Cancer; the Moon lords it and sits in it.
    mo = links(c, career, "Mo")
    assert "lords D1 house 10" in mo and "in D1 house 10" in mo
    assert links(c, career, "Sa")[-1] == "natural karaka"


class _Fake:
    """Natal chart with only the Lagna sign, for double-transit tests."""
    class lagna:
        sign = 0


def test_double_transit():
    marriage = event_rules()["marriage"]           # D1 7th = Libra for an Aries Lagna
    assert double_transit(_Fake, marriage, {"Ju": 10, "Sa": 6}) == [7]   # Ju 9th aspect, Sa occupies
    assert double_transit(_Fake, marriage, {"Ju": 10, "Sa": 3}) == []    # Saturn misses Libra
    assert double_transit(_Fake, marriage, {"Ju": 0, "Sa": 0}) == [7]    # both aspect by 7th


def test_check_events_scores_are_consistent():
    for c in check_events(GANDHI, EVENTS):
        expected = (1 if c.antar_links else 0) + (0.5 if c.maha_links else 0) \
            + (0.5 if c.double_transit_houses else 0)
        assert c.score == expected and c.verdict == verdict(expected)
        assert c.mahadasha and c.antardasha
    assert [c.check_only for c in check_events(GANDHI, EVENTS)] == [False, False, False, True]


def test_fit_curve():
    f = fit_curve(GANDHI, EVENTS[:2], window_min=5, step_s=60)
    assert [p["offset_s"] for p in f["points"]] == list(range(-300, 301, 60))
    assert f["best"]["score"] == max(p["score"] for p in f["points"])
    assert len(f["helps_decide"]) == 2 and f["max_score"] == 4.0
    # Every candidate scores exactly as check_events does at that shifted time.
    for p in f["points"]:
        shifted = GANDHI.shifted(minutes=p["offset_s"] / 60)
        assert p["score"] == sum(c.score for c in check_events(shifted, EVENTS[:2]))


def test_significance_is_reproducible_and_bounded():
    a = fit_curve(GANDHI, EVENTS, window_min=5, step_s=60, shuffles=100)["significance"]
    b = fit_curve(GANDHI, EVENTS, window_min=5, step_s=60, shuffles=100)["significance"]
    assert a == b                                   # seeded from the birth and the events
    assert a["shuffles"] == 100 and 0 < a["p_value"] <= 1
    assert a["p_value"] == pytest.approx((1 + a["random_at_least"]) / 101, abs=1e-4)
    assert a["verdict"] in ("unlikely by chance", "weak", "no signal")
    assert a["null_dates"][0] > "1869-10-02"        # never before birth
    assert fit_curve(GANDHI, EVENTS, window_min=5, step_s=60, shuffles=0)["significance"] is None


def _random_birth(rnd):
    local = datetime(1945, 1, 1) + timedelta(seconds=rnd.randrange(0, 45 * 365 * 86400))
    return BirthData(local, round(rnd.uniform(8, 32), 3), round(rnd.uniform(68, 90), 3), utc_offset_hours=5.5)


def test_planted_events_are_found_significant():
    """Events dated inside antardashas whose lords both link to them at the recorded
    time: random dates should rarely fit as well."""
    rnd = random.Random(5)
    hits = 0
    for _ in range(6):
        b = _random_birth(rnd)
        jd0 = b.jd_ut()
        ip = indicative_periods(b)
        ev = []
        for t in ["marriage", "child", "career", "relocation"] * 2:
            rows = [r for r in ip[t] if r["end_jd"] - r["start_jd"] > 60 and r["start_jd"] > jd0 + 18 * 365]
            if rows:
                r = rnd.choice(rows)
                ev.append((t, jd_to_datetime(rnd.uniform(r["start_jd"], r["end_jd"])).date()))
        f = fit_curve(b, ev, window_min=10, step_s=60, shuffles=200)
        hits += f["significance"]["p_value"] <= 0.05
    assert hits >= 5


def test_random_events_are_rarely_significant():
    """With dates unrelated to the chart the test should mostly say so (about 5% false alarms)."""
    rnd = random.Random(9)
    types = list(event_rules())
    flagged = 0
    for _ in range(12):
        b = _random_birth(rnd)
        ev = [(rnd.choice(types), (b.local_datetime + timedelta(days=rnd.uniform(18, 60) * 365.25)).date())
              for _ in range(5)]
        flagged += fit_curve(b, ev, window_min=10, step_s=60, shuffles=200)["significance"]["p_value"] <= 0.05
    assert flagged <= 2


def test_indicative_never_death_or_illness():
    ip = indicative_periods(GANDHI)
    assert set(ip) == {"marriage", "child", "career", "relocation"}
    for rows in ip.values():
        for r in rows:
            assert r["maha_links"] and r["antar_links"] and r["start_jd"] < r["end_jd"]

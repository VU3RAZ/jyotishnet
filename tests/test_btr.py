# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Rahul Sathe
"""Rectification helpers: event links, double transit, scoring, curve, indicative periods."""

import random
from datetime import date, datetime, timedelta

import pytest

from jyotishnet_engine import DEFAULT_CONFIG, BirthData, build_chart
from jyotishnet_engine.constants import SIGN_LORD
from jyotishnet_engine.timeutil import jd_to_datetime
from jyotishnet_engine.btr import (
    RULE_SETS, antardasha_quality, check_events, classical_rules, double_transit, event_rules,
    fit_curve, indicative_periods, links, required_vargas, significator_reasons, verdict)

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


def test_check_events_scores_are_consistent_modern():
    for c in check_events(GANDHI, EVENTS, rule_set="modern"):
        expected = (1 if c.antar_links else 0) + (0.5 if c.maha_links else 0) \
            + (0.5 if c.double_transit_houses else 0)
        assert c.score == expected and c.verdict == verdict(expected)
        assert c.mahadasha and c.antardasha and c.rule_set == "modern" and c.quality is None
    assert [c.check_only for c in check_events(GANDHI, EVENTS)] == [False, False, False, True]


def test_classical_rules_cite_every_condition():
    cr = classical_rules()
    assert set(cr) == set(event_rules())
    for r in cr.values():
        assert r.status == "draft" and r.polarity in ("good", "adverse")
        assert all(c.get("cite") for c in r.significators)
        assert not r.transit or r.transit.get("cite")
        if not r.significators:
            assert r.notes                       # says why there is no classical rule
    # Death and illness are scored on the period's quality only, never by a timing rule.
    for k in ("father_death", "mother_death", "illness"):
        assert cr[k].polarity == "adverse" and not cr[k].significators and not cr[k].transit


def test_significators_gandhi():
    # Libra Lagna: 7th Aries (Mars), 5th Aquarius (Saturn), 1st Libra (Venus).
    c = build_chart(GANDHI, vargas=required_vargas())
    cr = classical_rules()
    assert any("lords house 7" in r for r in significator_reasons(c, cr["marriage"], "Ma"))
    assert any(r.startswith("is Venus") for r in significator_reasons(c, cr["marriage"], "Ve"))
    child = {g for g in ("Su", "Mo", "Ma", "Me", "Ju", "Ve", "Sa", "Ra", "Ke")
             if significator_reasons(c, cr["child"], g)}
    assert {"Ve", "Sa", "Ma", "Ju"} <= child     # lords of 1, 5, 7 and Jupiter (PD 12.25)


def test_antardasha_quality_is_good_bad_or_mixed():
    c = build_chart(GANDHI, vargas=required_vargas())
    for m in ("Su", "Ve", "Sa"):
        for a in ("Su", "Mo", "Ma", "Me", "Ju", "Ve", "Sa", "Ra", "Ke"):
            q, good, bad = antardasha_quality(c, m, a)
            assert q == ("good" if good and not bad else "bad" if bad and not good else "mixed")
            assert all("(" in r for r in good + bad)          # every reason cites its verse


def test_check_events_scores_are_consistent_classical():
    for c in check_events(GANDHI, EVENTS):
        rule = classical_rules()[c.event]
        want, other = ("good", "bad") if rule.polarity == "good" else ("bad", "good")
        q = 0.5 if c.quality == want else 0.0 if c.quality == other else 0.25
        expected = (1 if c.antar_links else 0) + (0.5 if c.maha_links else 0) + q + (0.5 if c.transit else 0)
        assert c.rule_set == "classical" and c.score == expected
        assert c.max_score == rule.max_score and c.verdict == verdict(expected, c.max_score)


@pytest.mark.parametrize("rule_set", RULE_SETS)
def test_fit_curve(rule_set):
    f = fit_curve(GANDHI, EVENTS[:2], window_min=5, step_s=60, rule_set=rule_set)
    assert [p["offset_s"] for p in f["points"]] == list(range(-300, 301, 60))
    assert f["best"]["score"] == max(p["score"] for p in f["points"])
    assert len(f["helps_decide"]) == 2
    assert f["max_score"] == (4.0 if rule_set == "modern" else 2.5 + 2.5)
    # Every candidate scores exactly as check_events does at that shifted time.
    for p in f["points"]:
        shifted = GANDHI.shifted(minutes=p["offset_s"] / 60)
        assert p["score"] == sum(c.score for c in check_events(shifted, EVENTS[:2], rule_set=rule_set))


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
    tried = 0
    for _ in range(30):     # about 90% are found (118 charts measured, 28 Nov 2026)
        b = _random_birth(rnd)
        jd0 = b.jd_ut()
        ip = indicative_periods(b)
        ev = []
        for t in ["marriage", "child", "career", "relocation"] * 2:
            rows = [r for r in ip[t] if r["end_jd"] - r["start_jd"] > 60 and r["start_jd"] > jd0 + 18 * 365]
            if rows:
                r = rnd.choice(rows)
                ev.append((t, jd_to_datetime(rnd.uniform(r["start_jd"], r["end_jd"])).date()))
        if not ev:
            continue
        tried += 1
        f = fit_curve(b, ev, window_min=10, step_s=60, shuffles=200)
        hits += f["significance"]["p_value"] <= 0.05
    assert hits >= 0.8 * tried


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
    ip = indicative_periods(GANDHI, rule_set="modern")
    assert set(ip) == {"marriage", "child", "career", "relocation"}
    for rows in ip.values():
        for r in rows:
            assert r["maha_links"] and r["antar_links"] and r["start_jd"] < r["end_jd"]
    c = build_chart(GANDHI, vargas=required_vargas())
    ip = indicative_periods(GANDHI)
    assert set(ip) == {"marriage", "child", "career", "relocation"}
    for rows in ip.values():
        for r in rows:
            assert r["antar_links"] and r["quality_reasons"]
            assert antardasha_quality(c, r["mahadasha"], r["antardasha"])[0] == "good"


@pytest.mark.parametrize("rule_set", RULE_SETS)
def test_indicative_periods_start_at_16_by_default(rule_set):
    jd0 = GANDHI.jd_ut()
    ip = indicative_periods(GANDHI, rule_set=rule_set)
    starts = [r["start_jd"] for rows in ip.values() for r in rows]
    assert starts and min(starts) >= jd0 + 16 * 365.25 - 1e-6
    young = indicative_periods(GANDHI, rule_set=rule_set, min_age_years=0)
    assert sum(map(len, young.values())) > sum(map(len, ip.values()))
    assert min(r["start_jd"] for rows in young.values() for r in rows) < jd0 + 16 * 365.25


def test_pd_10_14_strongest_planet_gives_marriage_and_gates_the_transit():
    """Phaladeepika 10.14: the strongest of the lords of the 7th lord's sign and navamsa,
    Venus and the Moon gives marriage; Jupiter's transit counts only in its dasha."""
    from jyotishnet_engine.btr import _from_chart, strengths, strongest_planet
    rnd = random.Random(3)
    cr = classical_rules()["marriage"]
    gated = 0
    for _ in range(10):
        b = _random_birth(rnd)
        c = build_chart(b, vargas=required_vargas())
        st = strengths(c, b)
        best = strongest_planet(c, cr, st)
        lord7 = c.grahas[c.house_lords[7]]
        four = {SIGN_LORD[lord7.sign], SIGN_LORD[lord7.vargas[9]], "Ve", "Mo"}
        assert best in four and st[best] == max(st[q] for q in four)
        assert any("PD 10.14" in r for r in significator_reasons(c, cr, best, st))
        cand = _from_chart(c, 0, DEFAULT_CONFIG, "classical", b)
        assert cand.gate["marriage"] == best and cand.gate["child"] is None
        for d in range(0, 60 * 365, 211):   # every check agrees with the gate
            jd = b.jd_ut() + 18 * 365.25 + d
            [chk] = check_events(b, [("marriage", jd_to_datetime(jd).date())], chart=c)
            if chk.transit:
                assert best in (chk.mahadasha, chk.antardasha) and "dasha of" in chk.transit[0]
            gated += bool(chk.transit)
    assert gated

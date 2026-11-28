# SPDX-License-Identifier: AGPL-3.0-or-later
"""Rule-based readings (M3.4): every sentence traceable to engine facts; safety filter."""

import sys
from dataclasses import replace
from datetime import date, datetime
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent / "golden"))
from jhora_parser import load_all  # noqa: E402

from jyotishnet_engine import BirthData  # noqa: E402
from jyotishnet_engine.readings import (Sheet, reading, safety, topics, verify,  # noqa: E402
                                        write)

PVR = BirthData(datetime(1970, 4, 4, 17, 50, 40), 16.1667, 81.1333, utc_offset_hours=5.5)
CHARTS = [c for c in load_all() if not c.name.startswith("edge_3")][:12]


def test_topics_cite_sources_and_stay_draft():
    ts = topics()
    assert len(ts) >= 15
    for t in ts.values():
        assert t.source.get("text") and t.source.get("section") and t.status == "draft", t.id
        assert all(1 <= h <= 12 for h in t.houses)


@pytest.mark.parametrize("c", CHARTS, ids=lambda c: c.name)
def test_every_sentence_is_grounded(c):
    b = BirthData(c.local, c.latitude, c.longitude, utc_offset_hours=c.utc_offset_hours,
                  altitude_m=c.altitude_m)
    for tid, t in topics().items():
        r = reading(b, tid, at=date(c.local.year + 40, 6, 1), stability_min=0)
        ids = {f.id for f in r.facts}
        assert r.factors, tid
        assert not [d for d in r.dropped if d["reason"].startswith("verifier")], (tid, r.dropped)
        if t.technical_only:
            assert not r.sentences
            continue
        assert len(r.sentences) == len(r.factors)
        for s in r.sentences:
            assert s.cites and set(s.cites) <= ids, s
            assert "classical texts" in s.text            # traditional-interpretation framing
            assert "the native" in s.text and "supporting" not in s.text and "obstructing" not in s.text
            assert safety(s.text) is None
        scores = [f.score for f in r.factors]
        assert scores == sorted(scores, reverse=True)


def _sheet_and_sentence(topic="career"):
    r = reading(PVR, topic, at=date(2026, 11, 25), stability_min=0)
    from jyotishnet_engine import DEFAULT_CONFIG, build_chart
    t = topics()[topic]
    vargas = [1] + ([t.varga] if t.varga else [])
    sh = Sheet(build_chart(PVR, DEFAULT_CONFIG, vargas), PVR, DEFAULT_CONFIG, vargas)
    from jyotishnet_engine.readings import rank
    factors = rank(sh, t, None, set())
    by_key = {f.key: f for f in factors}
    lord = next(f for f in factors if f.role == "lord")
    return sh, t, by_key, write(sh, t, lord), r


def test_verifier_accepts_the_template_sentence():
    sh, t, by_key, s, _ = _sheet_and_sentence()
    assert verify(s, sh, None, t, by_key) is None


def test_verifier_rejects_a_false_claim():
    sh, t, by_key, s, _ = _sheet_and_sentence()
    bad = [dict(c) for c in s.claims]
    for c in bad:
        if c["kind"] == "placement":
            c["sign"] = (c["sign"] + 1) % 12
    assert "not backed" in verify(replace(s, claims=bad), sh, None, t, by_key)


def test_verifier_rejects_unclaimed_names_and_missing_citations():
    sh, t, by_key, s, _ = _sheet_and_sentence()
    assert "without a claim" in verify(replace(s, text=s.text + " Rahu agrees."), sh, None, t, by_key)
    assert "without a claim" in verify(replace(s, text=s.text + " So does Capricorn."), sh, None, t, by_key)
    assert verify(replace(s, cites=[]), sh, None, t, by_key) == "cites no fact"
    assert "unknown facts" in verify(replace(s, cites=s.cites + ["made.up"]), sh, None, t, by_key)
    flipped = {"supports": "obstructs", "obstructs": "supports", "mixed": "supports"}
    claims = [dict(c, direction=flipped[c["direction"]]) if c["kind"] == "direction" else c for c in s.claims]
    assert "not true of the chart" in verify(replace(s, claims=claims), sh, None, t, by_key)


@pytest.mark.parametrize("text", [
    "Classical texts associate this with the birth of a son.",
    "The 8th lord shows longevity.",
    "This period may bring an accident.",
    "Pregnancy is indicated.",
    "Maraka dasha runs.",
])
def test_safety_filter_blocks(text):
    assert safety(text)


def test_health_is_technical_only_with_disclaimer():
    r = reading(PVR, "health", stability_min=0)
    assert r.factors and not r.sentences
    assert any("not medical advice" in d for d in r.disclaimers)
    assert reading(PVR, "earned_income", stability_min=0).disclaimers
    assert any("sex of a child is never predicted" in n for n in reading(PVR, "children", stability_min=0).notes)


def test_current_period_scope_adds_linked_dasha_lords():
    r = reading(PVR, "career", at=date(2026, 11, 25), stability_min=0)
    dasha = [f for f in r.factors if f.role.startswith("dasha")]
    assert dasha and any(f.id.startswith("dasha.L1") for f in r.facts)
    natal = reading(PVR, "career", stability_min=0)
    assert not [f for f in natal.factors if f.role.startswith("dasha")]


def test_unstable_lagna_marks_factors_uncertain():
    # PVR's D10 Lagna changes sign about 0.1 min from his recorded time.
    r = reading(PVR, "career", stability_min=5)
    assert any("D10 Lagna changes sign" in n for n in r.notes)
    assert all(f.uncertain for f in r.factors if f.varga == 10)
    assert any(s.uncertain for s in r.sentences)


def test_unknown_topic():
    with pytest.raises(ValueError):
        reading(PVR, "lottery")


def test_house_rules_cite_every_entry():
    for t in topics().values():
        for h, rules in t.house_rules.items():
            assert h in t.houses, (t.id, h)
            for kind, entries in rules.items():
                assert kind in ("occupant", "aspect", "lord"), (t.id, kind)
                for key, e in entries.items():
                    assert e["reads"] in ("supports", "obstructs", "mixed") and e["cite"], (t.id, h, key)


@pytest.mark.parametrize("c", CHARTS, ids=lambda c: c.name)
def test_disputes_follow_the_6th_house_rules(c):
    """Planets in the 6th read as Phaladeepika ch. 8 says; the 6th lord in a dusthana
    (Harsha) and malefic aspects favour the native, never against them."""
    b = BirthData(c.local, c.latitude, c.longitude, utc_offset_hours=c.utc_offset_hours,
                  altitude_m=c.altitude_m)
    r = reading(b, "disputes", stability_min=0, limit=100)
    occ = topics()["disputes"].house_rules[6]["occupant"]
    for f in r.factors:
        if f.key.startswith(("occupant.D1.H6.", "occupant.D6.H6.")):
            assert f.direction == occ[f.subject]["reads"], f
        if f.key == "lord.D1.H6" and any("dusthana" in x for x in f.reasons):
            assert "Harsha" in "; ".join(f.reasons)
        if f.key.startswith("aspect.D1.H6.") and "natural malefic" in f.reasons:
            assert f.direction == "supports", f
    assert r.topic["labels"]["supports"] == "favours the native"
    assert all("the native in matters of enemies, disputes and competition" in s.text for s in r.sentences)


def test_foreign_12th_occupants_support_travel_either_way():
    for c in CHARTS:
        b = BirthData(c.local, c.latitude, c.longitude, utc_offset_hours=c.utc_offset_hours,
                      altitude_m=c.altitude_m)
        for f in reading(b, "foreign", stability_min=0, limit=100).factors:
            if f.key.startswith(("occupant.D1.H12.", "aspect.D1.H12.")):
                assert f.direction == "supports" and "BPHS 23.1" in f.reasons[-1], f


def test_topics_without_house_rules_keep_the_general_rule():
    r = reading(PVR, "siblings", stability_min=0, limit=100)
    assert not topics()["siblings"].house_rules
    assert not [f for f in r.factors if any("Phaladeepika" in x or "BPHS" in x for x in f.reasons)]
    assert r.topic["labels"] == {"supports": "favours the native", "obstructs": "against the native",
                                 "mixed": "mixed"}

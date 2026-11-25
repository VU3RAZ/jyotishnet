# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Rahul Sathe
"""Yoga rule engine: synthetic charts built from signs (0 = Aries ... 11 = Pisces)."""

from pathlib import Path

import pytest

from jyotishnet_engine.yogas import Context, find_yogas, load_rules

RULES = load_rules()
IDS = {r.id for r in RULES}

# A spread-out base chart, Aries lagna: Su Ta, Mo Ge, Ma Le, Me Ta, Ju Sg, Ve Ar, Sa Aq, Ra Cp.
BASE = {"Su": 1, "Mo": 2, "Ma": 4, "Me": 1, "Ju": 8, "Ve": 0, "Sa": 10, "Ra": 9}


def yogas(lagna: int = 0, **moves) -> dict:
    signs = {**BASE, **moves}
    return {y.id: y for y in find_yogas(Context.from_signs(lagna, signs), RULES)}


def present(lagna=0, **moves) -> set[str]:
    return {k for k, y in yogas(lagna, **moves).items() if not y.cancelled}


def test_rules_load_with_sources():
    assert len(RULES) >= 50
    for r in RULES:
        assert r.source.get("text") and r.source.get("section"), r.id
        assert r.status in {"draft", "reviewed"}, r.id


def test_rule_files_are_packaged():
    import jyotishnet_engine
    folder = Path(jyotishnet_engine.__file__).parent / "rules" / "yogas"
    assert sorted(p.name for p in folder.glob("*.yaml"))


def test_unknown_predicate_rejected(tmp_path):
    (tmp_path / "x.yaml").write_text(
        "- {id: x, name: X, group: G, summary: s, source: {text: t, section: s}, when: {nope: {}}}\n")
    rules = load_rules(tmp_path)
    with pytest.raises(Exception):
        find_yogas(Context.from_signs(0, BASE), rules)


def test_duplicate_ids_rejected(tmp_path):
    row = "- {id: x, name: X, group: G, summary: s, source: {text: t, section: s}, when: {sign_count: {count: 1}}}\n"
    (tmp_path / "a.yaml").write_text(row)
    (tmp_path / "b.yaml").write_text(row)
    with pytest.raises(ValueError):
        load_rules(tmp_path)


# --- Pancha Mahapurusha ---------------------------------------------------

@pytest.mark.parametrize("planet,sign,yoga", [
    ("Ma", 9, "ruchaka"),      # Mars exalted in Capricorn, 10th from Aries
    ("Me", 5, "bhadra"),       # Mercury exalted in Virgo, 4th from Gemini lagna
    ("Ju", 3, "hamsa"),        # Jupiter exalted in Cancer, 4th from Aries
    ("Ve", 6, "malavya"),      # Venus own sign Libra, 7th from Aries
    ("Sa", 9, "sasa"),         # Saturn own sign Capricorn, 10th from Aries
])
def test_mahapurusha(planet, sign, yoga):
    lagna = 2 if planet == "Me" else 0
    assert yoga in present(lagna, **{planet: sign})


def test_mahapurusha_needs_kendra():
    assert "hamsa" not in present(Ju=8)          # Jupiter own sign but 9th house


# --- Chandra and Surya ----------------------------------------------------

def test_sunapha_anapha_durudhara_kemadruma():
    # Moon in Cancer. Planets in Leo (2nd) only -> Sunapha.
    clear = dict(Su=0, Mo=3, Ma=4, Me=0, Ju=0, Ve=0, Sa=0, Ra=6)
    assert "sunapha" in present(**clear)
    assert "anapha" in present(**{**clear, "Ma": 2})          # Gemini = 12th
    assert "durudhara" in present(**{**clear, "Ve": 2})        # both sides
    ys = yogas(**{**clear, "Ma": 0})                           # nobody beside the Moon
    assert ys["kemadruma"].present
    assert ys["kemadruma"].cancelled                           # planets in kendra from lagna
    # The Sun beside the Moon does not count.
    assert "sunapha" not in present(**{**clear, "Ma": 0, "Su": 4})


def test_kemadruma_uncancelled():
    # Lagna Aries, Moon Taurus; all others in Libra (7th, a kendra) would cancel,
    # so put them in Virgo (6th from lagna, 5th from Moon).
    ys = yogas(Su=5, Mo=1, Ma=5, Me=5, Ju=5, Ve=5, Sa=5, Ra=8)
    assert ys["kemadruma"].present and not ys["kemadruma"].cancelled


def test_gajakesari_and_shakata():
    assert "gajakesari" in present(Mo=2, Ju=11)                # Pisces is 10th from Gemini
    assert "gajakesari" not in present(Mo=2, Ju=3)
    ys = yogas(Mo=6, Ju=0)                                      # Moon 7th from Jupiter: no Shakata
    assert "shakata" not in ys
    ys = yogas(Mo=5, Ju=0)                                      # Moon 6th from Jupiter, 6th house
    assert ys["shakata"].present and not ys["shakata"].cancelled
    ys = yogas(Mo=3, Ju=10)                                     # 6th from Ju, but 4th house: cancelled
    assert ys["shakata"].cancelled


def test_adhi():
    assert "adhi" in present(Mo=0, Me=5, Ju=6, Ve=7)
    assert "adhi" not in present(Mo=0, Me=5, Ju=6, Ve=8)


def test_vesi_vosi_ubhayachari():
    base = dict(Su=4, Mo=0, Ma=0, Me=4, Ju=0, Ve=0, Sa=0, Ra=6)
    assert "vesi" in present(**{**base, "Ma": 5})
    assert "vosi" in present(**{**base, "Ma": 3})
    assert "ubhayachari" in present(**{**base, "Ma": 3, "Ve": 5})
    assert "vesi" not in present(**{**base, "Mo": 5})          # the Moon doesn't count


def test_budha_aditya():
    assert "budha_aditya" in present()                          # Su and Me both in Taurus


# --- Raja, Viparita, Parivartana ------------------------------------------

def test_raja_and_dharma_karmadhipati():
    # Aries lagna: 9th lord Ju, 10th lord Sa. Put them together in Leo.
    ys = yogas(Ju=4, Sa=4)
    assert ys["dharma_karmadhipati"].present
    assert any("conjunction" in e for e in ys["dharma_karmadhipati"].evidence)
    assert "raja_kendra_trikona" in ys


def test_yogakaraka():
    assert "yogakaraka" in present(lagna=1)                      # Saturn for Taurus lagna
    assert "yogakaraka" not in present(lagna=2)                  # none for Gemini


def test_viparita():
    # Aries lagna: 6th lord Me, 8th lord Ma, 12th lord Ju.
    assert "harsha" in present(Me=11)
    assert "sarala" in present(Ma=5)
    assert "vimala" in present(Ju=7)


def test_parivartana_kinds():
    # Aries lagna. Ma in Aq and Sa in Sc: the 8th and 11th signs exchanged -> Dainya.
    assert "dainya_parivartana" in present(Ma=10, Sa=7)
    # Ma in Cp and Sa in Ar exchange the 1st and 10th signs -> Maha, not Dainya.
    assert "maha_parivartana" in present(Ma=9, Sa=0)
    assert "dainya_parivartana" not in present(Ma=9, Sa=0)
    # Su (5th lord) in Cn, Mo (4th lord) in Le -> Maha.
    assert "maha_parivartana" in present(Su=3, Mo=4)
    # Ve in Ge and Me in Ta exchange the 2nd and 3rd signs -> Khala.
    assert "khala_parivartana" in present(Ve=2, Me=1)


def test_neecha_bhanga():
    # Jupiter debilitated in Capricorn; Saturn (lord of Cp) in a kendra (Cancer, 4th).
    ys = yogas(Ju=9, Sa=3)
    assert ys["neecha_bhanga"].present
    # Saturn in the 11th, Mars (exaltation lord) in the 5th, Moon in Virgo: no cancellation.
    # The Moon as exaltation lord is not "in a kendra from itself".
    assert "neecha_bhanga" not in yogas(Ju=9, Sa=10, Mo=5)


# --- Nabhasa ---------------------------------------------------------------

def test_sankhya_counts_exactly_one():
    for n, yid in [(7, "vallaki"), (6, "damini"), (5, "pasha"), (4, "kedara"),
                   (3, "shoola"), (2, "yuga"), (1, "gola")]:
        signs = {p: i % n for i, p in enumerate(["Su", "Mo", "Ma", "Me", "Ju", "Ve", "Sa"])}
        got = {k for k in present(**signs, Ra=11) if k in
               {"vallaki", "damini", "pasha", "kedara", "shoola", "yuga", "gola"}}
        assert got == {yid}


def test_ashraya_and_shapes():
    movable = dict(Su=0, Mo=3, Ma=6, Me=9, Ju=0, Ve=3, Sa=6, Ra=1)
    ys = present(**movable)
    assert "rajju" in ys and "kamala" in ys and "musala" not in ys
    assert "gada" in present(Su=0, Mo=3, Ma=0, Me=3, Ju=0, Ve=3, Sa=0)
    assert "shakata_akriti" in present(Su=0, Mo=6, Ma=0, Me=6, Ju=0, Ve=6, Sa=0)
    assert "shringataka" in present(Su=0, Mo=4, Ma=8, Me=0, Ju=4, Ve=8, Sa=0)
    assert "hala" in present(Su=1, Mo=5, Ma=9, Me=1, Ju=5, Ve=9, Sa=1)
    assert "vapi" in present(Su=1, Mo=4, Ma=1, Me=4, Ju=1, Ve=4, Sa=1)


def test_mala_and_sarpa():
    assert "mala" in present(Me=0, Ju=3, Ve=6)
    assert "sarpa" in present(Su=0, Ma=3, Sa=6, Me=1, Ju=1, Ve=1, Mo=1, Ra=1)


# --- Others ---------------------------------------------------------------

def test_amala_only_benefics():
    assert "amala" in present(Ju=9, Mo=5, Ra=2)                 # Ju in 10th, nothing malefic
    assert "amala" not in present(Ju=9, Sa=9, Mo=5, Ra=2)       # Saturn there too


def test_kartari():
    assert "papa_kartari_lagna" in present(Ma=1, Sa=11)
    assert "shubha_kartari_lagna" in present(Ju=1, Ve=11, Me=11, Su=4, Ma=4, Sa=4)


def test_every_rule_fires_on_some_chart():
    """Smoke test: random sign layouts exercise every rule at least once."""
    import random
    rng = random.Random(7)
    seen = set()
    for _ in range(4000):
        signs = {p: rng.randrange(12) for p in ["Su", "Mo", "Ma", "Me", "Ju", "Ve", "Sa", "Ra"]}
        seen |= {y.id for y in find_yogas(Context.from_signs(rng.randrange(12), signs), RULES)}
    rare = {"gola", "yuga", "nala", "musala", "rajju", "gada", "shakata_akriti", "vihaga",
            "shringataka", "hala", "kamala", "vapi", "mala", "sarpa", "shoola"}
    assert IDS - seen <= rare


# --- M2.9: strength conditions (Aries lagna: Lagna lord Mars, 9th lord Jupiter in Sg,
# 4th lord Moon in Ge, 7th from Jupiter)

def test_lakshmi_and_kahala_need_a_strong_lagna_lord():
    assert {"lakshmi", "kahala"} <= present()                       # Mars in Leo, 5th: trikona
    assert {"lakshmi", "kahala"} <= present(Ma=7)                   # own sign (8th house)
    assert {"lakshmi", "kahala"} <= present(Ma=9)                   # exalted
    assert not {"lakshmi", "kahala"} & present(Ma=2)                # 3rd, Mercury's sign
    assert not {"lakshmi", "kahala"} & present(Ma=3)                # 4th but debilitated
    y = yogas()["lakshmi"]
    assert any("1st lord (Ma) strong: in the 5th house" in e for e in y.evidence)


def _with(options, **moves):
    from jyotishnet_engine.yogas import YogaOptions
    ctx = Context.from_signs(0, {**BASE, **moves}, options=YogaOptions(**options))
    return {y.id for y in find_yogas(ctx, RULES) if not y.cancelled}


def test_gajakesari_phaladeepika_conditions():
    pd = {"gajakesari": "phaladeepika"}
    assert "gajakesari" in present()                                 # BPHS: Ju 7th from Mo
    assert "gajakesari" not in _with(pd)                             # no benefic on Jupiter
    assert "gajakesari" in _with(pd, Ve=2)                           # Venus in Ge aspects Sg
    assert "gajakesari" in _with(pd, Me=8)                           # Mercury with Jupiter
    assert "gajakesari" not in _with(pd, Ve=2, Su=8)                 # combust (same degree)
    # Jupiter in Ta (Venus's sign, an enemy), Moon in Le (Ta is the 10th), Mercury with it
    assert "gajakesari" in _with({}, Ju=1, Mo=4)
    assert "gajakesari" not in _with(pd, Ju=1, Mo=4, Me=1)
    assert "gajakesari" not in _with(pd, Ju=9, Mo=0, Ve=9)           # debilitated in Cp


def test_yoga_options_validated():
    from jyotishnet_engine.yogas import YogaOptions
    with pytest.raises(ValueError):
        YogaOptions(strong_lord="vague")
    with pytest.raises(ValueError):
        YogaOptions(gajakesari="x")


def test_strong_lord_by_shadbala():
    from datetime import datetime
    from jyotishnet_engine import BirthData, DEFAULT_CONFIG, build_chart
    from jyotishnet_engine.yogas import YogaOptions
    birth = BirthData(datetime(1990, 1, 15, 6, 30), 28.61, 77.21, "Asia/Kolkata")
    c = build_chart(birth, DEFAULT_CONFIG, [1])
    opts = YogaOptions(strong_lord="shadbala")
    with pytest.raises(ValueError):
        find_yogas(c, options=opts)
    ys = {y.id: y for y in find_yogas(c, include_absent=True, options=opts, birth=birth)}
    assert any("Shadbala" in e and "required rupas" in e for e in ys["lakshmi"].evidence)

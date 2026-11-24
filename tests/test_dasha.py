# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Rahul Sathe
import pytest

from jyotishnet_engine import SchoolConfig, running, vimshottari, yogini
from jyotishnet_engine.constants import NAKSHATRA_SPAN
from jyotishnet_engine.nakshatra import nakshatra_of

# Fixed 365.25-day years keep these rule checks exact; the solar year is tested
# against Jagannatha Hora in test_jhora_golden.py.
DEFAULT_CONFIG = SchoolConfig(dasha_year_mode="fixed", dasha_year_days=365.25)
YEAR = DEFAULT_CONFIG.dasha_year_days
BIRTH = 2447906.5  # arbitrary Julian day


def test_nakshatra_edges():
    assert (nakshatra_of(0).name, nakshatra_of(0).pada, nakshatra_of(0).lord) == ("Ashwini", 1, "Ke")
    last = nakshatra_of(359.999)
    assert (last.name, last.pada, last.lord) == ("Revati", 4, "Me")


def test_vimshottari_cycle_is_120_years():
    mds = vimshottari(0.0, BIRTH, DEFAULT_CONFIG, levels=1)
    nine = mds[:9]
    assert nine[0].lord == "Ke"
    assert nine[0].start_jd == pytest.approx(BIRTH)          # Moon at 0 deg: full Ketu period
    assert nine[-1].end_jd - nine[0].start_jd == pytest.approx(120 * YEAR)


def test_vimshottari_balance():
    moon = NAKSHATRA_SPAN * 0.25                              # a quarter through Ashwini
    md = vimshottari(moon, BIRTH, DEFAULT_CONFIG, levels=1)[0]
    assert md.end_jd - BIRTH == pytest.approx(0.75 * 7 * YEAR)


def test_antardashas_fill_the_mahadasha():
    md = vimshottari(123.4, BIRTH, DEFAULT_CONFIG, levels=3)[0]
    assert md.children[0].lord == md.lord
    assert md.children[0].start_jd == pytest.approx(md.start_jd)
    assert md.children[-1].end_jd == pytest.approx(md.end_jd)
    ad = md.children[3]
    assert ad.children[-1].end_jd == pytest.approx(ad.end_jd)


def test_running_chain():
    periods = vimshottari(200.0, BIRTH, DEFAULT_CONFIG, levels=3)
    chain = running(periods, BIRTH + 30 * YEAR)
    assert [p.level for p in chain] == [1, 2, 3]


def test_yogini_start():
    # Ashwini (nakshatra 1): (1 + 3) mod 8 = 4 -> Bhramari.
    first = yogini(0.0, BIRTH, DEFAULT_CONFIG)[0]
    assert first.name == "Bhramari" and first.lord == "Ma"
    cycle = yogini(0.0, BIRTH, DEFAULT_CONFIG)[:8]
    assert cycle[-1].end_jd - cycle[0].start_jd == pytest.approx(36 * YEAR)


# --- Ashtottari --------------------------------------------------------------

def test_ashtottari_structure():
    from jyotishnet_engine.constants import ASHTOTTARI_NAKSHATRAS, ASHTOTTARI_YEARS
    from jyotishnet_engine.dasha import ashtottari
    assert sum(ASHTOTTARI_YEARS.values()) == 108
    assert sum(ASHTOTTARI_NAKSHATRAS.values()) == 27
    ps = ashtottari(100.0, 2451545.0, DEFAULT_CONFIG, levels=2)
    seq = [p.lord for p in ps[:8]]
    assert seq == (["Su", "Mo", "Ma", "Me", "Sa", "Ju", "Ra", "Ve"] * 2)[
        ["Su", "Mo", "Ma", "Me", "Sa", "Ju", "Ra", "Ve"].index(seq[0]):][:8]
    for md in ps:
        assert md.children[0].lord == md.lord
        span = md.end_years - md.start_years
        assert sum(c.end_years - c.start_years for c in md.children) == pytest.approx(span)


@pytest.mark.parametrize("moon,lord,frac", [
    (5 * 360 / 27, "Su", 0.0),                  # start of Ardra
    (5 * 360 / 27 + 2 * 360 / 27, "Su", 0.5),   # halfway through Ardra..Ashlesha
    (0.0, "Ra", 0.5),                           # Ashwini: 3rd of Rahu's 4 (UBha, Rev, Ash, Bha)
    (2 * 360 / 27, "Ve", 0.0),                  # Krittika starts Venus
])
def test_ashtottari_balance(moon, lord, frac):
    from jyotishnet_engine.constants import ASHTOTTARI_YEARS
    from jyotishnet_engine.dasha import ashtottari
    first = ashtottari(moon, 2451545.0, DEFAULT_CONFIG, levels=1)[0]
    assert first.lord == lord
    assert -first.start_years == pytest.approx(frac * ASHTOTTARI_YEARS[lord])


def test_ashtottari_applicability():
    from jyotishnet_engine.dasha import ashtottari_applicable
    # Aries lagna, Mars (lagna lord) in Cancer; Rahu in Libra = 4th from Mars -> applies.
    assert ashtottari_applicable(0, {"Ma": 3, "Ra": 6})
    # Rahu in the Lagna never applies.
    assert not ashtottari_applicable(0, {"Ma": 3, "Ra": 0})
    # Rahu 3rd from the lagna lord -> no.
    assert not ashtottari_applicable(0, {"Ma": 3, "Ra": 5})

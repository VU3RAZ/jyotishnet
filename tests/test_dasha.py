import pytest

from jyotishnet_engine import DEFAULT_CONFIG, running, vimshottari, yogini
from jyotishnet_engine.constants import NAKSHATRA_SPAN
from jyotishnet_engine.nakshatra import nakshatra_of

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

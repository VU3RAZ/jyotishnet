# SPDX-License-Identifier: AGPL-3.0-or-later
from datetime import datetime, timezone

from jyotishnet_engine import DEFAULT_CONFIG
from jyotishnet_engine.timeutil import datetime_to_jd, jd_to_datetime
from jyotishnet_engine.transits import (house_from, kakshya, sade_sati_phase, saturn_spells,
                                        sign_entry, tara)


def test_kakshya_parts():
    assert kakshya(0.1) == "Sa" and kakshya(3.8) == "Ju" and kakshya(29.9) == "La"
    assert kakshya(30 + 7.85) == "Ma"


def test_tara_cycle():
    assert tara(0.5, 0.6) == (1, "Janma")            # same nakshatra
    assert tara(0.5, 13.4) == (2, "Sampat")
    assert tara(0.5, 9 * 13.3334 + 1) == (1, "Janma")   # 10th nakshatra
    assert tara(350.0, 1.0)[0] == 2                   # Revati -> Ashwini wraps


def test_houses_and_phases():
    assert house_from(0, 11) == 2
    assert sade_sati_phase(10, 11) == "rising"
    assert sade_sati_phase(11, 11) == "peak" and sade_sati_phase(0, 11) == "setting"
    assert sade_sati_phase(2, 11) == "kantaka" and sade_sati_phase(6, 11) == "ashtama"
    assert sade_sati_phase(5, 11) is None


def test_saturn_ingresses_lahiri():
    # Saturn (Lahiri) entered Aquarius on 29 Apr 2022, went back into Capricorn on
    # 12 Jul 2022, re-entered Aquarius on 17 Jan 2023 and entered Pisces on 29 Mar 2025.
    start = datetime_to_jd(datetime(2022, 1, 1, tzinfo=timezone.utc))
    end = datetime_to_jd(datetime(2026, 1, 1, tzinfo=timezone.utc))
    spells = saturn_spells(11, start, end, DEFAULT_CONFIG)          # natal Moon in Pisces
    day = lambda jd: jd_to_datetime(jd).date().isoformat()  # noqa: E731
    rising = [(day(s.start_jd), day(s.end_jd)) for s in spells if s.phase == "rising"]
    assert rising == [("2022-04-29", "2022-07-12"), ("2023-01-17", "2025-03-29")]
    assert spells[-1].phase == "peak"


def test_sign_entry_is_inside_the_sign():
    jd = datetime_to_jd(datetime(2024, 6, 1, tzinfo=timezone.utc))
    e = sign_entry("Ju", jd, DEFAULT_CONFIG)
    assert jd_to_datetime(e).date().isoformat() == "2024-05-01"   # Jupiter into Taurus

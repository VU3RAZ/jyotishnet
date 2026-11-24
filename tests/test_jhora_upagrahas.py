# SPDX-License-Identifier: AGPL-3.0-or-later
"""Upagrahas, Sree/Indu/Varnada/Vighati lagnas and Bhrigu Bindu against the 55
Jagannatha Hora golden exports (the body table of each tests/golden/jhora file).

Tolerances follow from the golden set's position and sunrise differences:
- Sun-based upagrahas: the Sun's 5". Bhrigu Bindu, Indu Lagna: the Moon's 5".
- Varnada Lagna: the Lagna's 30". Sree Lagna: 30" + 27 x the Moon's 5" (it moves
  27 times as fast as the Moon).
- Vighati Lagna: 10', as the Pranapada (same rate, one sign per 6 minutes, which
  turns our ~1 s earlier sunrise into ~0.1 deg).
- Time-based upagrahas: 4 s of time. JHora's sunrise and sunset are 0.6-2.1 s
  later than ours on these charts (printed to the second), and its upagraha
  moments 0-3.3 s later; the arc this makes depends on the ascendant's speed."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent / "golden"))
from jhora_parser import load_all  # noqa: E402

from jyotishnet_engine import BirthData, DEFAULT_CONFIG, build_chart  # noqa: E402
from jyotishnet_engine.ephemeris import ascendant  # noqa: E402
from jyotishnet_engine.upagrahas import (indu_lagna, upagraha_times,  # noqa: E402
                                         varnada_lagna)

CHARTS = load_all()
ARC = {"Dh": 5, "Vy": 5, "Pv": 5, "IC": 5, "UK": 5, "BB": 5, "IL": 5, "VL": 30,
       "SL": 30 + 27 * 5, "ViL": 600}


def _arc(a: float, b: float) -> float:
    d = (a - b) % 360.0
    return d - 360.0 if d > 180.0 else d


@pytest.fixture(scope="module", params=CHARTS, ids=[c.name for c in CHARTS])
def pair(request):
    c = request.param
    b = BirthData(c.local, c.latitude, c.longitude, utc_offset_hours=c.utc_offset_hours,
                  altitude_m=c.altitude_m)
    return c, b, build_chart(b, DEFAULT_CONFIG, [1])


def test_points(pair):
    c, _, ch = pair
    for k, tol in ARC.items():
        assert abs(_arc(ch.special[k].longitude, c.longitudes[k])) * 3600 < tol, k


def test_time_upagrahas(pair):
    c, b, _ = pair
    for k, t in upagraha_times(b.jd_ut(), b.latitude, b.longitude, b.altitude_m,
                               DEFAULT_CONFIG).items():
        ours = ascendant(t, b.latitude, b.longitude, DEFAULT_CONFIG)
        speed = _arc(ascendant(t + 10 / 86400, b.latitude, b.longitude, DEFAULT_CONFIG), ours) / 10
        assert abs(_arc(c.longitudes[k], ours) / speed) < 4.0, k


def test_indu_and_varnada_examples():
    # PVR Rao's chart: Lagna 14 Vi 58', Moon 28 Aq 35', Hora Lagna in Pisces.
    assert int(indu_lagna(164.98, 328.59) // 30) == 9          # Capricorn
    assert int(varnada_lagna(164.98, 344.53) // 30) == 4       # Leo
    assert int(varnada_lagna(10.0, 10.0) // 30) == 1           # Aries, Aries -> Taurus

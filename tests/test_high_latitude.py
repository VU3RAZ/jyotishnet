# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Rahul Sathe
"""Charts above the polar circles.

In polar night or midnight sun there is no sunrise, which the special lagnas,
Tribhaga, vara and hora all count from. Today build_chart raises instead of
returning the planets and Lagna. The convention (JHora's, or a fallback such as
the Sun's lowest point) is an open decision; golden chart 12 in
tests/golden/README.md asks what JHora does.
"""

from datetime import datetime

import pytest

from jyotishnet_engine import BirthData, build_chart

TROMSO = (69.65, 18.96)


def test_short_night_builds():
    b = BirthData(datetime(1975, 6, 21, 23, 30), 64.15, -21.94, utc_offset_hours=0.0)
    assert build_chart(b).lagna.sign in range(12)


@pytest.mark.xfail(raises=ValueError, strict=True,
                   reason="no sunrise in polar night; convention for special lagnas is open")
@pytest.mark.parametrize("dt", [datetime(1980, 12, 21, 12), datetime(1980, 6, 21, 12)],
                         ids=["polar-night", "midnight-sun"])
def test_polar_chart_builds(dt):
    b = BirthData(dt, *TROMSO, utc_offset_hours=1.0)
    assert build_chart(b).lagna.sign in range(12)

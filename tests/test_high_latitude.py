# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Rahul Sathe
"""Charts at high latitudes, below the polar circles.

Polar births (no sunrise in polar night or midnight sun) are out of scope:
the API rejects latitudes beyond +/-66 deg (docs/DECISIONS.md).
"""

from datetime import datetime

from jyotishnet_engine import BirthData, build_chart


def test_short_night_builds():
    b = BirthData(datetime(1975, 6, 21, 23, 30), 64.15, -21.94, utc_offset_hours=0.0)
    assert build_chart(b).lagna.sign in range(12)

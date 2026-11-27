# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Rahul Sathe
"""JyotishNet Layer 0: the verified calculation core.

Deterministic Vedic astrology calculations used by the API, the browser
slider (via a WebAssembly build later) and the neural model's data pipeline.
"""

from .config import Ayanamsa, DEFAULT_CONFIG, HouseSystem, NodeType, SchoolConfig, SunriseMode
from .timeutil import BirthData
from .chart import Chart, build_chart, describe
from .dasha import ashtottari, vimshottari, yogini, running
from .boundaries import boundary_map
from .vargas import varga_sign, varga_longitude

__all__ = [
    "Ayanamsa", "DEFAULT_CONFIG", "HouseSystem", "NodeType", "SchoolConfig", "SunriseMode",
    "BirthData", "Chart", "build_chart", "describe", "vimshottari", "ashtottari", "yogini", "running",
    "boundary_map", "varga_sign", "varga_longitude",
]

__version__ = "1.0.0"

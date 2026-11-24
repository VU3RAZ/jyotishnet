# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Rahul Sathe
"""School configuration: every convention that differs between traditions.

One SchoolConfig travels with every calculation so results are reproducible
and explainable (design doc, Layer 0 "School config").
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from enum import Enum
import hashlib
import json


class Ayanamsa(str, Enum):
    LAHIRI = "lahiri"
    RAMAN = "raman"
    KP = "kp"
    TRUE_CHITRA = "true_chitra"
    YUKTESHWAR = "yukteshwar"
    FAGAN_BRADLEY = "fagan_bradley"


class NodeType(str, Enum):
    MEAN = "mean"
    TRUE = "true"


class HouseSystem(str, Enum):
    # Open decision #1 in the design doc; whole-sign is the model's default frame.
    WHOLE_SIGN = "whole_sign"
    SRIPATI = "sripati"
    PLACIDUS = "placidus"
    KOCH = "koch"
    EQUAL = "equal"
    PORPHYRY = "porphyry"


class SunriseMode(str, Enum):
    # Open decision #2 in the design doc.
    DISC_CENTER_NO_REFRACTION = "disc_center_no_refraction"
    DISC_CENTER_REFRACTION = "disc_center_refraction"
    UPPER_LIMB_REFRACTION = "upper_limb_refraction"


@dataclass(frozen=True)
class SchoolConfig:
    ayanamsa: Ayanamsa = Ayanamsa.LAHIRI
    node_type: NodeType = NodeType.MEAN
    house_system: HouseSystem = HouseSystem.WHOLE_SIGN
    sunrise: SunriseMode = SunriseMode.DISC_CENTER_NO_REFRACTION
    # Dasha years: "solar" (Sun's sidereal motion; Jagannatha Hora's default) or
    # "fixed" (dasha_year_days per year).
    dasha_year_mode: str = "solar"
    dasha_year_days: float = 365.25
    node_special_aspects: bool = False
    chara_karakas: int = 8
    # True (geometric) positions, as Jagannatha Hora and PyJHora use: the JHora
    # golden set matches within 2.2 arc-seconds this way, against 48 with apparent
    # positions (light-time and aberration), the astronomical standard.
    true_positions: bool = True

    def key(self) -> str:
        """Stable hash used for caching results per configuration."""
        payload = json.dumps(asdict(self), sort_keys=True, default=str)
        return hashlib.sha256(payload.encode()).hexdigest()[:16]


DEFAULT_CONFIG = SchoolConfig()

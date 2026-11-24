# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Rahul Sathe
"""Static Jyotish reference tables used across the engine.

Signs are indexed 0..11 from Aries. Planets use two-letter codes.
"""

from __future__ import annotations

SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
]
SIGN_ABBR = ["Ar", "Ta", "Ge", "Cn", "Le", "Vi", "Li", "Sc", "Sg", "Cp", "Aq", "Pi"]

GRAHAS = ["Su", "Mo", "Ma", "Me", "Ju", "Ve", "Sa", "Ra", "Ke"]
GRAHA_NAMES = {
    "Su": "Sun", "Mo": "Moon", "Ma": "Mars", "Me": "Mercury", "Ju": "Jupiter",
    "Ve": "Venus", "Sa": "Saturn", "Ra": "Rahu", "Ke": "Ketu",
}

# Sign lords (Parashari).
SIGN_LORD = ["Ma", "Ve", "Me", "Mo", "Su", "Me", "Ve", "Ma", "Ju", "Sa", "Sa", "Ju"]

# Modality: 0 movable (chara), 1 fixed (sthira), 2 dual (dvisvabhava).
def modality(sign: int) -> int:
    return sign % 3

# Element: 0 fire, 1 earth, 2 air, 3 water.
def element(sign: int) -> int:
    return sign % 4

def is_odd_sign(sign: int) -> bool:
    """Aries, Gemini, Leo... are odd (male) signs; index 0, 2, 4..."""
    return sign % 2 == 0

# Exaltation sign and deepest degree; debilitation is the 7th from it.
EXALTATION = {
    "Su": (0, 10.0), "Mo": (1, 3.0), "Ma": (9, 28.0), "Me": (5, 15.0),
    "Ju": (3, 5.0), "Ve": (11, 27.0), "Sa": (6, 20.0),
}

# Moolatrikona: sign and degree range [start, end).
# Moon: Taurus 4-20 deg (as Jagannatha Hora: golden charts edge_18-20 place the end
# between 17.2 and 20.2 deg); BPHS readings that run to 30 deg are a school option.
MOOLATRIKONA = {
    "Su": (4, 0.0, 20.0), "Mo": (1, 4.0, 20.0), "Ma": (0, 0.0, 12.0),
    "Me": (5, 16.0, 20.0), "Ju": (8, 0.0, 10.0), "Ve": (6, 0.0, 15.0),
    "Sa": (10, 0.0, 20.0),
}

OWN_SIGNS = {
    "Su": [4], "Mo": [3], "Ma": [0, 7], "Me": [2, 5], "Ju": [8, 11],
    "Ve": [1, 6], "Sa": [9, 10],
}

# Naisargika (natural) relationships, BPHS.
NATURAL_FRIENDS = {
    "Su": {"Mo", "Ma", "Ju"}, "Mo": {"Su", "Me"}, "Ma": {"Su", "Mo", "Ju"},
    "Me": {"Su", "Ve"}, "Ju": {"Su", "Mo", "Ma"}, "Ve": {"Me", "Sa"},
    "Sa": {"Me", "Ve"},
}
NATURAL_ENEMIES = {
    "Su": {"Ve", "Sa"}, "Mo": set(), "Ma": {"Me"}, "Me": {"Mo"},
    "Ju": {"Me", "Ve"}, "Ve": {"Su", "Mo"}, "Sa": {"Su", "Mo", "Ma"},
}

NAKSHATRAS = [
    "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra",
    "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni",
    "Uttara Phalguni", "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha",
    "Jyeshtha", "Mula", "Purva Ashadha", "Uttara Ashadha", "Shravana",
    "Dhanishta", "Shatabhisha", "Purva Bhadrapada", "Uttara Bhadrapada", "Revati",
]
NAKSHATRA_SPAN = 360.0 / 27.0

# Vimshottari sequence and years.
VIMSHOTTARI_LORDS = ["Ke", "Ve", "Su", "Mo", "Ma", "Ra", "Ju", "Sa", "Me"]
VIMSHOTTARI_YEARS = {"Ke": 7, "Ve": 20, "Su": 6, "Mo": 10, "Ma": 7, "Ra": 18, "Ju": 16, "Sa": 19, "Me": 17}

# Yogini dasha: name, lord, years. Total 36 years.
# Ashtottari (108 years). Each lord rules a run of nakshatras counted from Ardra
# (index 5, 0-based); the balance at birth is the Moon's progress through the
# whole run. Order of lords: Su, Mo, Ma, Me, Sa, Ju, Ra, Ve.
ASHTOTTARI_LORDS = ["Su", "Mo", "Ma", "Me", "Sa", "Ju", "Ra", "Ve"]
ASHTOTTARI_YEARS = {"Su": 6, "Mo": 15, "Ma": 8, "Me": 17, "Sa": 10, "Ju": 19, "Ra": 12, "Ve": 21}
ASHTOTTARI_NAKSHATRAS = {"Su": 4, "Mo": 3, "Ma": 4, "Me": 3, "Sa": 3, "Ju": 3, "Ra": 4, "Ve": 3}
ASHTOTTARI_FIRST_NAKSHATRA = 5   # Ardra

YOGINIS = [
    ("Mangala", "Mo", 1), ("Pingala", "Su", 2), ("Dhanya", "Ju", 3),
    ("Bhramari", "Ma", 4), ("Bhadrika", "Me", 5), ("Ulka", "Sa", 6),
    ("Siddha", "Ve", 7), ("Sankata", "Ra", 8),
]

# Parashari graha drishti: houses aspected counted from the planet (1 = own house).
GRAHA_DRISHTI = {
    "Su": [7], "Mo": [7], "Me": [7], "Ve": [7],
    "Ma": [4, 7, 8], "Ju": [5, 7, 9], "Sa": [3, 7, 10],
    "Ra": [7], "Ke": [7],
}
NODE_SPECIAL_DRISHTI = [5, 7, 9]  # optional school setting for Rahu/Ketu

# The 16 Parashari divisional charts (Shodashavarga).
SHODASHAVARGA = [1, 2, 3, 4, 7, 9, 10, 12, 16, 20, 24, 27, 30, 40, 45, 60]

# Every chart Jagannatha Hora draws (D150 is a nadiamsa number, not a chart).
ALL_VARGAS = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 16, 20, 24, 27, 30, 40, 45, 60,
              81, 108, 144]

# The 13 vargas encoded by the neural model (design doc, locked decision 3).
MODEL_VARGAS = [1, 2, 3, 4, 7, 9, 10, 12, 16, 20, 24, 30, 60]

VARGA_NAMES = {
    1: "Rasi", 2: "Hora", 3: "Drekkana", 4: "Chaturthamsa", 7: "Saptamsa",
    9: "Navamsa", 10: "Dasamsa", 12: "Dwadasamsa", 16: "Shodasamsa",
    20: "Vimsamsa", 24: "Chaturvimsamsa", 27: "Bhamsa", 30: "Trimsamsa",
    40: "Khavedamsa", 45: "Akshavedamsa", 60: "Shashtiamsa",
    5: "Panchamsa", 6: "Shashthamsa", 8: "Ashtamsa", 11: "Rudramsa",
    81: "Navanavamsa", 108: "Ashtottaramsa", 144: "Dwadasa-dwadasamsa",
}

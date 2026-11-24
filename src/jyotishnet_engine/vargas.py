# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Rahul Sathe
"""Parashari divisional charts (Shodashavarga), per Brihat Parashara Hora Shastra.

`varga_sign(lon, n)` returns the sign (0..11) a sidereal longitude falls in for
divisional chart Dn. `varga_longitude` also gives the position within that sign,
scaling the division to 30 degrees, which the slider and the model use.

Variant schemes (Parivritti or Kashinatha hora, Somanatha drekkana and others)
are added as separate functions keyed by name; the defaults below are Parashari.

D5, D6, D8, D11, D81, D108 and D144 follow Jagannatha Hora 8.0's code and default
settings (read from jhora.exe); all 22 vargas JHora draws match its charts on the
55 golden charts. D150 (nadiamsa) is a numbered part of the sign, not a chart:
see `nadiamsa`.
"""

from __future__ import annotations

from bisect import bisect_right
from dataclasses import dataclass

from .constants import element, is_odd_sign, modality


def _parts(lon: float, n: int) -> tuple[int, int, float]:
    """Sign, part index within the sign, and fraction through that part."""
    lon = lon % 360.0
    sign = int(lon // 30)
    within = lon - sign * 30
    # Multiply before dividing so exact boundaries (e.g. 10 deg in D9) land in
    # the next part, matching the continuous formula floor(lon * n / 30).
    scaled = within * n / 30.0
    part = min(int(scaled), n - 1)
    frac = min(max(scaled - part, 0.0), 1.0 - 1e-12)
    return sign, part, frac


HORA_SCHEMES = ("uma_shambhu", "parashara")
RUDRAMSA_SCHEMES = ("rath", "raman")
D108_SCHEMES = ("navamsa", "rasi")
# Panchamsa: odd signs Aries, Aquarius, Sagittarius, Gemini, Libra (the signs of
# Mars, Saturn, Jupiter, Mercury, Venus); even signs the other signs of the same
# lords in the same order of parts reversed: Taurus, Virgo, Pisces, Capricorn, Scorpio.
_PANCHAMSA_ODD = (0, 10, 8, 2, 6)
_PANCHAMSA_EVEN = (1, 5, 11, 9, 7)


def varga_sign(lon: float, n: int, hora_scheme: str = "uma_shambhu",
               rudramsa_scheme: str = "rath", d108_scheme: str = "navamsa") -> int:
    """Sign of `lon` in Dn.

    D2 defaults to the Uma-Shambhu hora (parivritti, reversed in even signs), which
    Jagannatha Hora uses for its D-2 chart and in Saptavargaja bala (golden set:
    21/21 exact). "parashara" is the classic Leo/Cancer hora.
    D11: "rath" (zodiacal Rudramsa, JHora's default) or "raman" (anti-zodiacal).
    D108: "navamsa" (each navamsa divided into 12, from the navamsa sign; JHora's
    setting in the golden set) or "rasi" (the sign in 108 parts, from the sign).
    """
    sign, part, _ = _parts(lon, n)
    if n == 2 and hora_scheme == "uma_shambhu":
        return (sign * 2 + (part if is_odd_sign(sign) else 1 - part)) % 12
    odd = is_odd_sign(sign)
    mod = modality(sign)

    if n == 1:
        return sign
    if n == 2:  # Hora: Sun's hora = Leo, Moon's hora = Cancer
        first = 4 if odd else 3
        return first if part == 0 else (3 if first == 4 else 4)
    if n == 3:  # Drekkana: 1st, 5th, 9th from the sign
        return (sign + 4 * part) % 12
    if n == 4:  # Chaturthamsa: kendras from the sign
        return (sign + 3 * part) % 12
    if n == 5:  # Panchamsa
        return (_PANCHAMSA_ODD if odd else _PANCHAMSA_EVEN)[part]
    if n == 6:  # Shashthamsa: odd from Aries, even from Libra
        return ((0 if odd else 6) + part) % 12
    if n == 7:  # Saptamsa: odd from the sign, even from the 7th
        return (sign + part + (0 if odd else 6)) % 12
    if n == 8:  # Ashtamsa: movable from Aries, fixed from Sagittarius, dual from Leo
        return ({0: 0, 1: 8, 2: 4}[mod] + part) % 12
    if n == 9:  # Navamsa: movable from itself, fixed from 9th, dual from 5th
        start = {0: sign, 1: sign + 8, 2: sign + 4}[mod]
        return (start + part) % 12
    if n == 10:  # Dasamsa: odd from the sign, even from the 9th
        return (sign + part + (0 if odd else 8)) % 12
    if n == 11:  # Rudramsa
        if rudramsa_scheme == "raman":   # anti-zodiacal, from the 12th from the sign
            return (sign - part + 11) % 12
        return (part - sign) % 12        # zodiacal (Pt. Rath): from Aries back by the sign
    if n == 12:  # Dwadasamsa: from the sign
        return (sign + part) % 12
    if n == 16:  # Shodasamsa: movable Aries, fixed Leo, dual Sagittarius
        return ({0: 0, 1: 4, 2: 8}[mod] + part) % 12
    if n == 20:  # Vimsamsa: movable Aries, fixed Sagittarius, dual Leo
        return ({0: 0, 1: 8, 2: 4}[mod] + part) % 12
    if n == 24:  # Chaturvimsamsa: odd from Leo, even from Cancer
        return ((4 if odd else 3) + part) % 12
    if n == 27:  # Bhamsa: fire Aries, earth Cancer, air Libra, water Capricorn
        return ({0: 0, 1: 3, 2: 6, 3: 9}[element(sign)] + part) % 12
    if n == 30:  # Trimsamsa: unequal parts ruled by the five tara grahas
        return _trimsamsa(lon)
    if n == 40:  # Khavedamsa: odd from Aries, even from Libra
        return ((0 if odd else 6) + part) % 12
    if n == 45:  # Akshavedamsa: movable Aries, fixed Leo, dual Sagittarius
        return ({0: 0, 1: 4, 2: 8}[mod] + part) % 12
    if n == 60:  # Shashtiamsa: from the sign
        return (sign + part) % 12
    if n == 81:  # Navanavamsa: navamsa of the navamsa (continuous from Aries)
        return int((lon % 360.0) * 81 / 30.0) % 12
    if n == 108:  # Ashtottaramsa
        start = sign if d108_scheme == "rasi" else varga_sign(lon, 9)
        return (start + part) % 12
    if n == 144:  # Dwadasa-dwadasamsa: dwadasamsa of the dwadasamsa
        return (varga_sign(lon, 12) + part) % 12
    raise ValueError(f"Unsupported varga D{n}")


# Odd signs: Mars 0-5 (Aries), Saturn 5-10 (Aquarius), Jupiter 10-18 (Sagittarius),
# Mercury 18-25 (Gemini), Venus 25-30 (Libra). Even signs reverse the order:
# Venus 0-5 (Taurus), Mercury 5-12 (Virgo), Jupiter 12-20 (Pisces),
# Saturn 20-25 (Capricorn), Mars 25-30 (Scorpio).
_TRIMSAMSA_ODD = [(5, 0), (10, 10), (18, 8), (25, 2), (30, 6)]
_TRIMSAMSA_EVEN = [(5, 1), (12, 5), (20, 11), (25, 9), (30, 7)]


def _trimsamsa_bounds(lon: float) -> tuple[float, float, int]:
    lon = lon % 360.0
    sign = int(lon // 30)
    within = lon - sign * 30
    table = _TRIMSAMSA_ODD if is_odd_sign(sign) else _TRIMSAMSA_EVEN
    start = 0.0
    for end, target in table:
        if within < end:
            return start, float(end), target
        start = float(end)
    return 25.0, 30.0, table[-1][1]


def _trimsamsa(lon: float) -> int:
    return _trimsamsa_bounds(lon)[2]


def varga_longitude(lon: float, n: int, hora_scheme: str = "uma_shambhu",
                    rudramsa_scheme: str = "rath", d108_scheme: str = "navamsa") -> float:
    """Longitude in the varga chart: target sign plus scaled position in the part."""
    if n == 1:
        return lon % 360.0
    if n == 30:
        start, end, target = _trimsamsa_bounds(lon)
        within = (lon % 30.0)
        frac = (within - start) / (end - start)
        return target * 30.0 + frac * 30.0
    _, _, frac = _parts(lon, n)
    return varga_sign(lon, n, hora_scheme, rudramsa_scheme, d108_scheme) * 30.0 + frac * 30.0


def is_vargottama(lon: float) -> bool:
    return varga_sign(lon, 1) == varga_sign(lon, 9)

# Nadiamsa (D150). Starts of the 150 parts of a sign in units of 1/504 deg, as
# Jagannatha Hora 8.0's "non-uniform 150 division based on Chandra Kala Nadi" (its
# default; read from jhora.exe). The uniform division (0.2 deg each) is an option.
_NADI_STARTS = (
    0, 252, 336, 378, 504, 560, 630, 672, 756, 945, 1008, 1120, 1134, 1260, 1344, 1512,
    1680, 1764, 1890, 2016, 2160, 2240, 2268, 2352, 2520, 2646, 2688, 2772, 2800, 2835,
    3024, 3150, 3276, 3360, 3402, 3528, 3696, 3780, 3920, 4032, 4158, 4284, 4320, 4368,
    4410, 4480, 4536, 4704, 4725, 4788, 4914, 5040, 5292, 5376, 5544, 5600, 5670, 5712,
    5796, 6048, 6160, 6300, 6384, 6426, 6480, 6552, 6615, 6720, 6804, 6930, 7056, 7182,
    7280, 7308, 7392, 7560, 7728, 7812, 7840, 7938, 8064, 8190, 8316, 8400, 8505, 8568,
    8640, 8694, 8736, 8820, 8960, 9072, 9324, 9408, 9450, 9520, 9576, 9744, 9828, 10080,
    10206, 10332, 10395, 10416, 10584, 10640, 10710, 10752, 10800, 10836, 10962, 11088,
    11200, 11340, 11424, 11592, 11718, 11760, 11844, 11970, 12096, 12285, 12320, 12348,
    12432, 12474, 12600, 12768, 12852, 12880, 12960, 13104, 13230, 13356, 13440, 13608,
    13776, 13860, 13986, 14000, 14112, 14175, 14364, 14448, 14490, 14560, 14616, 14742,
    14784, 14868,
)
# Names in Deva Keralam (Chandra Kala Nadi), by nadiamsa index 1..150 (JHora's
# default name list).
NADI_NAMES = (
    'Vasudha', 'Vaishnavi', 'Braahmi', 'Kaalakoota', 'Sankari', 'Sudhakarasama',
    'Saumya', 'Suraa', 'Maayaa', 'Manohara', 'Maadhavi', 'Manjuswana', 'Ghora',
    'Kumbhini', 'Kutila', 'Prabhaa', 'Paraa', 'Payaswini', 'Maalaa', 'Jagati',
    'Jarjhari', 'Dhruva', 'Musala', 'Mudgala', 'Paasaa', 'Chambaka', 'Daamini', 'Mahi',
    'Kalusha', 'Kamala', 'Kaantaa', 'Kaalaa', 'Karikara', 'Kshamaa', 'Durdharaa',
    'Durbhagaa', 'Viswa', 'Visirna', 'Vihwala', 'Anilaa', 'Bheema', 'Sukhaprada',
    'Snigdha', 'Sodara', 'Surasundari', 'Amritapraasini', 'Kaalaa/Karaalaa',
    'Kaamadrikkara Veerini', 'Gahwaraa', 'Kundini', 'Kaanthaa', 'Vishaakhya (Visha)',
    'Vishanaasini', 'Nirmada', 'Seetala', 'Nimnaa', 'Preeta', 'Priyavivardhini',
    'Manaadha (Maanaghna)', 'Durbhaga', 'Chitra', 'Vichitra', 'Chiranjeevini', 'Bhoopa',
    'Gadaaharaa', 'Naalaa', 'Gaalavee', 'Nirmalaa', 'Nadee', 'Sudhaa', 'Mritamsuga',
    'Kaali', 'Kaalikaa', 'Kalushaankuraa', 'Trailokya Mohanakari', 'Mahaamaayaa',
    'Suseetalaa', 'Sukhadaa', 'Suprabhaa', 'Sobhaa', 'Sobhana', 'Sivadaa', 'Sivaa',
    'Balaa', 'Jwaalaa', 'Gadaa', 'Gaadaa', 'Sootana (Nootana)', 'Sumanoharaa',
    'Somavalli', 'Somalataa', 'Mangala', 'Mudrikaa', 'Sudhaa', 'Melaa', 'Apavargaa',
    'Pasyathaa', 'Navaneetaa', 'Nisaachari', 'Nivriti', 'Nirgatha', 'Saaraa',
    'Saamagaa', 'Saamadaa', 'Samaa', 'Viswambharaa', 'Kumaari', 'Kokilaa',
    'Kunjarakriti', 'Indra', 'Swaahaa', 'Swadhaa', 'Vahni', 'Peetha', 'Yakshi',
    'Achalaprabhaa', 'Saarini', 'Madhuraa', 'Maitri', 'Harini', 'Haarini', 'Marutaa',
    'Dhananjaya', 'Dhanakari', 'Dhanadaa', 'Kachchapaa', 'Ambujaa', 'Isaani', 'Soolini',
    'Roudri', 'Sivaasivakari', 'Kalaa', 'Kunda', 'Mukunda', 'Bharata', 'Kadali',
    'Smaraa', 'Basita', 'Kodala', 'Kokilamsa', 'Kaamini', 'Kalasodbhava', 'Viraprasoo',
    'Sangaraa', 'Satayajnaa', 'Sataavari', 'Sragvi', 'Paatalini', 'Naagapankaja',
    'Parameswari',
)
NADIAMSA_SCHEMES = ("chandra_kala", "uniform")


@dataclass(frozen=True)
class Nadiamsa:
    division: int   # 1..150, counted from the start of the sign
    index: int      # 1..150: as the division in movable signs, reversed in fixed
                    # signs, shifted by 75 in dual signs (JHora)
    name: str


def nadiamsa(lon: float, scheme: str = "chandra_kala") -> Nadiamsa:
    lon = lon % 360.0
    sign = int(lon // 30)
    within = lon - sign * 30
    if scheme == "uniform":
        div = min(int(within * 5.0), 149)
    else:
        units = within * 504.0
        div = bisect_right(_NADI_STARTS, units) - 1
        div = min(max(div, 0), 149)
    mod = modality(sign)
    index = div if mod == 0 else 149 - div if mod == 1 else (div + 75) % 150
    return Nadiamsa(div + 1, index + 1, NADI_NAMES[index])

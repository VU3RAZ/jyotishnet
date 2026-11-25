# SPDX-License-Identifier: AGPL-3.0-or-later
"""Panchanga against Jagannatha Hora 8.0.

Birth panchanga: the "Key info" block of each golden chart (tests/golden/jhora/*.txt).

Day panchanga: tests/golden/jhora_panchanga/<chart>.json, JHora's monthly panchanga
for the birth month at the birth place (tools/import_jhora_panchanga.py). JHora prints
h:mm and, per field:
  - element ends (tithi, nakshatra, yoga, karana, the Moon's sign) are truncated to
    the minute: ours - JHora in [0, 1) min;
  - sunrise, sunset, the kalas, durmuhurta, varjya, moonrise and moonset are rounded:
    |ours - JHora| <= 0.5 min.
Both allow EPS (3 s) for ephemeris and Delta-T noise, the same 3 s as the birth sunrise
check. Day entries JHora gets visibly wrong, or that sit within seconds of a sunrise,
are listed in tests/golden/pending/jhora_panchanga.json with a note and skipped.
"""

import json
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent / "golden"))
from jhora_parser import parse  # noqa: E402

from jyotishnet_engine import BirthData, DEFAULT_CONFIG, build_chart  # noqa: E402
from jyotishnet_engine.panchanga import (MASAS, WEEKDAYS, birth_panchanga,  # noqa: E402
                                         day_panchanga)
from jyotishnet_engine.timeutil import datetime_to_jd, jd_to_datetime  # noqa: E402

GOLDEN = Path(__file__).parent / "golden"
CHARTS = sorted(p.stem for p in (GOLDEN / "jhora").glob("*.txt"))
DAYS = sorted(p.stem for p in (GOLDEN / "jhora_panchanga").glob("*.json"))
PENDING = {(p["chart"], p["date"], p["field"]): p["note"]
           for p in json.loads((GOLDEN / "pending" / "jhora_panchanga.json").read_text())}
EPS = 3.0 / 60.0

# JHora spellings
J_TITHI = {"Pratipat": "Pratipada", "Sapthami": "Saptami", "Dasami": "Dashami",
           "Ekadasi": "Ekadashi", "Dwadasi": "Dwadashi", "Trayodasi": "Trayodashi",
           "Chaturdasi": "Chaturdashi"}
J_MASA = ["Chaitra", "Vaisakha", "Jyeshtha", "Ashadha", "Sravana", "Bhadrapada", "Aswayuja",
          "Karthika", "Margasira", "Pushya", "Magha", "Phalguna"]
J_KARANA = ["Bava", "Balava", "Kaulava", "Taitula", "Garija", "Vanija", "Vishti", "Sakuna",
            "Chatushpada", "Naga", "Kimstughna"]
PLANETS = {"Sun": "Su", "Moon": "Mo", "Mars": "Ma", "Mercury": "Me", "Jupiter": "Ju",
           "Venus": "Ve", "Saturn": "Sa"}


def karana11(index: int) -> int:
    """0..59 karana of the lunar month -> JHora's 11-name index."""
    return 10 if index == 0 else 7 + index - 57 if index >= 57 else (index - 1) % 7


def test_day_files_cover_the_golden_set():
    assert DAYS == CHARTS


@pytest.mark.parametrize("name", CHARTS)
def test_birth_panchanga(name):
    c = parse(GOLDEN / "jhora" / f"{name}.txt")
    text = (GOLDEN / "jhora" / f"{name}.txt").read_text()

    def key(k: str) -> str:
        return re.search(rf"^{k}:\s+(.*)$", text, re.M).group(1).strip()

    ch = build_chart(BirthData(c.local, c.latitude, c.longitude, utc_offset_hours=c.utc_offset_hours,
                               altitude_m=c.altitude_m), DEFAULT_CONFIG, [1])
    b = birth_panchanga(ch.jd_ut, c.latitude, c.longitude, c.altitude_m, DEFAULT_CONFIG, ch.lagna.sign)

    pak, nm, lord, left = re.match(r"(?:(Sukla|Krishna) )?(\w+) \((\w\w)\) \(([\d.]+)% left\)",
                                   key("Tithi")).groups()
    tithi = ("Purnima" if nm == "Pournimasya" else "Amavasya" if nm == "Amavasya"
             else f"{'Shukla' if pak == 'Sukla' else 'Krishna'} {J_TITHI.get(nm, nm)}")
    assert b.tithi.name == tithi
    assert b.tithi.lord == lord
    assert b.tithi.fraction_left * 100 == pytest.approx(float(left), abs=0.02)
    assert WEEKDAYS[b.weekday] == key("Vedic Weekday").split()[0]

    def lord_left(field: str) -> tuple[str, float]:
        v = key(field)
        return re.search(r"\((\w\w)\)", v).group(1), float(re.search(r"([\d.]+)% left", v).group(1))

    y_lord, y_left = lord_left("Yoga")
    assert b.yoga.lord == y_lord
    assert b.yoga.fraction_left * 100 == pytest.approx(y_left, abs=0.02)
    assert b.nakshatra.fraction_left * 100 == pytest.approx(
        float(re.search(r"([\d.]+)% left", key("Nakshatra")).group(1)), abs=0.02)
    assert J_KARANA[karana11(b.karana.index)] == key("Karana").split()[0]
    assert b.karana.lord == re.search(r"\((\w\w)\)", key("Karana")).group(1)
    assert b.hora_lord == PLANETS[key("Hora Lord").split()[0]]

    year, month = key("Lunar Yr-Mo").split(" - ")
    assert b.samvatsara == year
    *prefix, masa = b.masa.split()
    *j_prefix, j_masa = month.split()
    assert (prefix, MASAS.index(masa)) == (j_prefix, J_MASA.index(j_masa))

    def seconds(jd: float) -> float:
        t = jd_to_datetime(jd).replace(tzinfo=None) + timedelta(hours=c.utc_offset_hours)
        return t.hour * 3600 + t.minute * 60 + t.second       # JHora truncates seconds too

    def j_seconds(v: str) -> int:
        h, m, s = v.split()[0].split(":")
        return int(h) * 3600 + int(m) * 60 + int(s)

    assert seconds(b.sunrise) == pytest.approx(j_seconds(key("Sunrise")), abs=3)
    assert seconds(b.sunset) == pytest.approx(j_seconds(key("Sunset")), abs=3)
    assert b.janma_ghatis == pytest.approx(float(key("Janma Ghatis")), abs=0.0015)


def _day_problems(name: str) -> list[str]:
    c = parse(GOLDEN / "jhora" / f"{name}.txt")
    problems = []
    for d in json.loads((GOLDEN / "jhora_panchanga" / f"{name}.json").read_text()):
        date = d["date"]
        midnight = datetime.strptime(date, "%Y-%m-%d") - timedelta(hours=c.utc_offset_hours)
        jd0 = datetime_to_jd(midnight.replace(tzinfo=timezone.utc))
        day = day_panchanga(jd0 + 0.5, c.latitude, c.longitude, c.altitude_m, DEFAULT_CONFIG)

        def m(jd: float) -> float:
            return (jd - jd0) * 1440.0

        def bad(field: str, what: str) -> None:
            if (name, date, field) not in PENDING:
                problems.append(f"{date} {field}: {what}")

        def rounded(field: str, ours: float, theirs: int | None) -> None:
            if theirs is not None and not abs(ours - theirs) <= 0.5 + EPS:
                bad(field, f"ours {ours:.2f} JHora {theirs}")

        def truncated(field: str, ours: float, theirs: int | None) -> None:
            if theirs is not None and not -EPS <= ours - theirs < 1.0 + EPS:
                bad(field, f"ours {ours:.2f} JHora {theirs}")

        if day.weekday != d["weekday"]:
            bad("weekday", f"ours {day.weekday} JHora {d['weekday']}")
        rounded("sunrise", m(day.sunrise), d["sunrise"])
        rounded("sunset", m(day.sunset), d["sunset"])
        for kind, mine in (("tithi", day.tithis), ("nakshatra", day.nakshatras),
                           ("yoga", day.yogas), ("karana", day.karanas)):
            idx = [karana11(e.index) if kind == "karana" else e.index for e in mine]
            if idx != [i for i, _ in d[kind]]:
                bad(kind, f"ours {idx} JHora {d[kind]}")
                continue
            for e, (_, t) in zip(mine, d[kind]):
                truncated(kind, m(e.end_jd), t)
        for field in ("rahu_kala", "gulika_kala", "yamaganda"):
            for ours, theirs in zip(getattr(day, field), d[field]):
                rounded(field, m(ours), theirs)
        for field in ("durmuhurta", "varjya"):
            mine = getattr(day, field)
            if len(mine) != len(d[field]):
                bad(field, f"ours {[(round(m(a)), round(m(b))) for a, b in mine]} JHora {d[field]}")
                continue
            for (a, b), (x, y) in zip(mine, d[field]):
                rounded(field, m(a), x)
                rounded(field, m(b), y)
        rounded("moonrise", m(day.moonrise), d["moonrise"])
        rounded("moonset", m(day.moonset), d["moonset"])
        if d["moon_sign"] is not None:          # JHora sometimes prints "Moonset" twice instead
            sign, end = d["moon_sign"]
            if sign != day.moon_sign or (end is None) != (day.moon_sign_end is None):
                bad("moon_sign", f"ours {day.moon_sign} till {day.moon_sign_end} JHora {d['moon_sign']}")
            elif end is not None:
                truncated("moon_sign", m(day.moon_sign_end), end)
    return problems


@pytest.mark.parametrize("name", DAYS)
def test_day_panchanga(name):
    assert _day_problems(name) == []


def test_pending_entries_name_known_days():
    for chart, date, _ in PENDING:
        days = json.loads((GOLDEN / "jhora_panchanga" / f"{chart}.json").read_text())
        assert date in {d["date"] for d in days}

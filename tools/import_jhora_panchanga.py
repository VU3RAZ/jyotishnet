# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Rahul Sathe
"""Convert JHora 8.0 monthly panchanga exports to golden JSON.

Export (one golden chart at a time, see tools/jhora/README.md): Miscellany tab >
Panchanga sub-tab > right-click > "Copy monthly panchanga"; save the clipboard as
SRC/<chart>.txt. Then

    python tools/import_jhora_panchanga.py SRC [tests/golden/jhora_panchanga]

writes <chart>.json: one entry per day with times in minutes from the local midnight
of that date (JHora prints h:mm; a "*" time is after midnight, +1440) and the
elements as indices (tithi 0..29, nakshatra 0..26, yoga 0..26, karana 0..59 of the
lunar month cannot be told from the name alone, so karanas keep the 11-name index:
Bava..Vishti 0..6, Shakuni 7, Chatushpada 8, Naga 9, Kimstughna 10).
"""

import json
import re
import sys
from datetime import datetime
from pathlib import Path

PAKSHA = ["Pratipat", "Dwitiya", "Tritiya", "Chaturthi", "Panchami", "Shashthi", "Sapthami",
          "Ashtami", "Navami", "Dasami", "Ekadasi", "Dwadasi", "Trayodasi", "Chaturdasi"]
NAKSHATRAS = ["aswini", "bharani", "krittika", "rohini", "mrigasira", "ardra", "punarvasu",
              "pushyami", "aasresha", "magha", "poorvaphalguni", "uttaraphalguni", "hastha",
              "chitra", "swaati", "visakha", "anuraadha", "jyeshtha", "moola", "poorvashadha",
              "uttarashadha", "sravanam", "dhanishtha", "satabhishak", "poorvabhadra",
              "uttarabhadra", "revati"]
ALIASES = {"aardra": "ardra", "arudra": "ardra", "chittha": "chitra", "chitta": "chitra"}
YOGAS = ["Vishkambha", "Priti", "Ayushman", "Soubhagya", "Sobhana", "Atiganda", "Sukarman",
         "Dhriti", "Soola", "Ganda", "Vriddhi", "Dhruva", "Vyaghata", "Harshana", "Vajra",
         "Siddhi", "Vyatipata", "Variyan", "Parigha", "Siva", "Siddha", "Sadhya", "Subha",
         "Sukla", "Brahma", "Indra", "Vaidhriti"]
KARANAS = ["Bava", "Balava", "Kaulava", "Taitula", "Garija", "Vanija", "Vishti", "Sakuna",
           "Chatushpada", "Naga", "Kimstughna"]
SIGNS = "Ar Ta Ge Cn Le Vi Li Sc Sg Cp Aq Pi".split()
WEEKDAYS = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
LISTS = {"Varjya": "varjya", "Durmuhurta": "durmuhurta"}
KALAS = {"RahuK": "rahu_kala", "GulikaK": "gulika_kala", "YamaG": "yamaganda"}


def minutes(t: str) -> int:
    star = t.endswith("*")
    h, m = t.rstrip("*").split(":")
    return int(h) * 60 + int(m) + (1440 if star else 0)


def tithi(name: str) -> int | None:
    if name == "Pournimasya":
        return 14
    if name == "Amavasya":
        return 29
    m = re.fullmatch(r"(Sukla|Krishna) (\w+)", name)
    if not m or m.group(2) not in PAKSHA:
        return None
    return PAKSHA.index(m.group(2)) + (0 if m.group(1) == "Sukla" else 15)


def nakshatra(name: str) -> int:
    key = name.lower().replace(" ", "")
    return NAKSHATRAS.index(ALIASES.get(key, key))


def parse_day(date: str, body: str) -> dict:
    d = {"date": datetime.strptime(date, "%B %d, %Y").strftime("%Y-%m-%d"),
         "tithi": [], "nakshatra": [], "yoga": [], "karana": [], "varjya": [], "durmuhurta": [],
         "moon_sign": None}     # JHora sometimes prints "Moonset" twice instead of it
    current = None
    for item in [x.strip() for x in body.split(",") if x.strip()]:
        if item in WEEKDAYS:
            d["weekday"] = WEEKDAYS.index(item)
            continue
        m = re.fullmatch(r"(\w+): (\d+:\d+\*?) - (\d+:\d+\*?)", item)
        if m:
            key, a, b = m.groups()
            if key in KALAS:
                d[KALAS[key]] = [minutes(a), minutes(b)]
                current = None
            else:
                current = LISTS[key]
                d[current].append([minutes(a), minutes(b)])
            continue
        m = re.fullmatch(r"(\d+:\d+\*?) - (\d+:\d+\*?)", item)
        if m and current:
            d[current].append([minutes(m.group(1)), minutes(m.group(2))])
            continue
        current = None
        m = re.fullmatch(r"(Sunrise|Sunset|Moonrise|Moonset) at (\d+:\d+\*?)", item)
        if m:
            d[m.group(1).lower()] = minutes(m.group(2))
            continue
        m = re.fullmatch(r"Moon in (\w\w) (?:till (\d+:\d+\*?)|\(whole day\))", item)
        if m:
            d["moon_sign"] = [SIGNS.index(m.group(1)), minutes(m.group(2)) if m.group(2) else None]
            continue
        m = re.fullmatch(r"(.+?) (yoga |karana )?(?:till (\d+:\d+\*?)|\(whole day\))", item)
        if not m:
            raise ValueError(f"{date}: cannot read {item!r}")
        name, kind = m.group(1), (m.group(2) or "").strip()
        t = minutes(m.group(3)) if m.group(3) else None      # None: runs the whole day
        if kind == "yoga":
            d["yoga"].append([YOGAS.index(name), t])
        elif kind == "karana":
            d["karana"].append([KARANAS.index(name), t])
        elif tithi(name) is not None:
            d["tithi"].append([tithi(name), t])
        else:
            d["nakshatra"].append([nakshatra(name), t])
    return d


def convert(text: str) -> list[dict]:
    days = re.split(r"^(\w+ \d+, \d+):\s*$", text.replace("\r", ""), flags=re.M)
    out = [parse_day(days[i], " ".join(days[i + 1].split())) for i in range(1, len(days), 2)]
    # JHora sometimes prints its last day or two with every time marked "*" (after
    # midnight), Rahu kala and sunrise included, though they belong to that date: drop.
    while out and out[-1]["sunrise"] >= 1440 and out[-1]["rahu_kala"][0] >= 1440:
        out.pop()
    return out


def main() -> None:
    src = Path(sys.argv[1])
    dst = Path(sys.argv[2] if len(sys.argv) > 2 else "tests/golden/jhora_panchanga")
    dst.mkdir(parents=True, exist_ok=True)
    n = 0
    for f in sorted(src.glob("*.txt")):
        days = convert(f.read_text())
        (dst / f"{f.stem}.json").write_text(
            "[\n" + ",\n".join(json.dumps(d, separators=(",", ":")) for d in days) + "\n]\n")
        n += 1
    print(f"{n} charts written to {dst}")


if __name__ == "__main__":
    main()

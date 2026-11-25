# SPDX-License-Identifier: AGPL-3.0-or-later
"""Gochara against Jagannatha Hora 8.0's "Basic Transit Results" (Transits tab;
right-click the table > Standard, then > Ashtakavarga related; Copy to clipboard
each; tests/golden/jhora_transits/), one transit date per golden chart, the
transit at the birth place at 12:00 and 5:30 from GMT in the direction the chart's
own zone box shows (West for charts at or west of GMT). Checks tara, murthi, house from the
natal Moon, good house, vedha both ways, AV and SAV scores, kakshya, kakshya good
and the bindu contributors."""

import re
import sys
from datetime import datetime
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent / "golden"))
from jhora_parser import parse  # noqa: E402

from jyotishnet_engine import BirthData, DEFAULT_CONFIG, build_chart  # noqa: E402
from jyotishnet_engine.transits import gochara  # noqa: E402

GOLDEN = Path(__file__).parent / "golden"
FILES = sorted((GOLDEN / "jhora_transits").glob("*.txt"))
CODES = {"Sun": "Su", "Moon": "Mo", "Mars": "Ma", "Mercury": "Me", "Jupiter": "Ju",
         "Venus": "Ve", "Saturn": "Sa", "Rahu": "Ra", "Ketu": "Ke", "Lagna": "La"}
ABBR = {"As": "La", "Su": "Su", "Mo": "Mo", "Ma": "Ma", "Me": "Me", "Ju": "Ju", "Ve": "Ve",
        "Sa": "Sa"}
LORDS = {**CODES}


def _names(cell: str, table: dict[str, str]) -> list[str]:
    return sorted(table[x.strip()] for x in cell.split(",") if x.strip() not in ("", "-"))


def load(path: Path):
    text = path.read_text()
    m = re.search(r"Transit: (\S+ \S+) ([+-])(\d\d):(\d\d)", text)
    when = datetime.strptime(m.group(1), "%Y-%m-%d %H:%M:%S")
    offset = (1 if m.group(2) == "+" else -1) * (int(m.group(3)) + int(m.group(4)) / 60)
    std_part, av_part = text.split("Reference:")
    header = next(line for line in std_part.splitlines() if line.startswith("Planet"))
    cols = [header.index(h) for h in ("Tara", "Murthi", "House", "Under vedha from",
                                      "Causing vedha to")] + [None]
    std, av = {}, {}
    for line in std_part.splitlines():
        w = line.split()
        if not w or w[0] not in CODES or w[0] == "Lagna":
            continue
        cell = [line[cols[i]:cols[i + 1]].strip() for i in range(5)]
        house = cell[2]
        std[CODES[w[0]]] = {
            "tara": cell[0].split(" (")[0],
            "murthi": None if cell[1] == "-" else cell[1].split(" -")[0],
            "house_from_moon": int(re.match(r"\d+", house).group()),
            "good": "Good" in house,
            "vedha_from": _names(cell[3], CODES), "vedha_to": _names(cell[4], CODES),
        }
    for line in av_part.splitlines():
        w = line.split()
        if len(w) >= 5 and w[0] in CODES and w[0] != "Lagna" and w[1].isdigit():
            av[CODES[w[0]]] = {
                "av_score": int(w[1]), "sav_score": int(w[2]), "kakshya": LORDS[w[3]],
                "kakshya_good": w[4] == "1", "bindu_from": _names(" ".join(w[5:]), ABBR),
            }
    return when, offset, std, av


@pytest.mark.skipif(not FILES, reason="no JHora transit exports")
@pytest.mark.parametrize("path", FILES, ids=[f.stem for f in FILES])
def test_transits_match_jhora(path: Path):
    c = parse(GOLDEN / "jhora" / path.name)
    when, offset, std, av = load(path)
    natal = build_chart(BirthData(c.local, c.latitude, c.longitude,
                                  utc_offset_hours=c.utc_offset_hours, altitude_m=c.altitude_m),
                        DEFAULT_CONFIG, [1])
    tr = build_chart(BirthData(when, c.latitude, c.longitude, utc_offset_hours=offset,
                               altitude_m=c.altitude_m), DEFAULT_CONFIG, [1])
    got = gochara(natal, tr, DEFAULT_CONFIG)
    errors = []
    for table in (std, av):
        for p, want in table.items():
            for key, value in want.items():
                mine = getattr(got[p], key)
                mine = sorted(mine) if isinstance(mine, list) else mine
                if mine != value:
                    errors.append(f"{p} {key}: {mine} != JHora {value}")
    assert not errors, "; ".join(errors)


def test_coverage():
    assert len(FILES) in (0, 55)

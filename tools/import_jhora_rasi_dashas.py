# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Rahul Sathe
"""Convert JHora 8.0 rasi dasha exports into golden JSON files.

The exports come from the Dasas tab > Rasi dasas: for each dasha, right-click >
pick the dasha > Copy (the mahadasha list), then a click on the first and second
mahadasha rows and Copy again (their antardashas), saved one file per dasha as
    <export dir>/<chart>/<dasha>.txt   (MD list, "=====", AD of row 1, "=====", AD of row 2)

    python tools/import_jhora_rasi_dashas.py EXPORT_DIR [tests/golden/jhora_rasi_dashas]
"""

import json
import re
import sys
from pathlib import Path

SIGNS = "Ar Ta Ge Cn Le Vi Li Sc Sg Cp Aq Pi".split()
LINE = re.compile(r"^\s*(\w\w)( MD)?: (\d{4}-\d\d-\d\d) \((\d+):(\d\d):(\d\d)\) - ")


def stamp(m: re.Match) -> str:
    return f"{m.group(3)} {int(m.group(4)):02d}:{m.group(5)}:{m.group(6)}"


def convert(path: Path) -> dict:
    parts = path.read_text().split("=====")
    title = parts[0].strip().splitlines()[0].rstrip(":")
    md = [[m.group(1), stamp(m)] for m in map(LINE.match, parts[0].splitlines()) if m]
    ads = []
    for part in parts[1:]:
        head, rows = None, []
        for line in part.splitlines():
            m = LINE.match(line)
            if not m:
                continue
            if m.group(2):
                head = m.group(1)
            else:
                rows.append([m.group(1), stamp(m)])
        if head and rows:
            ads.append({"md": head, "rows": rows})
    return {"title": title, "md": md, "ad": ads}


def main() -> None:
    src = Path(sys.argv[1])
    dst = Path(sys.argv[2] if len(sys.argv) > 2 else "tests/golden/jhora_rasi_dashas")
    dst.mkdir(parents=True, exist_ok=True)
    pending = Path(__file__).parent.parent / "tests/golden/pending" / dst.name
    n = 0
    for d in sorted(p for p in src.iterdir() if (p / "done").exists()):
        if (pending / f"{d.name}.json").exists():
            print(f"{d.name}: in tests/golden/pending, skipped")
            continue
        out = {f.stem: convert(f) for f in sorted(d.glob("*.txt"))}
        body = ",\n".join(f"{json.dumps(k)}: {json.dumps(v, separators=(',', ':'))}"
                          for k, v in out.items())
        (dst / f"{d.name}.json").write_text("{\n" + body + "\n}\n")
        n += 1
    print(f"{n} charts written to {dst}")


if __name__ == "__main__":
    main()

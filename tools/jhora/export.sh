#!/bin/bash
# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Rahul Sathe
#
# Export Jagannatha Hora "complete calculations" for every .jhd chart in a
# folder, by driving JHora under Wine on a virtual X display. See README.md.
#
#   JH_PREFIX=/path/to/wineprefix PY=/path/to/python-with-xlib-and-pillow \
#     tools/jhora/export.sh charts_dir out_dir
#
# The charts are copied into the prefix (C:\charts) and each export is written
# to out_dir/<name>.txt with CRLF line ends, as JHora's own exports are.
set -u
HERE=$(cd "$(dirname "$0")" && pwd)
SRC=$1; OUT=$2
: "${JH_PREFIX:?set JH_PREFIX to the Wine prefix holding C:\\JHora}"
PY=${PY:-python3}
export WINEPREFIX=$JH_PREFIX DISPLAY=${DISPLAY_JH:-:77} WINEDEBUG=-all
WS=${WINESERVER:-/usr/lib/x86_64-linux-gnu/wine/wineserver}
X() { "$PY" "$HERE/xdrive.py" "$@"; }

mkdir -p "$OUT" "$JH_PREFIX/drive_c/charts"
cp "$SRC"/*.jhd "$JH_PREFIX/drive_c/charts/"
for f in "$SRC"/*.jhd; do
  n=$(basename "$f" .jhd)
  "$WS" -k; sleep 2
  (cd "$JH_PREFIX/drive_c/JHora/bin" && nohup wine jhora.exe "C:\\charts\\$n.jhd" > /dev/null 2>&1 &)
  ok=
  for _ in $(seq 1 40); do sleep 1; X wins 2>/dev/null | grep -q "Jagannatha Hora - $n.jhd" && { ok=1; break; }; done
  [ -z "$ok" ] && { echo "$n: window did not open"; continue; }
  sleep 4
  # Edit > Copy complete calculations (menu positions for a 1600x1000 screen).
  X click 50 41; sleep 1; X click 120 181
  ok=
  for _ in $(seq 1 30); do sleep 1; X wins 2>/dev/null | grep -q "Successfully Copied" && { ok=1; break; }; done
  [ -z "$ok" ] && { echo "$n: copy failed"; continue; }
  "$PY" "$HERE/clip.py" | sed 's/\r$//; s/$/\r/' > "$OUT/$n.txt"
  echo "$n: $(wc -l < "$OUT/$n.txt") lines; $(grep -m1 'Time Zone' "$OUT/$n.txt" | tr -d '\r')"
done
"$WS" -k

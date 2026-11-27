#!/usr/bin/env bash
# SPDX-License-Identifier: AGPL-3.0-or-later
# Build the Swiss Ephemeris as WebAssembly for the browser engine (M3.5).
#
# Uses the exact C sources pyswisseph 2.10.3.2 bundles (Swiss Ephemeris 2.10.03), so
# the browser computes what the API computes. Built with zig cc (pip package ziglang,
# pinned) for wasm32-wasi as a reactor module: no main, no Emscripten glue; the few
# WASI imports are stubbed in web/lib/engine/swe.ts. No ephemeris files: Moshier, as
# the API without SE_EPHE_PATH. The output web/public/engine/swe.wasm is committed so
# nobody else needs the toolchain; CI rebuilds it and checks it is byte-identical.
set -euo pipefail
ROOT=$(cd "$(dirname "$0")/.." && pwd)
WORK=${SWE_BUILD_DIR:-$(mktemp -d)}
OUT=${1:-$ROOT/web/public/engine/swe.wasm}
PYSWE=2.10.3.2
ZIG=0.13.0

if [ ! -x "$WORK/venv/bin/python" ]; then
  python3 -m venv "$WORK/venv"
  "$WORK/venv/bin/pip" install -q "ziglang==$ZIG"
fi
if [ ! -d "$WORK/pyswisseph-$PYSWE" ]; then
  "$WORK/venv/bin/pip" download -q "pyswisseph==$PYSWE" --no-binary :all: --no-deps -d "$WORK"
  tar xzf "$WORK/pyswisseph-$PYSWE.tar.gz" -C "$WORK"
fi
SRC="$WORK/pyswisseph-$PYSWE/libswe"
EXPORTS=(swe_calc_ut swe_set_sid_mode swe_get_ayanamsa_ut swe_houses_ex swe_rise_trans
         swe_julday swe_revjul swe_version malloc free)
LDFLAGS=()
for e in "${EXPORTS[@]}"; do LDFLAGS+=("-Wl,--export=$e"); done

"$WORK/venv/bin/python" -m ziglang cc -target wasm32-wasi -mexec-model=reactor -O2 \
  -fno-sanitize=undefined -I"$SRC" \
  "$SRC"/swecl.c "$SRC"/swedate.c "$SRC"/swehel.c "$SRC"/swehouse.c "$SRC"/swejpl.c \
  "$SRC"/swemmoon.c "$SRC"/swemplan.c "$SRC"/sweph.c "$SRC"/swephlib.c \
  "${LDFLAGS[@]}" -Wl,--strip-all -o "$OUT"
echo "built $OUT ($(wc -c < "$OUT") bytes)"

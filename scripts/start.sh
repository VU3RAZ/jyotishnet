#!/usr/bin/env bash
# SPDX-License-Identifier: AGPL-3.0-or-later
# Start the JyotishNet workbench on this computer (macOS or Linux).
# First run installs everything; later runs just start. Ctrl+C stops both parts.
# Both servers listen on 127.0.0.1 only: nothing is reachable from other machines.
set -euo pipefail
cd "$(dirname "$0")/.."
ROOT=$(pwd)
API_PORT=${JYOTISHNET_API_PORT:-8000}
WEB_PORT=${JYOTISHNET_WEB_PORT:-3000}

need() { command -v "$1" >/dev/null 2>&1 || { echo "Please install $2 first."; exit 1; }; }
need python3 "Python 3.11 or newer (https://www.python.org/downloads/)"
need npm "Node.js 20 or newer (https://nodejs.org/)"

if [ ! -d .venv ]; then
  echo "First run: setting up Python packages (a minute or two)..."
  python3 -m venv .venv
fi
# Reinstall when pyproject.toml changes (e.g. after git pull).
if [ ! -f .venv/.installed ] || [ pyproject.toml -nt .venv/.installed ]; then
  .venv/bin/pip install -q --upgrade pip
  .venv/bin/pip install -q -e .
  touch .venv/.installed
fi

cd web
if [ ! -d node_modules ] || [ package-lock.json -nt node_modules ]; then
  echo "Installing the web app's packages..."
  npm ci --silent
fi
# Rebuild when any web source is newer than the last build.
if [ ! -f .next/BUILD_ID ] || [ -n "$(find app components lib next.config.mjs package.json -newer .next/BUILD_ID -print -quit)" ]; then
  echo "Building the workbench..."
  JYOTISHNET_API_URL="http://127.0.0.1:$API_PORT" npx next build >/dev/null 2>&1 \
    || { echo "The web build failed; run 'cd web && npx next build' to see why."; exit 1; }
fi
cd "$ROOT"

cleanup() { kill "${API_PID:-}" "${WEB_PID:-}" 2>/dev/null || true; }
trap cleanup EXIT INT TERM

.venv/bin/uvicorn jyotishnet_api.main:app --host 127.0.0.1 --port "$API_PORT" --log-level warning &
API_PID=$!
JYOTISHNET_API_URL="http://127.0.0.1:$API_PORT" node web/node_modules/next/dist/bin/next start web \
  -H 127.0.0.1 -p "$WEB_PORT" >/dev/null &
WEB_PID=$!

URL="http://localhost:$WEB_PORT"
for _ in $(seq 1 60); do
  curl -fs "http://127.0.0.1:$API_PORT/health" >/dev/null 2>&1 && curl -fs "$URL" >/dev/null 2>&1 && break
  sleep 0.5
done
echo "JyotishNet workbench is running at $URL  (Ctrl+C to stop)"
# Open the browser; never let a missing browser stop the workbench.
if [ "$(uname)" = "Darwin" ]; then open "$URL" || true
else xdg-open "$URL" >/dev/null 2>&1 || true; fi
wait

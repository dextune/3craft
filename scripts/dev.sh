#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON="$ROOT/.venv/bin/python"
WEB_DIR="$ROOT/apps/web"
VITE="$WEB_DIR/node_modules/.bin/vite"

if [[ ! -x "$PYTHON" ]]; then
  echo "Missing Python environment. Run: make setup" >&2
  exit 2
fi
if [[ ! -x "$VITE" ]]; then
  echo "Missing frontend dependencies. Run: make setup" >&2
  exit 2
fi

export THREECRAFT_DATA_DIR="${THREECRAFT_DATA_DIR:-$ROOT/.threecraft-data}"
export THREECRAFT_IMAGE_PROVIDER="${THREECRAFT_IMAGE_PROVIDER:-deterministic-dev}"

api_pid=""
web_pid=""
cleanup() {
  local status=$?
  trap - EXIT INT TERM
  [[ -n "$api_pid" ]] && kill "$api_pid" 2>/dev/null || true
  [[ -n "$web_pid" ]] && kill "$web_pid" 2>/dev/null || true
  [[ -n "$api_pid" ]] && wait "$api_pid" 2>/dev/null || true
  [[ -n "$web_pid" ]] && wait "$web_pid" 2>/dev/null || true
  exit "$status"
}
trap cleanup EXIT INT TERM

cd "$ROOT"
"$PYTHON" -m uvicorn services.api.main:app --host 127.0.0.1 --port 8000 &
api_pid=$!
"$VITE" "$WEB_DIR" --host 127.0.0.1 --port 5173 --strictPort &
web_pid=$!

echo "3Craft API: http://127.0.0.1:8000/docs"
echo "3Craft Web: http://127.0.0.1:5173"
wait -n "$api_pid" "$web_pid"

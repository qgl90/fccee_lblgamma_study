#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# In restricted environments, writing to ~/Library/Caches may be blocked (macOS).
# Detect that and fall back to a local HOME inside the project so that
# appdirs/platformdirs uses a writable cache location.
_cache_probe="${HOME}/Library/Caches/snakemake/.probe"
if ! (mkdir -p "$(dirname "$_cache_probe")" && : >"$_cache_probe" && rm -f "$_cache_probe") >/dev/null 2>&1; then
  export HOME="$ROOT_DIR/work/home"
fi

export TMPDIR="${TMPDIR:-$ROOT_DIR/work/tmp}"

mkdir -p "$HOME" "$TMPDIR"

# Some CERN setups define a shell *function* called `snakemake` that sources an LCG view.
# If that view is missing, calling `snakemake` fails before the real executable is reached.
# Prefer `python3 -m snakemake` (module invocation) and otherwise bypass functions via `command`.
PYTHON_BIN="python3"
if [[ -x "$ROOT_DIR/.venv/bin/python3" ]]; then
  PYTHON_BIN="$ROOT_DIR/.venv/bin/python3"
elif [[ -x "$ROOT_DIR/.venv/bin/python" ]]; then
  PYTHON_BIN="$ROOT_DIR/.venv/bin/python"
fi

if "$PYTHON_BIN" -c "import snakemake" >/dev/null 2>&1; then
  exec "$PYTHON_BIN" -m snakemake -s "$ROOT_DIR/Snakefile" "$@"
else
  exec command snakemake -s "$ROOT_DIR/Snakefile" "$@"
fi

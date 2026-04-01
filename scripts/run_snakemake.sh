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

exec snakemake -s "$ROOT_DIR/Snakefile" "$@"

#!/usr/bin/env bash
set -euo pipefail

# Create a local Python virtualenv for Snakemake inside the repo.
# Use --system-site-packages so that ROOT from the Key4hep environment
# (needed by plots/plot_mass_overlay.py) stays importable.

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

if [[ -d ".venv" ]]; then
  echo "Found existing .venv/ (skipping creation)"
else
  python3 -m venv --system-site-packages .venv
fi

source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install --upgrade snakemake

echo "Done. Next:"
echo "  source .venv/bin/activate"
echo "  ./scripts/run_snakemake.sh -j 4"


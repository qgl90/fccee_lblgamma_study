#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
if command -v pdflatex >/dev/null 2>&1; then
  TEX_BIN=$(command -v pdflatex)
elif [[ -x /cvmfs/sft.cern.ch/lcg/external/texlive/2025/bin/x86_64-linux/pdflatex ]]; then
  TEX_BIN=/cvmfs/sft.cern.ch/lcg/external/texlive/2025/bin/x86_64-linux/pdflatex
else
  echo "pdflatex is required" >&2
  exit 2
fi
"$TEX_BIN" -interaction=nonstopmode -halt-on-error stage2_v3_armenteros_1028.tex >/dev/null
"$TEX_BIN" -interaction=nonstopmode -halt-on-error stage2_v3_armenteros_1028.tex >/dev/null
echo "$(pwd)/stage2_v3_armenteros_1028.pdf"

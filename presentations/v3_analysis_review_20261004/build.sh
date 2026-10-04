#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
if command -v pdflatex >/dev/null 2>&1; then
  TEX_BIN=$(command -v pdflatex)
else
  TEX_BIN=/cvmfs/sft.cern.ch/lcg/external/texlive/2025/bin/x86_64-linux/pdflatex
fi
"$TEX_BIN" -interaction=nonstopmode -halt-on-error v3_analysis_review_20261004.tex > build.log
"$TEX_BIN" -interaction=nonstopmode -halt-on-error v3_analysis_review_20261004.tex >> build.log
echo "$(pwd)/v3_analysis_review_20261004.pdf"

#!/usr/bin/env bash
# Create the repository-local LHCb analysis venv and its generated `run` wrapper.
set -euo pipefail

usage() {
  cat <<'EOF'
Create or validate the local analysis environment used for flattening, plots,
BDT studies, and Snakemake. FCCAnalyses itself uses the separate Key4hep Python
recorded in external/FCCAnalyses/build/CMakeCache.txt.

Usage:
  scripts/bootstrap_analysis_env.sh [ENV_DIR]

Environment:
  LB_ANALYSIS_CONDA_ENV  LbConda environment spec (default:
                         default/2026-02-05_13-08)

The default creates ENV_DIR (myenv) with lb-conda-dev virtual-env, which also
generates ENV_DIR/run. Existing environments are validated and left untouched.
EOF
}

if [[ ${1:-} == --help || ${1:-} == -h ]]; then usage; exit 0; fi
[[ $# -le 1 ]] || { usage >&2; exit 2; }

repo_dir=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
env_dir=${1:-"$repo_dir/myenv"}
if [[ "$env_dir" != /* ]]; then env_dir="$repo_dir/$env_dir"; fi
env_spec=${LB_ANALYSIS_CONDA_ENV:-default/2026-02-05_13-08}

if [[ ! -d "$env_dir" ]]; then
  command -v lb-conda-dev >/dev/null 2>&1 || {
    echo "lb-conda-dev is unavailable. Load the CERN LbEnv setup, then rerun this script." >&2
    exit 127
  }
  echo "Creating $env_dir from LbConda environment $env_spec"
  lb-conda-dev virtual-env "$env_spec" "$env_dir"
fi

[[ -x "$env_dir/run" ]] || {
  echo "Missing executable environment wrapper: $env_dir/run" >&2
  echo "Existing directory was left untouched. Choose a fresh ENV_DIR or inspect it." >&2
  exit 1
}
[[ -x "$env_dir/bin/python" ]] || {
  echo "Missing Python executable: $env_dir/bin/python" >&2
  exit 1
}

echo "Checking $env_dir through its generated run wrapper"
"$env_dir/run" python - <<'PY'
import importlib.metadata as metadata
import sys

if sys.version_info[:2] != (3, 11):
    raise SystemExit(f"Expected analysis Python 3.11; found {sys.version.split()[0]}")

modules = {
    "numpy": "numpy",
    "uproot": "uproot",
    "awkward": "awkward",
    "pyarrow": "pyarrow",
    "pandas": "pandas",
    "matplotlib": "matplotlib",
    "scikit-learn": "sklearn",
    "xgboost": "xgboost",
    "snakemake": "snakemake",
}
for distribution, module in modules.items():
    __import__(module)
    print(f"{distribution}={metadata.version(distribution)}")
print(f"analysis_python={sys.executable} ({sys.version.split()[0]})")
PY

echo "Analysis environment ready: $env_dir"
echo "Run project commands with: $env_dir/bin/python ..."

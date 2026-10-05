#!/usr/bin/env bash
# Run one ROOT input or a text list through the pinned FCCAnalyses builder.
set -euo pipefail
usage() {
  cat <<'EOF'
Run one ROOT input or a text file list through the fitted-vertex
Lambda_b -> Lambda gamma builder.

Usage:
  scripts/run_reco_preselection.sh SAMPLE INPUT_ROOT|FILE_LIST OUTPUT_ROOT EVENT_LIMIT RECO_CONFIG [NCPUS]

Arguments:
  SAMPLE       Trace label: signal_phsp, signal_physics, lbgamma_eta,
               lbgamma_eta_physics, lbgamma_pi0_phsp, lbgamma_pi0, or zbb
  INPUT_ROOT   Input EDM4hep ROOT file, or .txt/.list containing ROOT paths
  OUTPUT_ROOT  Destination ROOT file path
  EVENT_LIMIT  Total entries (1..1000), or 'all' for all listed files
  RECO_CONFIG JSON candidate selection config
  NCPUS        FCCAnalyses threads for EVENT_LIMIT=all (default: 4)

Environment:
  FCCANALYSES_PYTHON  Explicit Python executable for FCCAnalyses (optional).
                      Defaults to the interpreter recorded in FCCAnalyses'
                      build CMakeCache.txt, then python3 on PATH.
  ANALYSIS_PYTHON     Analysis/flattening Python used by post-reco steps.

List files contain one ROOT path per line; blank lines and # comments are
ignored. FCCAnalyses receives all listed ROOT paths in one run. A finite
EVENT_LIMIT is applied to the combined input chain.
EOF
}
if [[ ${1:-} == "--help" || ${1:-} == "-h" ]]; then usage; exit 0; fi
if [[ $# -lt 5 || $# -gt 6 ]]; then
  usage >&2
  exit 2
fi
sample=$1
input=$2
output=$3
event_limit=$4
reco_config=$5
ncpus=${6:-4}
repo_dir=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
cd "$repo_dir"
case "$sample" in
  signal_phsp|signal_physics|lbgamma_eta|lbgamma_eta_physics|lbgamma_pi0_phsp|lbgamma_pi0|zbb) ;;
  *) echo "Unknown sample label: $sample" >&2; exit 2 ;;
esac
inputs=()
if [[ "$input" == *.txt || "$input" == *.list ]]; then
  [[ -r "$input" ]] || { echo "Cannot read input list: $input" >&2; exit 1; }
  while IFS= read -r listed_input || [[ -n "$listed_input" ]]; do
    listed_input=${listed_input%$'\r'}
    listed_input=${listed_input#"${listed_input%%[![:space:]]*}"}
    listed_input=${listed_input%"${listed_input##*[![:space:]]}"}
    [[ -z "$listed_input" || "$listed_input" == \#* ]] && continue
    [[ -r "$listed_input" ]] || { echo "Cannot read listed ROOT file: $listed_input" >&2; exit 1; }
    [[ "$listed_input" == *.root ]] || { echo "List entry is not a .root file: $listed_input" >&2; exit 1; }
    inputs+=("$listed_input")
  done < "$input"
  (( ${#inputs[@]} > 0 )) || { echo "No ROOT paths found in list: $input" >&2; exit 1; }
else
  [[ -r "$input" ]] || { echo "Cannot read input ROOT file: $input" >&2; exit 1; }
  inputs=("$input")
fi
if [[ "$event_limit" != all ]]; then
  [[ "$event_limit" =~ ^[1-9][0-9]*$ ]] && (( event_limit <= 1000 )) || {
    echo "Use an event limit from 1 to 1,000, or 'all' for a full-file job" >&2; exit 2;
  }
  ncpus=1
fi
[[ "$ncpus" =~ ^[1-9][0-9]*$ ]] || { echo "NCPUS must be positive" >&2; exit 2; }
[[ -r "$reco_config" ]] || { echo "Missing reconstruction config: $reco_config" >&2; exit 1; }

# FCCAnalyses and its compiled dependencies must use the Python executable
# used to build that checkout (Key4hep Python 3.10 for the pinned build).
# Do not infer it from PATH: myenv is a separate Python 3.11 analysis env.
set +u
source external/FCCAnalyses/setup.sh
set -u
framework_python=${FCCANALYSES_PYTHON:-}
fcc_cmake_cache=external/FCCAnalyses/build/CMakeCache.txt
if [[ -z "$framework_python" && -r "$fcc_cmake_cache" ]]; then
  framework_python=$(sed -n 's/^_Python_EXECUTABLE:INTERNAL=//p' "$fcc_cmake_cache" | head -n 1)
fi
if [[ -z "$framework_python" ]]; then
  framework_python=$(command -v python3 || true)
fi
[[ -x "$framework_python" ]] || {
  echo "Cannot find FCCAnalyses Python. Build FCCAnalyses first or set FCCANALYSES_PYTHON to its Key4hep-stack Python executable." >&2
  exit 1
}
framework_python_version=$("$framework_python" --version 2>&1)
echo "fccanalysis_python=$framework_python ($framework_python_version)"
echo "sample=$sample"
echo "input=$input"
echo "input_files=${#inputs[@]}"
echo "events=$event_limit"
echo "ncpus=$ncpus"
echo "config=$reco_config"
echo "output=$output"
mkdir -p "$(dirname "$output")"
raw_output="outputs/analysis/studies/$(basename "$output")"
[[ ! -e "$raw_output" ]] || { echo "Output already exists: $raw_output" >&2; exit 1; }
fcc_args=(--files-list "${inputs[@]}" --output "$(basename "$raw_output")" --ncpus "$ncpus")
if [[ "$event_limit" != all ]]; then
  fcc_args+=(--nevents "$event_limit")
fi
LB_RECO_CONFIG="$reco_config" "$framework_python" \
  external/FCCAnalyses/install/bin/fccanalysis run \
  "${LB_RECO_ANALYSIS:-analysis/studies/lb2lambda_gamma_reco.py}" "${fcc_args[@]}"
if [[ "$raw_output" != "$output" ]]; then
  mv "$raw_output" "$output"
fi

#!/usr/bin/env bash
# Preview or submit v4 Stage 1 native Condor campaigns for Zbb, Zcc, Zss.
set -euo pipefail
usage() {
  cat <<'EOF'
Usage: scripts/submit_stage1_v4_zflavours.sh [--check-only|--submit]
Default: --check-only. --submit explicitly submits all three new campaigns.
Uses accounting group group_u_FCC.local_gen and workday job flavour.
EOF
}
mode=${1:---check-only}
case "$mode" in --check-only|--submit) ;; --help|-h) usage; exit 0;; *) usage >&2; exit 2;; esac
repo_dir=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
cd "$repo_dir"
set +u
source external/FCCAnalyses/setup.sh
set -u
fcc_cmake_cache=external/FCCAnalyses/build/CMakeCache.txt
framework_python=$(sed -n 's/^_Python_EXECUTABLE:INTERNAL=//p' "$fcc_cmake_cache" | head -n 1)
[[ -x "$framework_python" ]] || { echo "FCCAnalyses build Python missing" >&2; exit 1; }
if [[ "$mode" == --submit ]]; then
  command -v condor_submit >/dev/null || { echo "condor_submit unavailable on this host" >&2; exit 1; }
fi
unset LB_RECO_CONFIG
run_tag=stage1_v4_pointing_20261005
for flavour in Zbb Zcc Zss; do
  lower=${flavour,,}
  input_glob="/eos/experiment/fcc/ee/generation/DelphesEvents/winter2023/IDEA/p8_ee_${flavour}_ecm91/events_*.root"
  output_eos="/eos/lhcb/lbdt3/user/rquaglia/fcc_ee/lblgamma/outputs/${lower}_full_condor/${run_tag}"
  args=(run analysis/studies/analysis_preselection_v4.py
    --input-glob "$input_glob" --chunks 1200
    --comp-group group_u_FCC.local_gen --queue workday --ncpus 4
    --output-eos "$output_eos" --eos-type eoslhcb)
  if [[ "$mode" == --check-only ]]; then args+=(--check-only); fi
  echo "sample=$flavour accounting_group=group_u_FCC.local_gen job_flavour=workday chunks=1200 output=$output_eos"
  "$framework_python" external/FCCAnalyses/install/bin/fccanalysis "${args[@]}"
done

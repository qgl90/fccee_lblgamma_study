#!/usr/bin/env bash
# Check or run bounded v5 Stage-1 samples; Condor mode is check-only.
set -euo pipefail

usage() {
  cat <<'EOF'
Usage:
  scripts/run_stage1_v5_samples.sh --list
  scripts/run_stage1_v5_samples.sh --check [SAMPLE ...]
  scripts/run_stage1_v5_samples.sh --run [--events N] SAMPLE [...]
  scripts/run_stage1_v5_samples.sh --condor-check [zbb|zcc|zss ...]

Samples: zbb zcc zss signal_physics signal_phsp lbgamma_pi0 lbgamma_eta
Direct runs default to 1,000 events and are capped at 1,000 by the Stage-1
wrapper. Outputs and logs go under /tmp/rquaglia/fccee_lblgamma_study/stage1_v5.
--condor-check validates the full Z input globs and creates no jobs.
EOF
}

repo_dir=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
cd "$repo_dir"
eos=/eos/lhcb/lbdt3/user/rquaglia/fcc_ee/lblgamma/outputs
gen=/eos/experiment/fcc/ee/generation/DelphesEvents/winter2023/IDEA
out_base=${V5_OUTPUT_BASE:-/tmp/rquaglia/fccee_lblgamma_study/stage1_v5}
config=${LB_RECO_CONFIG:-config/lb_reco_v5_training.json}
analysis=analysis/studies/lb2lambda_gamma_reco_v5.py
events=1000
action=${1:---list}
shift || true

declare -A inputs=(
  [signal_physics]="$eos/Lb2LambdaGammaPhysics_nev100000_IDEA_edm4hep.root"
  [signal_phsp]="$eos/Lb2LambdaGamma_nev100000_IDEA_edm4hep.root"
  [lbgamma_pi0]="$eos/stage0_v3_pseudoscalar_physics_100k_20261004/Lb2LambdaPi0Physics_nev100000_IDEA_edm4hep.root"
  [lbgamma_eta]="$eos/stage0_v3_pseudoscalar_physics_100k_20261004/Lb2LambdaEtaPhysics_nev100000_IDEA_edm4hep.root"
)
declare -A zflavours=(
  [zbb]=Zbb [zcc]=Zcc [zss]=Zss
)

if [[ "$action" == --run && ${1:-} == --events ]]; then
  events=${2:-}; shift 2
  [[ "$events" =~ ^[1-9][0-9]*$ ]] && (( events <= 1000 )) || { echo '--events must be 1..1000' >&2; exit 2; }
fi

if [[ "$action" == --list ]]; then
  printf '%s\n' "Direct samples (default events=$events):" "  signal_physics -> ${inputs[signal_physics]}" "  signal_phsp -> ${inputs[signal_phsp]}" "  lbgamma_pi0 -> ${inputs[lbgamma_pi0]}" "  lbgamma_eta -> ${inputs[lbgamma_eta]}" "Condor samples (check-only): zbb zcc zss"
  exit 0
fi

if [[ "$action" == --condor-check ]]; then
  flavours=("$@")
  ((${#flavours[@]})) || flavours=(zbb zcc zss)
  for sample in "${flavours[@]}"; do
    [[ -n ${zflavours[$sample]:-} ]] || { echo "Unknown Z sample: $sample" >&2; exit 2; }
    flavour=${zflavours[$sample]}
    dest="$eos/${sample}_full_condor/stage1_v5_flavtag_20261006"
    args=(run analysis/studies/analysis_preselection_v5.py
      --input-glob "$gen/p8_ee_${flavour}_ecm91/events_*.root"
      --chunks 1200 --comp-group group_u_FCC.local_gen --queue workday
      --ncpus 4 --output-eos "$dest" --eos-type eoslhcb --check-only)
    echo "CHECK $sample -> $dest"
    ( set +u; source external/FCCAnalyses/setup.sh; set -u
      external/FCCAnalyses/install/bin/fccanalysis "${args[@]}" )
  done
  exit 0
fi

case "$action" in --check|--run) ;; --help|-h) usage; exit 0;; *) usage >&2; exit 2;; esac
samples=("$@")
((${#samples[@]})) || { echo 'Choose at least one direct sample.' >&2; usage >&2; exit 2; }
[[ -r "$config" ]] || { echo "Missing v5 config: $config" >&2; exit 1; }
for sample in "${samples[@]}"; do
  input=${inputs[$sample]:-}
  [[ -n "$input" ]] || { echo "Unknown direct sample: $sample" >&2; exit 2; }
  [[ -r "$input" ]] || { echo "MISSING input: $sample -> $input" >&2; exit 1; }
  output="$out_base/${sample}_${events}_stage1_v5.root"
  echo "READY $sample input=$input output=$output events=$events config=$config"
  if [[ "$action" == --run ]]; then
    mkdir -p "$out_base/logs"
    LB_RECO_ANALYSIS="$analysis" scripts/run_reco_preselection.sh \
      "$sample" "$input" "$output" "$events" "$config" 1 \
      > "$out_base/logs/${sample}_${events}.log" 2>&1
    echo "DONE $sample log=$out_base/logs/${sample}_${events}.log"
  fi
done

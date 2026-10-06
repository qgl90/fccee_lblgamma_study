#!/usr/bin/env bash
# Run selected Stage 0 or v5 Stage 1 chunks from the 1M Physics campaign.
set -euo pipefail
repo_dir=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
cd "$repo_dir"
usage() {
  cat <<'EOF'
Usage:
  scripts/run_lbgamma_physics_1m.sh stage0 --check --chunks 0,1
  scripts/run_lbgamma_physics_1m.sh stage0 --run --executor local|condor --chunks 0,1
  scripts/run_lbgamma_physics_1m.sh stage1 --check --chunks 0,1
  scripts/run_lbgamma_physics_1m.sh stage1 --run --executor local|condor --chunks 0,1

The campaign is ten independent 100k jobs (1,000,000 generated events total).
Stage 0 output can be redirected with LB_DELPHES_OUTPUT_DIR.
Stage 1 Condor jobs use FCCAnalyses runBatch through a processList.
EOF
}
stage=${1:-}; action=${2:-}; shift 2 || true
executor=local; chunks_arg=
while (($#)); do
  case "$1" in
    --chunks) chunks_arg=${2:?missing chunk list}; shift 2 ;;
    --executor) executor=${2:?missing executor}; shift 2 ;;
    --help|-h) usage; exit 0 ;;
    *) usage >&2; exit 2 ;;
  esac
done
[[ "$stage" == stage0 || "$stage" == stage1 ]] || { usage >&2; exit 2; }
[[ "$action" == --check || "$action" == --run ]] || { usage >&2; exit 2; }
[[ -n "$chunks_arg" ]] || { echo '--chunks is required' >&2; exit 2; }
IFS=, read -r -a chunks <<< "$chunks_arg"
declare -A seen=()
for chunk in "${chunks[@]}"; do
  [[ "$chunk" =~ ^[0-9]+$ ]] && (( chunk < 10 )) || { echo "invalid chunk id: $chunk" >&2; exit 2; }
  [[ -z ${seen[$chunk]:-} ]] || { echo "duplicate chunk id: $chunk" >&2; exit 2; }
  seen[$chunk]=1
done

sample=Lb2LambdaGammaPhysics; total=1000000; chunk_events=100000; seed_base=72601
stage0_dir=${LB_DELPHES_OUTPUT_DIR:-/eos/lhcb/lbdt3/user/rquaglia/fcc_ee/lblgamma/outputs/stage0_lbgamma_physics_1m_20261006}
stage1_eos=${LB_STAGE1_OUTPUT_EOS:-/eos/lhcb/lbdt3/user/rquaglia/fcc_ee/lblgamma/outputs/stage1_v5_lbgamma_physics_1m_20261006}
if [[ "$stage" == stage0 ]]; then
  [[ "$executor" == local || "$executor" == condor ]] || { echo 'executor must be local or condor' >&2; exit 2; }
  queue=work/condor/lbgamma_physics_1m.queue
  mkdir -p "$(dirname "$queue")"
  : > "$queue"
  for chunk in "${chunks[@]}"; do
    seed=$((seed_base+chunk))
    output="$stage0_dir/chunks/${sample}_nev${total}_chunk${chunk}_IDEA_edm4hep.root"
    if [[ -s "$output" ]]; then echo "EXISTS $output"; else echo "READY chunk=$chunk seed=$seed events=$chunk_events -> $output"; fi
    printf '%s %s %s %s %s\n' "$sample" "$chunk" "$seed" "$chunk_events" "$total" >> "$queue"
    if [[ "$action" == --run && "$executor" == local ]]; then
      LB_DELPHES_OUTPUT_DIR="$stage0_dir" bash scripts/produce_chunk.sh "$sample" "$chunk" "$seed" "$chunk_events" "$total"
    fi
  done
  if [[ "$action" == --run && "$executor" == condor ]]; then
    mkdir -p outputs/logs/condor
    LB_DELPHES_OUTPUT_DIR="$stage0_dir" condor_submit scripts/condor_lbgamma_physics_1m.sub
  fi
  exit 0
fi

input_dir="$stage0_dir/chunks"
for chunk in "${chunks[@]}"; do
  input="$input_dir/${sample}_nev${total}_chunk${chunk}_IDEA_edm4hep.root"
  [[ -s "$input" ]] || { echo "MISSING Stage 0 chunk: $input" >&2; exit 1; }
  echo "READY chunk=$chunk input=$input"
done
[[ "$action" == --run ]] || exit 0
[[ "$executor" == local || "$executor" == condor ]] || { echo 'executor must be local or condor' >&2; exit 2; }

export LB_STAGE1_CHUNKS="$chunks_arg"
export LB_STAGE1_INPUT_DIR="$input_dir"
export LB_STAGE1_EXECUTOR="$executor"
export LB_RECO_CONFIG="$repo_dir/config/lb_reco_v5_training.json"
export LB_STAGE1_OUTPUT_DIR=${LB_STAGE1_OUTPUT_DIR:-/tmp/rquaglia/fccee_lblgamma_study/stage1_v5_lbgamma_physics_1m_20261006}
if [[ "$executor" == condor ]]; then
  export LB_STAGE1_OUTPUT_EOS="$stage1_eos"
  export LB_STAGE1_QUEUE=workday
  export LB_STAGE1_ACCOUNTING_GROUP=group_u_FCC.local_gen
fi
set +u
source external/FCCAnalyses/setup.sh
set -u
external/FCCAnalyses/install/bin/fccanalysis run analysis/studies/analysis_stage1_v5_physics_processlist.py

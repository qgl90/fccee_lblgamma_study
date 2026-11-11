#!/usr/bin/env bash
# Generate and/or v5-reconstruct selected 1M forced-decay campaigns.
set -euo pipefail
repo_dir=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
cd "$repo_dir"

usage() {
  cat <<'EOF'
Usage:
  scripts/run_lbgamma_physics_1m.sh stage0 --check [--samples LIST] --chunks LIST
  scripts/run_lbgamma_physics_1m.sh stage0 --run --executor local|condor [--jobs N] [--events-per-chunk N] [--samples LIST] --chunks LIST
  scripts/run_lbgamma_physics_1m.sh stage1 --check [--samples LIST] --chunks LIST
  scripts/run_lbgamma_physics_1m.sh stage1 --run --executor local|condor [--samples LIST] --chunks LIST

Samples (comma-separated):
  Lb2LambdaGamma         PHSP gamma
  Lb2LambdaGammaPhysics  HELAMP Physics gamma
  Lb2LambdaEtaPhysics    HELAMP Physics eta background
  Lb2LambdaPi0Physics    HELAMP Physics pi0 background

Each sample is 100 x 10k events (1M). Stage 0 can run locally in parallel or
submit to Condor. Set LB_DELPHES_OUTPUT_DIR to override the shared EOS chunk
directory.
Stage 1 uses v5 and writes to LB_STAGE1_OUTPUT_EOS on Condor.
EOF
}

stage=${1:-}; action=${2:-}; shift 2 || true
executor=local; chunks_arg=; samples_arg=Lb2LambdaGammaPhysics; jobs=4
chunk_events=10000
while (($#)); do
  case "$1" in
    --chunks) chunks_arg=${2:?missing chunk list}; shift 2 ;;
    --samples) samples_arg=${2:?missing sample list}; shift 2 ;;
    --executor) executor=${2:?missing executor}; shift 2 ;;
    --jobs) jobs=${2:?missing job count}; shift 2 ;;
    --events-per-chunk) chunk_events=${2:?missing event count}; shift 2 ;;
    --help|-h) usage; exit 0 ;;
    *) usage >&2; exit 2 ;;
  esac
done
[[ "$stage" == stage0 || "$stage" == stage1 ]] || { usage >&2; exit 2; }
[[ "$action" == --check || "$action" == --run ]] || { usage >&2; exit 2; }
[[ -n "$chunks_arg" ]] || { echo '--chunks is required' >&2; exit 2; }
[[ "$jobs" =~ ^[1-9][0-9]*$ ]] || { echo '--jobs must be positive' >&2; exit 2; }
[[ "$chunk_events" =~ ^[1-9][0-9]*$ ]] || { echo '--events-per-chunk must be positive' >&2; exit 2; }
[[ "$executor" == local || "$executor" == condor ]] || { echo 'executor must be local or condor' >&2; exit 2; }

declare -A seed_base=(
  [Lb2LambdaGamma]=72701
  [Lb2LambdaGammaPhysics]=72601
  [Lb2LambdaEtaPhysics]=72801
  [Lb2LambdaPi0Physics]=72901
)
IFS=, read -r -a samples <<< "$samples_arg"
((${#samples[@]})) || { echo 'No samples selected' >&2; exit 2; }
declare -A seen_samples=()
for sample in "${samples[@]}"; do
  [[ -n ${seed_base[$sample]:-} ]] || { echo "unsupported sample: $sample" >&2; exit 2; }
  [[ -z ${seen_samples[$sample]:-} ]] || { echo "duplicate sample: $sample" >&2; exit 2; }
  seen_samples[$sample]=1
done

total=1000000
(( total % chunk_events == 0 )) || { echo 'events-per-chunk must divide 1000000 exactly' >&2; exit 2; }
IFS=, read -r -a chunks <<< "$chunks_arg"
declare -A seen_chunks=()
for chunk in "${chunks[@]}"; do
  [[ "$chunk" =~ ^[0-9]+$ ]] && (( chunk < total / chunk_events )) || { echo "invalid chunk id: $chunk" >&2; exit 2; }
  [[ -z ${seen_chunks[$chunk]:-} ]] || { echo "duplicate chunk id: $chunk" >&2; exit 2; }
  seen_chunks[$chunk]=1
done

stage0_dir=${LB_DELPHES_OUTPUT_DIR:-/eos/lhcb/lbdt3/user/rquaglia/fcc_ee/lblgamma/outputs/stage0_v5_forced_modes_1m_20261006}
stage1_eos=${LB_STAGE1_OUTPUT_EOS:-/eos/lhcb/lbdt3/user/rquaglia/fcc_ee/lblgamma/outputs/stage1_v5_forced_modes_1m_20261006}
stage1_local=${LB_STAGE1_OUTPUT_DIR:-/tmp/rquaglia/fccee_lblgamma_study/stage1_v5_forced_modes_1m_20261006}
input_dir="$stage0_dir/chunks"

if [[ "$stage" == stage0 ]]; then
  queue=work/condor/lbgamma_v5_forced_modes_1m.queue
  mkdir -p "$(dirname "$queue")"
  : > "$queue"
  declare -a local_commands=()
  for sample in "${samples[@]}"; do
    for chunk in "${chunks[@]}"; do
      seed=$((seed_base[$sample]+chunk))
      output="$input_dir/${sample}_nev${total}_chunk${chunk}_IDEA_edm4hep.root"
      partial="${output}.partial.root"
      if [[ -s "$output" ]]; then
        echo "EXISTS $output"
        continue
      fi
      if [[ -e "$partial" ]]; then
        echo "PARTIAL (not queued; inspect or let the active job finish) $partial"
        continue
      fi
      echo "READY sample=$sample chunk=$chunk seed=$seed events=$chunk_events -> $output"
      printf '%s %s %s %s %s\n' "$sample" "$chunk" "$seed" "$chunk_events" "$total" >> "$queue"
      if [[ "$action" == --run && "$executor" == local ]]; then
        local_commands+=("$sample $chunk $seed")
      fi
    done
  done
  if [[ "$action" == --run && "$executor" == local ]]; then
    pids=(); pending=0; failed=0
    wait_batch() {
      local pid
      for pid in "${pids[@]}"; do wait "$pid" || failed=1; done
      pids=(); pending=0
    }
    for row in "${local_commands[@]}"; do
      read -r sample chunk seed <<< "$row"
      LB_DELPHES_OUTPUT_DIR="$stage0_dir" \
        LB_PRODUCTION_LOG_DIR=${LB_PRODUCTION_LOG_DIR:-outputs/logs/lbgamma_v5_forced_modes_1m_20261006} \
        bash scripts/produce_chunk.sh "$sample" "$chunk" "$seed" "$chunk_events" "$total" &
      pids+=("$!"); ((pending+=1))
      if (( pending >= jobs )); then wait_batch; fi
    done
    ((${#pids[@]} == 0)) || wait_batch
    (( failed == 0 )) || { echo 'One or more Stage 0 chunks failed; inspect production logs.' >&2; exit 1; }
  elif [[ "$action" == --run && "$executor" == condor ]]; then
    mkdir -p outputs/logs/condor
    if [[ -s "$queue" ]]; then
      condor_submit STAGE0_OUTPUT_DIR="$stage0_dir" \
        scripts/stage0_condor.sub
    else
      echo 'No absent Stage 0 chunks to submit.'
    fi
  fi
  exit 0
fi

for sample in "${samples[@]}"; do
  for chunk in "${chunks[@]}"; do
    input="$input_dir/${sample}_nev${total}_chunk${chunk}_IDEA_edm4hep.root"
    [[ -s "$input" ]] || { echo "MISSING Stage 0 chunk: $input" >&2; exit 1; }
    echo "READY sample=$sample chunk=$chunk input=$input"
  done
done
[[ "$action" == --run ]] || exit 0

if [[ "$executor" == condor ]]; then
  queue=work/condor/lbgamma_v5_stage1.queue
  mkdir -p "$(dirname "$queue")" outputs/logs/condor
  : > "$queue"
  for sample in "${samples[@]}"; do
    for chunk in "${chunks[@]}"; do
      input="$input_dir/${sample}_nev${total}_chunk${chunk}_IDEA_edm4hep.root"
      output_dir="$stage1_eos/${sample}_nev${total}_chunk${chunk}_IDEA_edm4hep"
      output_url="root://eoslhcb.cern.ch//${output_dir#/}/chunk_0.root"
      mkdir -p "$output_dir"
      printf '%s %s %s %s %s\n' "$sample" "$chunk" \
        "root://eoslhcb.cern.ch//${input#/}" "$output_dir" "$output_url" >> "$queue"
    done
  done
  condor_submit STAGE1_OUTPUT_EOS="$stage1_eos" \
    scripts/stage1_v5_condor.sub
  exit 0
fi

export LB_STAGE1_CHUNKS="$chunks_arg"
export LB_STAGE1_SAMPLES="$samples_arg"
export LB_STAGE1_INPUT_DIR="$input_dir"
export LB_STAGE1_EXECUTOR="$executor"
export LB_RECO_CONFIG="$repo_dir/config/lb_reco_v5_training.json"
export LB_STAGE1_OUTPUT_DIR="$stage1_local"
if [[ "$executor" == condor ]]; then
  export LB_STAGE1_OUTPUT_EOS="$stage1_eos"
  export LB_STAGE1_QUEUE=workday
  export LB_STAGE1_ACCOUNTING_GROUP=group_u_FCC.local_gen
fi
set +u
source external/FCCAnalyses/setup.sh
set -u
external/FCCAnalyses/install/bin/fccanalysis run analysis/studies/analysis_stage1_v5_physics_processlist.py

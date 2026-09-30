#!/usr/bin/env bash
# Reconstruct a range of independent cached Winter2023 IDEA Zbb files.
# One ROOT output per source file preserves a stable source_id for ML splits.
set -euo pipefail
repo_dir=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
cd "$repo_dir"
manifest=${1:-outputs/analysis/studies/Zbb_winter2023_baseline_manifest.files.txt}
threads_per_file=${2:-4}
parallel_files=${3:-10}
output_tag=${ZBB_OUTPUT_TAG:-Zbb_winter2023_IDEA_100k}
[[ "$threads_per_file" =~ ^[1-9][0-9]*$ && "$parallel_files" =~ ^[1-9][0-9]*$ ]] || exit 2
mapfile -t files < "$manifest"
[[ ${#files[@]} -gt 0 ]] || { echo "Empty manifest: $manifest" >&2; exit 1; }
start_index=${4:-0}
end_index=${5:-$((${#files[@]}-1))}
[[ "$start_index" =~ ^[0-9]+$ && "$end_index" =~ ^[0-9]+$ ]] || exit 2
(( start_index <= end_index && end_index < ${#files[@]} )) || {
  echo "Invalid source index range $start_index..$end_index for ${#files[@]} files" >&2
  exit 2
}
mkdir -p outputs/logs
pids=()
indices=()
failed=0
for ((index=start_index; index<=end_index; index++)); do
  printf -v label '%02d' "$index"
  output="outputs/analysis/studies/${output_tag}_chunk${label}.root"
  log="outputs/logs/${output_tag}_chunk${label}.log"
  if [[ -e "$output" ]]; then
    if [[ -s "$output" && -f "$log" ]] &&
       rg -q 'Total events processed:.*100,000' "$log"; then
      echo "Keeping completed $output"
      continue
    fi
    echo "Existing output is incomplete or currently running: $output" >&2
    exit 1
  fi
  echo "Launching source $index: ${files[$index]}"
  ZBB_FILE_LIST="$manifest" bash scripts/run_zbb_file_chunk.sh "$index" "$threads_per_file" \
    > "$log" 2>&1 &
  pids+=("$!")
  indices+=("$index")
  if (( ${#pids[@]} >= parallel_files )); then
    for slot in "${!pids[@]}"; do
      if ! wait "${pids[$slot]}"; then
        echo "Failed source ${indices[$slot]}: outputs/logs/${output_tag}_chunk$(printf '%02d' "${indices[$slot]}").log" >&2
        failed=1
      fi
    done
    pids=()
    indices=()
  fi
done
for slot in "${!pids[@]}"; do
  if ! wait "${pids[$slot]}"; then
    echo "Failed source ${indices[$slot]}" >&2
    failed=1
  fi
done
(( failed == 0 )) || exit 1
echo "Zbb reconstruction complete; one output per source file."

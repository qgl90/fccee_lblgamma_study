#!/usr/bin/env bash
# Run one generated job card. The same text card is accepted locally and by Condor.
set -euo pipefail

usage() {
  cat <<'EOF'
Run the Zbb batch described in a generated plain-text job card.

Usage:
  scripts/run_zbb_preselection_shard.sh JOB_CARD.txt

The card contains batch_index, batch_list, source_manifest, output_dir, ncpus,
event_limit, and reco_config key=value lines. Generate the batch lists and
cards with studies/reconstruction/split_input_file_list.py --help.
EOF
}
if [[ ${1:-} == "--help" || ${1:-} == "-h" ]]; then usage; exit 0; fi
[[ $# -eq 1 ]] || { usage >&2; exit 2; }
job_card=$1
[[ -r "$job_card" ]] || { echo "Cannot read job card: $job_card" >&2; exit 1; }
job_card="$(cd "$(dirname "$job_card")" && pwd)/$(basename "$job_card")"
repo_dir=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
cd "$repo_dir"

declare -A card=()
while IFS= read -r line || [[ -n "$line" ]]; do
  line=${line%$'\r'}
  line=${line#"${line%%[![:space:]]*}"}
  line=${line%"${line##*[![:space:]]}"}
  [[ -z "$line" || "$line" == \#* ]] && continue
  [[ "$line" == *=* ]] || { echo "Invalid job-card line: $line" >&2; exit 2; }
  key=${line%%=*}
  value=${line#*=}
  key=${key//[[:space:]]/}
  value=${value#"${value%%[![:space:]]*}"}
  value=${value%"${value##*[![:space:]]}"}
  [[ -n "$key" && -n "$value" ]] || { echo "Empty key/value in job card: $line" >&2; exit 2; }
  [[ -z ${card[$key]+present} ]] || { echo "Duplicate job-card key: $key" >&2; exit 2; }
  card[$key]=$value
done < "$job_card"

for key in batch_index batch_list source_manifest output_dir ncpus event_limit reco_config; do
  [[ -n ${card[$key]+present} ]] || { echo "Missing job-card key: $key" >&2; exit 2; }
done
batch_index=${card[batch_index]}
batch_list=${card[batch_list]}
source_manifest=${card[source_manifest]}
output_dir=${card[output_dir]}
ncpus=${card[ncpus]}
event_limit=${card[event_limit]}
reco_config=${card[reco_config]}
[[ "$batch_index" =~ ^[0-9]+$ && "$ncpus" =~ ^[1-9][0-9]*$ ]] || {
  echo "batch_index and ncpus must be nonnegative/positive integers" >&2; exit 2;
}
if [[ "$event_limit" != all ]]; then
  [[ "$event_limit" =~ ^[1-9][0-9]*$ ]] && (( event_limit <= 1000 )) || {
    echo "event_limit must be 'all' or an integer from 1 to 1,000" >&2; exit 2;
  }
  ncpus=1
fi
[[ -s "$batch_list" ]] || { echo "Missing batch list: $batch_list" >&2; exit 1; }
[[ -s "$source_manifest" ]] || { echo "Missing source manifest: $source_manifest" >&2; exit 1; }
[[ -r "$reco_config" ]] || { echo "Missing reconstruction config: $reco_config" >&2; exit 1; }

trimmed_paths() {
  local path
  while IFS= read -r path || [[ -n "$path" ]]; do
    path=${path%$'\r'}
    path=${path#"${path%%[![:space:]]*}"}
    path=${path%"${path##*[![:space:]]}"}
    [[ -z "$path" || "$path" == \#* ]] && continue
    printf '%s\n' "$path"
  done < "$1"
}

declare -A source_id=()
manifest_paths=()
while IFS= read -r input; do
  [[ -z ${source_id[$input]+present} ]] || { echo "Duplicate path in source manifest: $input" >&2; exit 2; }
  source_id[$input]=${#manifest_paths[@]}
  manifest_paths+=("$input")
done < <(trimmed_paths "$source_manifest")
batch_paths=()
while IFS= read -r input; do
  [[ -n ${source_id[$input]+present} ]] || { echo "Batch input is missing from source manifest: $input" >&2; exit 2; }
  batch_paths+=("$input")
done < <(trimmed_paths "$batch_list")
(( ${#batch_paths[@]} > 0 )) || { echo "Batch list has no input files: $batch_list" >&2; exit 2; }

python_bin=${ANALYSIS_PYTHON:-myenv/bin/python}
mkdir -p "$output_dir/logs"
printf 'job_card=%s batch=%s files=%s source_files=%s event_limit=%s config=%s output=%s\n' \
  "$job_card" "$batch_index" "${#batch_paths[@]}" "${#manifest_paths[@]}" \
  "$event_limit" "$reco_config" "$output_dir"

for ((local_index=0; local_index<${#batch_paths[@]}; local_index++)); do
  input=${batch_paths[$local_index]}
  global_source_id=${source_id[$input]}
  prefix="$output_dir/zbb_file_$(printf '%04d' "$local_index")"
  root="${prefix}_reco.root"
  parquet="${prefix}_candidates.parquet"
  if [[ -s "${prefix}_summary.json" && -s "${prefix}_selected.parquet" ]]; then
    echo "Keeping completed source_id=$global_source_id input=$input"
    continue
  fi
  for output in "$root" "$parquet" "${prefix}_selected.parquet"; do
    [[ ! -e "$output" ]] || { echo "Partial output exists; inspect or remove it: $output" >&2; exit 1; }
  done
  log_prefix="$output_dir/logs/file_$(printf '%04d' "$local_index")"
  bash scripts/run_reco_preselection.sh zbb "$input" "$root" "$event_limit" \
    "$reco_config" "$ncpus" > "${log_prefix}_reco.log" 2>&1
  env -u PYTHONPATH -u PYTHONHOME "$python_bin" \
    studies/reconstruction/flatten_candidates.py --mode gamma --input "$root" \
    --output "$parquet" --source-id "$global_source_id" --chunk-events 500 \
    > "${log_prefix}_flatten.log" 2>&1
  env -u PYTHONPATH -u PYTHONHOME "$python_bin" \
    studies/reconstruction/preselect_candidates.py --input "$parquet" \
    --output-prefix "$prefix" > "${log_prefix}_preselection.log" 2>&1
  echo "Finished source_id=$global_source_id input=$input"
done
printf 'batch_index=%s\nfiles=%s\nsource_files=%s\nbatch_list=%s\nsource_manifest=%s\nevent_limit=%s\n' \
  "$batch_index" "${#batch_paths[@]}" "${#manifest_paths[@]}" \
  "$batch_list" "$source_manifest" "$event_limit" > "$output_dir/SHARD_COMPLETE.txt"

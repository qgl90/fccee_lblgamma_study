#!/usr/bin/env bash
# Reconstruct a deterministic contiguous subset of full Winter2023 Zbb files.
set -euo pipefail
usage() {
  cat <<'EOF'
Process one Zbb file shard. Each ROOT file is reconstructed separately so its
source_id remains available for independent-file BDT splits.

Usage:
  scripts/run_zbb_preselection_shard.sh SHARD_INDEX FILE_LIST [N_SHARDS] [NCPUS] [OUTPUT_DIR]

Arguments:
  SHARD_INDEX  Zero-based shard number
  FILE_LIST    Complete ordered list of central Zbb ROOT files
  N_SHARDS     Total shards (default: 600)
  NCPUS        FCCAnalyses threads per shard (default: 4)
  OUTPUT_DIR   Shared output root (default: outputs/analysis/studies/zbb_preselection15)

Environment:
  LB_RECO_CONFIG  Reconstruction config (default: the 15 MeV, 4.5–6.5 GeV config)
  ANALYSIS_PYTHON Python with awkward/uproot/pyarrow (default: myenv/bin/python)

The manifest paths must be readable on the worker. Use a shared filesystem or
configure Condor file transfer for the source and output paths before submission.
EOF
}
if [[ ${1:-} == "--help" || ${1:-} == "-h" ]]; then usage; exit 0; fi
if [[ $# -lt 2 || $# -gt 5 ]]; then usage >&2; exit 2; fi
shard=$1
file_list=$2
shards=${3:-600}
ncpus=${4:-4}
output_dir=${5:-outputs/analysis/studies/zbb_preselection15}
[[ "$shard" =~ ^[0-9]+$ && "$shards" =~ ^[1-9][0-9]*$ && "$ncpus" =~ ^[1-9][0-9]*$ ]] || {
  echo "Shard, shard count, and CPU count must be nonnegative/positive integers" >&2; exit 2;
}
[[ -s "$file_list" ]] || { echo "Missing file list: $file_list" >&2; exit 1; }
mapfile -t files < "$file_list"
total=${#files[@]}
(( shard < shards )) || { echo "SHARD_INDEX must be less than N_SHARDS" >&2; exit 2; }
start=$(( shard * total / shards ))
stop=$(( (shard + 1) * total / shards ))
(( start < stop )) || { echo "Shard $shard has no files ($total files / $shards shards)" >&2; exit 2; }
repo_dir=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
cd "$repo_dir"
reco_config=${LB_RECO_CONFIG:-config/lb_reco_preselection_15mev_45_65.json}
python_bin=${ANALYSIS_PYTHON:-myenv/bin/python}
shard_dir="$output_dir/shard_$(printf '%03d' "$shard")"
mkdir -p "$shard_dir/logs"
printf 'shard=%s/%s files=%s range=[%s,%s) config=%s\n' \
  "$shard" "$shards" "$total" "$start" "$stop" "$reco_config"
for ((index=start; index<stop; index++)); do
  input=${files[$index]}
  prefix="$shard_dir/zbb_file_$(printf '%04d' "$index")"
  root="${prefix}_reco.root"
  parquet="${prefix}_candidates.parquet"
  if [[ -s "${prefix}_summary.json" && -s "${prefix}_selected.parquet" ]]; then
    echo "Keeping completed file index $index: $input"
    continue
  fi
  for output in "$root" "$parquet" "${prefix}_selected.parquet"; do
    [[ ! -e "$output" ]] || { echo "Partial output exists; inspect or remove it: $output" >&2; exit 1; }
  done
  bash scripts/run_reco_preselection.sh zbb "$input" "$root" all \
    "$reco_config" "$ncpus" > "$shard_dir/logs/file_$(printf '%04d' "$index")_reco.log" 2>&1
  env -u PYTHONPATH -u PYTHONHOME "$python_bin" \
    studies/reconstruction/flatten_candidates.py --mode gamma --input "$root" \
    --output "$parquet" --source-id "$index" --chunk-events 500 \
    > "$shard_dir/logs/file_$(printf '%04d' "$index")_flatten.log" 2>&1
  env -u PYTHONPATH -u PYTHONHOME "$python_bin" \
    studies/reconstruction/preselect_candidates.py --input "$parquet" \
    --output-prefix "$prefix" \
    > "$shard_dir/logs/file_$(printf '%04d' "$index")_preselection.log" 2>&1
  echo "Finished source_id=$index input=$input"
done
printf '%s\n' "$shard" "$shards" "$total" "$start" "$stop" > "$shard_dir/SHARD_COMPLETE.txt"

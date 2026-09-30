#!/usr/bin/env bash
# One independently restartable job for a single file from the verified
# winter2023 IDEA p8_ee_Zbb_ecm91 million-event manifest. Supply a zero-based
# file index; a batch scheduler can launch indices 0..9 concurrently.
set -euo pipefail

if [[ $# -lt 1 || ! "$1" =~ ^[0-9]+$ ]]; then
  echo "Usage: bash scripts/run_zbb_file_chunk.sh FILE_INDEX [NCPUS]" >&2
  exit 2
fi
index="$1"
ncpus="${2:-4}"
output_tag="${ZBB_OUTPUT_TAG:-Zbb_winter2023_IDEA_100k}"
repo_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_dir"
file_list="${ZBB_FILE_LIST:-outputs/analysis/studies/Zbb_winter2023_baseline_manifest.files.txt}"
mapfile -t input_files < "$file_list"
if (( index >= ${#input_files[@]} )); then
  echo "Index $index is outside 0..$((${#input_files[@]} - 1))" >&2
  exit 2
fi
input_file="${input_files[$index]}"
if [[ ! -r "$input_file" ]]; then
  echo "Cannot read ROOT input: $input_file" >&2
  exit 1
fi
printf -v label '%02d' "$index"
cached="$repo_dir/work/cache/winter2023_zbb/$(basename "$input_file")"
[[ -f "$cached" && ! -L "$cached" ]] || {
  echo "Missing local cache: $cached; run scripts/cache_zbb_inputs.sh" >&2; exit 1;
}
[[ $(stat -c%s "$cached") == $(stat -c%s "$input_file") ]] || {
  echo "Incomplete local cache: $cached" >&2; exit 1;
}
set +u # The pinned Key4hep setup reads several optional unset variables.
source external/FCCAnalyses/setup.sh
set -u
fccanalysis run analysis/studies/lb2lambda_gamma_reco.py \
  --files-list "$cached" \
  --output "${output_tag}_chunk${label}.root" \
  --ncpus "$ncpus"

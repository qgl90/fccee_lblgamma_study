#!/usr/bin/env bash
# Run the unchanged Lambda_b -> Lambda0 gamma selection on the pinned generic
# winter2023 IDEA Zbb file list. The manifest is prepared and checked by
# studies/reconstruction/catalog_zbb_winter2023.py. No truth selection is used.
set -euo pipefail

repo_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_dir"

file_list="${1:-outputs/analysis/studies/Zbb_winter2023_baseline_manifest.files.txt}"
output_name="${2:-Zbb_winter2023_IDEA_baseline_1m.root}"
ncpus="${3:-40}"
if [[ ! -s "$file_list" ]]; then
  echo "Missing or empty input file list: $file_list" >&2
  exit 1
fi
mapfile -t input_files < "$file_list"
if [[ ${#input_files[@]} -eq 0 ]]; then
  echo "No ROOT files in $file_list" >&2
  exit 1
fi
for input_file in "${input_files[@]}"; do
  if [[ ! -r "$input_file" ]]; then
    echo "Cannot read ROOT input: $input_file" >&2
    exit 1
  fi
done

# The pinned fccanalysis CLI rewrites /eos/ paths into root://. Even symlinks
# can trigger remote opens in MT, so require exact-size local cached copies.
local_files=()
for index in "${!input_files[@]}"; do
  cached="$repo_dir/work/cache/winter2023_zbb/$(basename "${input_files[$index]}")"
  [[ -f "$cached" && ! -L "$cached" ]] || {
    echo "Missing local cache: $cached; run scripts/cache_zbb_inputs.sh" >&2; exit 1;
  }
  [[ $(stat -c%s "$cached") == $(stat -c%s "${input_files[$index]}") ]] || {
    echo "Incomplete local cache: $cached" >&2; exit 1;
  }
  local_files+=("$cached")
done

set +u # The pinned Key4hep setup reads several optional unset variables.
source external/FCCAnalyses/setup.sh
set -u
# Omit --nevents: this pinned FCCAnalyses version disables multithreading
# when a finite event limit is requested. The ten verified files contain
# exactly 1,000,000 entries and are listed explicitly in the manifest.
fccanalysis run analysis/studies/lb2lambda_gamma_reco.py \
  --files-list "${local_files[@]}" \
  --output "$output_name" --ncpus "$ncpus"

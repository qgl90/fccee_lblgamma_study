#!/usr/bin/env bash
# Independent Winter2023 IDEA Zbb tail validation for frozen BDT and NN cuts.
# Default: source files 10..19, an additional 1,000,000 generated Zbb events.
# Run each stage separately or use all; existing completed outputs are kept.
set -euo pipefail
repo_dir=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
cd "$repo_dir"
stage=${1:-help}
start=${START_INDEX:-10}
end=${END_INDEX:-19}
manifest=${EXTENSION_MANIFEST:-outputs/analysis/studies/Zbb_winter2023_extension20_manifest.files.txt}
base=${BDT_STUDY_DIR:-outputs/analysis/studies/bdt_winter2023_v1}
nn_dir=${NN_STUDY_DIR:-outputs/analysis/studies/nn_winter2023_v1}
extension_dir=${EXTENSION_OUTPUT_DIR:-$nn_dir/extension_${start}_${end}}
python_bin=${ANALYSIS_PYTHON:-myenv/bin/python}
case "$stage" in
  catalog)
    env -u PYTHONPATH -u PYTHONHOME "$python_bin" \
      studies/reconstruction/catalog_zbb_winter2023.py \
      --output "${manifest%.files.txt}.json" \
      --target-events $(( (end+1)*100000 )) --max-files $((end+1))
    ;;
  cache)
    bash scripts/cache_zbb_inputs.sh "$manifest"
    ;;
  reconstruct)
    bash scripts/run_zbb_training_chunks.sh "$manifest" \
      "${ZBB_THREADS_PER_FILE:-4}" "${ZBB_PARALLEL_FILES:-10}" "$start" "$end"
    ;;
  flatten)
    for ((index=start; index<=end; index++)); do
      printf -v label '%02d' "$index"
      input="outputs/analysis/studies/Zbb_winter2023_IDEA_100k_chunk${label}.root"
      output="outputs/analysis/studies/Zbb_winter2023_IDEA_100k_chunk${label}.parquet"
      if [[ -s "$output" ]]; then echo "Keeping $output"; continue; fi
      [[ -s "$input" ]] || { echo "Missing reconstruction $input" >&2; exit 1; }
      env -u PYTHONPATH -u PYTHONHOME "$python_bin" \
        studies/reconstruction/flatten_candidates.py --mode gamma \
        --input "$input" --output "$output" --source-id "$index" --chunk-events 500
    done
    ;;
  score)
    inputs=()
    for ((index=start; index<=end; index++)); do
      printf -v label '%02d' "$index"
      inputs+=("outputs/analysis/studies/Zbb_winter2023_IDEA_100k_chunk${label}.parquet")
    done
    env -u PYTHONPATH -u PYTHONHOME "$python_bin" \
      studies/reconstruction/score_zbb_extension.py \
      --inputs "${inputs[@]}" \
      --bdt-model "$base/model/bdt_model.json" \
      --bdt-metrics "$base/model/metrics.json" \
      --bdt-scored "$base/model/scored_candidates.parquet" \
      --nn-dir "$nn_dir" --yield-config config/yield_projection.json \
      --events-per-file 100000 --output-dir "$extension_dir"
    ;;
  all)
    for next in catalog cache reconstruct flatten score; do
      echo "===== $next ====="
      bash "$0" "$next"
    done
    ;;
  *)
    echo "Usage: bash $0 {catalog|cache|reconstruct|flatten|score|all}" >&2
    exit 2
    ;;
esac

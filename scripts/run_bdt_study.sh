#!/usr/bin/env bash
# Stage-by-stage, restartable Lambda_b -> Lambda gamma BDT study.
# Usage: bash scripts/run_bdt_study.sh STAGE
# Stages: provenance, catalog, cache, generate, reco_forced, reco_zbb,
#         flatten, dataset, statistics, train, angular, projection, slides, all.
set -euo pipefail
repo_dir=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
cd "$repo_dir"
stage=${1:-help}
tag=${STUDY_TAG:-bdt_winter2023_v1}
lambda_half_window=${LAMBDA_HALF_WINDOW_GEV:-.010}
lb_mass_min=${LB_MASS_MIN_GEV:-4.9}
lb_mass_max=${LB_MASS_MAX_GEV:-6.3}
events=${FORCED_EVENTS:-10000}
threads=${FORCED_THREADS:-8}
zbb_threads=${ZBB_THREADS_PER_FILE:-4}
zbb_jobs=${ZBB_PARALLEL_FILES:-10}
zbb_output_tag=${ZBB_OUTPUT_TAG:-Zbb_winter2023_IDEA_100k}
python_bin=${ANALYSIS_PYTHON:-myenv/bin/python}
manifest=outputs/analysis/studies/Zbb_winter2023_baseline_manifest.json
file_list=outputs/analysis/studies/Zbb_winter2023_baseline_manifest.files.txt
study_dir="outputs/analysis/studies/$tag"
plot_dir="outputs/plots/reconstruction/$tag"
mkdir -p "$study_dir" "$plot_dir" outputs/logs

signal_edm=${SIGNAL_EDM:-outputs/delphes/chunks/Lb2LambdaGamma_nev${events}_chunk0_IDEA_edm4hep.root}
eta_edm=${ETA_EDM:-outputs/delphes/chunks/Lb2LambdaEta_nev${events}_chunk0_IDEA_edm4hep.root}
physics_edm=${PHYSICS_EDM:-outputs/delphes/chunks/Lb2LambdaGammaPhysics_nev${events}_chunk0_IDEA_edm4hep.root}
signal_root="outputs/analysis/studies/${tag}_signal_phsp.root"
eta_root="outputs/analysis/studies/${tag}_eta_as_gamma.root"
physics_root="outputs/analysis/studies/${tag}_signal_helamp.root"
signal_parquet=${SIGNAL_PARQUET:-outputs/analysis/studies/${tag}_signal_phsp.parquet}
eta_parquet=${ETA_PARQUET:-outputs/analysis/studies/${tag}_eta_as_gamma.parquet}
physics_parquet=${PHYSICS_PARQUET:-outputs/analysis/studies/${tag}_signal_helamp.parquet}

case "$stage" in
  provenance)
    {
      date -u '+created_utc=%Y-%m-%dT%H:%M:%SZ'
      printf 'fccanalyses_branch='; git -C external/FCCAnalyses branch --show-current
      printf 'fccanalyses_commit='; git -C external/FCCAnalyses rev-parse HEAD
      printf 'analysis_python=%s\n' "$python_bin"
      printf 'lb_reco_config=%s\nlambda_half_window_gev=%s\nlb_mass_range_gev=%s,%s\nzbb_output_tag=%s\n' \
        "${LB_RECO_CONFIG:-config/lb_reco.json}" "$lambda_half_window" \
        "$lb_mass_min" "$lb_mass_max" "$zbb_output_tag"
      "$python_bin" -c 'import xgboost,sklearn,pyarrow; print("xgboost="+xgboost.__version__); print("sklearn="+sklearn.__version__); print("pyarrow="+pyarrow.__version__)'
      sha256sum cards/card_IDEA.tcl cards/edm4hep_IDEA.tcl \
        evtgen/Lb2LambdaGamma.dec evtgen/Lb2LambdaGamma_trpol.dec \
        evtgen/Lb2LambdaEta.dec config/lb_reco.json \
        config/lb_observables.json config/yield_projection.json
      if [[ "${LB_RECO_CONFIG:-config/lb_reco.json}" != config/lb_reco.json ]]; then
        sha256sum "$LB_RECO_CONFIG"
      fi
    } > "$study_dir/provenance.txt"
    echo "$study_dir/provenance.txt"
    ;;
  catalog)
    if [[ ! -s "$file_list" ]]; then
      "$python_bin" studies/reconstruction/catalog_zbb_winter2023.py \
        --output "$manifest" --target-events 1000000 --max-files 10
    fi
    [[ $(wc -l < "$file_list") == 10 ]] || { echo "Expected ten Zbb files" >&2; exit 1; }
    echo "$file_list"
    ;;
  cache)
    bash scripts/cache_zbb_inputs.sh "$file_list"
    ;;
  generate)
    [[ "$events" =~ ^[1-9][0-9]*$ ]] || exit 2
    bash scripts/produce_chunk.sh Lb2LambdaGamma 0 71501 "$events" "$events"
    bash scripts/produce_chunk.sh Lb2LambdaEta 0 71502 "$events" "$events"
    bash scripts/produce_chunk.sh Lb2LambdaGammaPhysics 0 71424 "$events" "$events"
    ;;
  reco_forced)
    for input in "$signal_edm" "$eta_edm" "$physics_edm"; do
      [[ -r "$input" ]] || { echo "Missing forced EDM4hep input: $input" >&2; exit 1; }
      "$python_bin" scripts/check_root_entries.py "$input" "$events"
    done
    set +u
    source external/FCCAnalyses/setup.sh > "$study_dir/fccanalysis_setup.log" 2>&1
    set -u
    for mode in signal eta physics; do
      case "$mode" in
        signal) input=$signal_edm; output=$signal_root ;;
        eta) input=$eta_edm; output=$eta_root ;;
        physics) input=$physics_edm; output=$physics_root ;;
      esac
      if [[ -s "$output" ]]; then echo "Keeping $output"; continue; fi
      echo "Reconstructing $mode: $input"
      fccanalysis run analysis/studies/lb2lambda_gamma_reco.py \
        --files-list "$input" --output "$(basename "$output")" --ncpus "$threads" \
        > "$study_dir/reco_${mode}.log" 2>&1
      [[ -s "$output" ]] || { echo "Missing reconstruction output $output" >&2; exit 1; }
    done
    ;;
  reco_zbb)
    ZBB_OUTPUT_TAG="$zbb_output_tag" bash scripts/run_zbb_training_chunks.sh "$file_list" "$zbb_threads" "$zbb_jobs"
    ;;
  flatten)
    for mode in signal eta physics; do
      case "$mode" in
        signal) input=$signal_root; output=$signal_parquet; sid=100 ;;
        eta) input=$eta_root; output=$eta_parquet; sid=101 ;;
        physics) input=$physics_root; output=$physics_parquet; sid=102 ;;
      esac
      if [[ -s "$output" ]]; then echo "Keeping $output"; continue; fi
      [[ -s "$input" ]] || { echo "Missing ROOT reconstruction: $input" >&2; exit 1; }
      env -u PYTHONPATH -u PYTHONHOME "$python_bin" \
        studies/reconstruction/flatten_candidates.py --mode gamma \
        --input "$input" --output "$output" --source-id "$sid" --chunk-events 500
    done
    for index in $(seq 0 9); do
      printf -v label '%02d' "$index"
      input="outputs/analysis/studies/${zbb_output_tag}_chunk${label}.root"
      output="outputs/analysis/studies/${zbb_output_tag}_chunk${label}.parquet"
      if [[ -s "$output" ]]; then echo "Keeping $output"; continue; fi
      [[ -s "$input" ]] || { echo "Missing Zbb ROOT reconstruction: $input" >&2; exit 1; }
      env -u PYTHONPATH -u PYTHONHOME "$python_bin" \
        studies/reconstruction/flatten_candidates.py --mode gamma \
        --input "$input" --output "$output" --source-id "$index" --chunk-events 500
    done
    ;;
  dataset)
    zbb_parquets=()
    for index in $(seq 0 9); do
      printf -v label '%02d' "$index"
      zbb_parquets+=("outputs/analysis/studies/${zbb_output_tag}_chunk${label}.parquet")
    done
    env -u PYTHONPATH -u PYTHONHOME "$python_bin" \
      studies/reconstruction/prepare_bdt_dataset.py \
      --signal "$signal_parquet" --eta "$eta_parquet" \
      --zbb "${zbb_parquets[@]}" --output-dir "$study_dir" \
      --signal-input-events "$events" --eta-input-events "$events" \
      --zbb-events-per-file 100000 --lambda-half-window "$lambda_half_window" \
      --lb-mass-min "$lb_mass_min" --lb-mass-max "$lb_mass_max"
    ;;
  statistics)
    env -u PYTHONPATH -u PYTHONHOME "$python_bin" \
      studies/reconstruction/estimate_zbb_statistics.py \
      --manifest "$study_dir/manifest.json" \
      --yield-config config/yield_projection.json \
      --signal-relative-efficiency .8 --test-fraction .2 \
      --output "$study_dir/statistics_needed.json"
    ;;
  train)
    physics_args=()
    if [[ -s "$physics_parquet" ]]; then
      physics_args=(--physics "$physics_parquet" --physics-input-events "$events")
    fi
    env -u PYTHONPATH -u PYTHONHOME "$python_bin" \
      studies/reconstruction/train_postlambda_bdt.py \
      --input "$study_dir/candidate_audit_postlambda.parquet" \
      --manifest "$study_dir/manifest.json" \
      --yield-config config/yield_projection.json \
      --output-dir "$study_dir/model" "${physics_args[@]}"
    ;;
  angular)
    env -u PYTHONPATH -u PYTHONHOME "$python_bin" \
      studies/reconstruction/plot_bdt_angle_acceptance.py \
      --phsp-mc "$signal_edm" --phsp-events "$events" \
      --scored "$study_dir/model/scored_candidates.parquet" \
      --metrics "$study_dir/model/metrics.json" \
      --physics-mc "$physics_edm" --physics-events "$events" \
      --physics-scored "$study_dir/model/physics_scored_candidates.parquet" \
      --output-dir "$study_dir/model"
    ;;
  projection)
    env -u PYTHONPATH -u PYTHONHOME "$python_bin" \
      studies/reconstruction/plot_yield_projection.py \
      --input "$study_dir/candidate_audit_stage1.parquet" \
      --config config/yield_projection.json \
      --input-manifest "$study_dir/manifest.json" \
      --output-dir "$plot_dir/yield_projection"
    env -u PYTHONPATH -u PYTHONHOME "$python_bin" \
      studies/reconstruction/plot_bdt_yield_projection.py \
      --scored "$study_dir/model/scored_candidates.parquet" \
      --metrics "$study_dir/model/metrics.json" \
      --output-dir "$plot_dir/yield_projection"
    ;;
  slides)
    env -u PYTHONPATH -u PYTHONHOME "$python_bin" \
      slides/build_full_study_pdf.py --study-dir "$study_dir" \
      --plot-dir "$plot_dir" --output "slides/${tag}.pdf"
    ;;
  all)
    for next in provenance catalog cache generate reco_forced reco_zbb flatten dataset statistics train angular projection slides; do
      echo "===== $next ====="
      bash "$0" "$next"
    done
    ;;
  *)
    echo "Usage: bash $0 {provenance|catalog|cache|generate|reco_forced|reco_zbb|flatten|dataset|statistics|train|angular|projection|slides|all}" >&2
    exit 2
    ;;
esac

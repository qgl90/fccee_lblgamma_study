#!/usr/bin/env bash
# Restartable post-Lambda neural-network comparison on the frozen BDT dataset.
# Usage: bash scripts/run_nn_study.sh {provenance|train|statistics|angular|projection|slides|all}
set -euo pipefail
repo_dir=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
cd "$repo_dir"
stage=${1:-help}
study_tag=${STUDY_TAG:-bdt_winter2023_v1}
base="outputs/analysis/studies/$study_tag"
nn_dir="outputs/analysis/studies/${NN_TAG:-nn_winter2023_v1}"
nn_plot="outputs/plots/reconstruction/${NN_TAG:-nn_winter2023_v1}"
python_bin=${ANALYSIS_PYTHON:-myenv/bin/python}
physics_parquet=${PHYSICS_PARQUET:-outputs/analysis/studies/Lb2LambdaGammaPhysics_10k_bdt.parquet}
signal_edm=${SIGNAL_EDM:-outputs/delphes/Lb2LambdaGamma_nev500000_IDEA_edm4hep.root}
physics_edm=${PHYSICS_EDM:-outputs/delphes/chunks/Lb2LambdaGammaPhysics_nev10000_chunk0_IDEA_edm4hep.root}
events=${FORCED_EVENTS:-10000}
mkdir -p "$nn_dir" "$nn_plot"
case "$stage" in
  provenance)
    {
      date -u '+created_utc=%Y-%m-%dT%H:%M:%SZ'
      printf 'fccanalyses_branch='; git -C external/FCCAnalyses branch --show-current
      printf 'fccanalyses_commit='; git -C external/FCCAnalyses rev-parse HEAD
      "$python_bin" -c 'import tensorflow,sklearn; print("tensorflow="+tensorflow.__version__); print("sklearn="+sklearn.__version__)'
      sha256sum studies/reconstruction/train_postlambda_nn.py \
        studies/reconstruction/nn_preprocessing.py \
        "$base/manifest.json" "$base/model/metrics.json" \
        config/yield_projection.json config/lb_reco.json
    } > "$nn_dir/provenance.txt" 2> "$nn_dir/provenance_stderr.log"
    echo "$nn_dir/provenance.txt"
    ;;
  train)
    bash "$0" provenance
    env -u PYTHONPATH -u PYTHONHOME "$python_bin" \
      studies/reconstruction/train_postlambda_nn.py \
      --input "$base/candidate_audit_postlambda.parquet" \
      --manifest "$base/manifest.json" \
      --bdt-metrics "$base/model/metrics.json" \
      --bdt-scored "$base/model/scored_candidates.parquet" \
      --physics "$physics_parquet" --physics-input-events "$events" \
      --yield-config config/yield_projection.json --output-dir "$nn_dir"
    ;;
  statistics)
    env -u PYTHONPATH -u PYTHONHOME "$python_bin" \
      studies/reconstruction/plan_nn_purity_statistics.py \
      --metrics "$nn_dir/metrics.json" \
      --yield-config config/yield_projection.json \
      --campaign-manifest outputs/analysis/studies/Zbb_winter2023_baseline_manifest.json \
      --threshold sig80 --output "$nn_dir/statistics_needed.json"
    ;;
  angular)
    env -u PYTHONPATH -u PYTHONHOME "$python_bin" \
      studies/reconstruction/plot_bdt_angle_acceptance.py \
      --phsp-mc "$signal_edm" --phsp-events "$events" \
      --scored "$nn_dir/scored_candidates.parquet" \
      --metrics "$nn_dir/metrics.json" \
      --physics-mc "$physics_edm" --physics-events "$events" \
      --physics-scored "$nn_dir/physics_scored_candidates.parquet" \
      --score-column nn_score --method NN --output-dir "$nn_dir"
    ;;
  projection)
    env -u PYTHONPATH -u PYTHONHOME "$python_bin" \
      studies/reconstruction/plot_bdt_yield_projection.py \
      --scored "$nn_dir/scored_candidates.parquet" \
      --metrics "$nn_dir/metrics.json" --score-column nn_score --method NN \
      --output-dir "$nn_plot"
    ;;
  slides)
    env -u PYTHONPATH -u PYTHONHOME "$python_bin" \
      slides/build_nn_update_pdf.py --nn-dir "$nn_dir" --plot-dir "$nn_plot" \
      --output "slides/${NN_TAG:-nn_winter2023_v1}.pdf"
    ;;
  all)
    for next in train statistics angular projection slides; do
      echo "===== $next ====="
      bash "$0" "$next"
    done
    ;;
  *)
    echo "Usage: bash $0 {provenance|train|statistics|angular|projection|slides|all}" >&2
    exit 2
    ;;
esac

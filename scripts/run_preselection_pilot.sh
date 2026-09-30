#!/usr/bin/env bash
# Paired baseline/scenario check on the same local signal and Winter2023 Zbb events.
set -euo pipefail
if [[ ${1:-} == "--help" || ${1:-} == "-h" ]]; then
  cat <<'EOF'
Run paired baseline and requested-preselection reconstructions on
signal_phsp, signal_physics, lbgamma_eta, and Winter2023 Zbb.

Usage:
  scripts/run_preselection_pilot.sh [EVENT_LIMIT]

Arguments:
  EVENT_LIMIT  Events per input, from 1 to 1000 (default: 1000)

Environment:
  PRESELECTION_TAG  Output-name prefix (default: nominal_preselection_pilotEVENT_LIMIT)
  SIGNAL_PHSP_EDM   Forced PHSP Lambda_b -> Lambda gamma EDM4hep input
  SIGNAL_PHYSICS_EDM Forced physics-model Lambda_b -> Lambda gamma input
  LBGAMMA_ETA_EDM   Forced Lambda_b -> Lambda eta EDM4hep input
  ZBB_EDM           Local Winter2023 Zbb EDM4hep input
  ANALYSIS_PYTHON   Python with uproot/awkward/pyarrow (default: myenv/bin/python)

Outputs go to outputs/analysis/studies and outputs/analysis/studies/TAG.
The script refuses to overwrite existing ROOT or Parquet tables.
EOF
  exit 0
fi
repo_dir=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
cd "$repo_dir"
events=${1:-1000}
[[ "$events" =~ ^[1-9][0-9]*$ ]] && (( events <= 1000 )) || {
  echo "Pilot event limit must be 1..1000" >&2; exit 2;
}
tag=${PRESELECTION_TAG:-nominal_preselection_pilot${events}}
declare -A inputs=(
  [signal_phsp]=${SIGNAL_PHSP_EDM:-outputs/delphes/Lb2LambdaGamma_nev500000_IDEA_edm4hep.root}
  [signal_physics]=${SIGNAL_PHYSICS_EDM:-outputs/delphes/chunks/Lb2LambdaGammaPhysics_nev10000_chunk0_IDEA_edm4hep.root}
  [lbgamma_eta]=${LBGAMMA_ETA_EDM:-outputs/delphes/Lb2LambdaEta_nev500000_IDEA_edm4hep.root}
  [zbb]=${ZBB_EDM:-work/cache/winter2023_zbb/events_000083138.root}
)
python_bin=${ANALYSIS_PYTHON:-myenv/bin/python}
for input in "${inputs[@]}"; do
  [[ -r "$input" ]] || { echo "Missing input: $input" >&2; exit 1; }
done
study_dir="outputs/analysis/studies/$tag"
mkdir -p "$study_dir"
{
  date -u '+created_utc=%Y-%m-%dT%H:%M:%SZ'
  printf 'event_limit=%s\n' "$events"
  for sample in signal_phsp signal_physics lbgamma_eta zbb; do
    printf '%s=%s\n' "$sample" "${inputs[$sample]}"
  done
  printf 'fccanalyses_revision='; git -C external/FCCAnalyses rev-parse HEAD
  sha256sum config/lb_reco.json config/lb_reco_preselection_15mev_45_65.json \
    config/lb_observables.json cards/card_IDEA.tcl "${inputs[@]}"
} > "$study_dir/provenance.txt"
set +u
source external/FCCAnalyses/setup.sh > "$study_dir/setup.log" 2>&1
set -u
for scenario in baseline requested15; do
  case "$scenario" in
    baseline) config=config/lb_reco.json ;;
    requested15) config=config/lb_reco_preselection_15mev_45_65.json ;;
  esac
  for sample in signal_phsp signal_physics lbgamma_eta zbb; do
    input=${inputs[$sample]}
    case "$sample" in
      signal_phsp) sid=100 ;;
      signal_physics) sid=101 ;;
      lbgamma_eta) sid=102 ;;
      zbb) sid=0 ;;
    esac
    name="${tag}_${scenario}_${sample}"
    root="outputs/analysis/studies/${name}.root"
    parquet="outputs/analysis/studies/${name}.parquet"
    [[ ! -e "$root" && ! -e "$parquet" ]] || {
      echo "Output exists: $root or $parquet; choose a new PRESELECTION_TAG" >&2; exit 1;
    }
    LB_RECO_CONFIG="$config" fccanalysis run analysis/studies/lb2lambda_gamma_reco.py \
      --files-list "$input" --output "${name}.root" --nevents "$events" --ncpus 1 \
      > "$study_dir/${scenario}_${sample}_reco.log" 2>&1
    env -u PYTHONPATH -u PYTHONHOME "$python_bin" \
      studies/reconstruction/flatten_candidates.py --mode gamma \
      --input "$root" --output "$parquet" --source-id "$sid" --chunk-events 500 \
      > "$study_dir/${scenario}_${sample}_flatten.log"
    env -u PYTHONPATH -u PYTHONHOME "$python_bin" \
      studies/reconstruction/preselect_candidates.py --input "$parquet" \
      --output-prefix "$study_dir/${scenario}_${sample}" \
      > "$study_dir/${scenario}_${sample}_preselect.log"
  done
done
echo "Pilot tables, cut summaries, logs, and provenance: $study_dir"

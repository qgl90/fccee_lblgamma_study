#!/usr/bin/env bash
# Finish the frozen-model 7M-event independent Zbb validation in the background.
# Files 10..19 may already be reconstructing; wait for their verified logs,
# then process files 20..77, flatten, score, and refresh the review deck.
set -euo pipefail
repo_dir=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
cd "$repo_dir"
manifest=outputs/analysis/studies/Zbb_winter2023_extension78_manifest.files.txt
[[ $(wc -l < "$manifest") == 78 ]] || { echo "Expected 78-file manifest" >&2; exit 1; }
log(){ date -u '+%Y-%m-%dT%H:%M:%SZ'; printf '%s\n' "$*"; }
log "Waiting for source files 10..19 to finish reconstruction"
deadline=$(( $(date +%s) + 6*3600 ))
while :; do
  complete=0
  for ((index=10;index<=19;index++)); do
    label=$(printf '%02d' "$index")
    root="outputs/analysis/studies/Zbb_winter2023_IDEA_100k_chunk${label}.root"
    source_log="outputs/logs/zbb_training_chunk${label}.log"
    if [[ -s "$root" && -s "$source_log" ]] &&
       rg -q 'Total events processed:.*100,000' "$source_log"; then
      ((complete+=1))
    fi
  done
  (( complete==10 )) && break
  if (( $(date +%s) >= deadline )); then
    echo "First ten extension files incomplete after six hours: $complete/10" >&2
    exit 1
  fi
  sleep 60
done
log "First ten extension files complete; reconstructing source files 20..77"
START_INDEX=20 END_INDEX=77 EXTENSION_MANIFEST="$manifest" \
  bash scripts/run_nn_zbb_extension.sh reconstruct
log "Reconstruction complete; flattening source files 10..77"
START_INDEX=10 END_INDEX=77 EXTENSION_MANIFEST="$manifest" \
  bash scripts/run_nn_zbb_extension.sh flatten
log "Flattening complete; scoring frozen BDT and NN"
START_INDEX=10 END_INDEX=77 EXTENSION_MANIFEST="$manifest" \
  bash scripts/run_nn_zbb_extension.sh score
log "Scoring complete; rebuilding NN review slides"
bash scripts/run_nn_study.sh slides
log "Extended independent test complete"

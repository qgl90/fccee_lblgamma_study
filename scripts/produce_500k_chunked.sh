#!/usr/bin/env bash
# Direct Bash alternative to the Snakefile's 10 x 50k chunked production.
set -euo pipefail

repo_dir=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
cd "$repo_dir"
jobs=${1:-20}
[[ "$jobs" =~ ^[1-9][0-9]*$ ]] || { echo "Usage: bash $0 [positive_parallel_jobs]" >&2; exit 2; }
[[ -z ${KEY4HEP_STACK:-} ]] || { echo "Run without a sourced Key4hep stack" >&2; exit 2; }

tasks=()
for chunk in {0..9}; do
    tasks+=("Lb2LambdaGamma $chunk $((22345 + chunk)) 50000 500000")
    tasks+=("Lb2LambdaEta $chunk $((22355 + chunk)) 50000 500000")
done
printf '%s\n' "${tasks[@]}" | xargs -P "$jobs" -n 5 bash scripts/produce_chunk.sh
bash scripts/merge_chunks.sh Lb2LambdaGamma 500000 10
bash scripts/merge_chunks.sh Lb2LambdaEta 500000 10

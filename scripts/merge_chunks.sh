#!/usr/bin/env bash
# Merge checked EDM4hep chunks into one checked final sample.
set -euo pipefail

repo_dir=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
cd "$repo_dir"

if (( $# != 3 )); then
    echo "Usage: bash $0 SAMPLE TOTAL_EVENTS NCHUNKS" >&2
    exit 2
fi
sample=$1
total_events=$2
nchunks=$3
[[ "$sample" == Lb2LambdaGamma || "$sample" == Lb2LambdaGammaPhysics ||
   "$sample" == Lb2LambdaEta ]] || exit 2
[[ "$total_events" =~ ^[1-9][0-9]*$ && "$nchunks" =~ ^[1-9][0-9]*$ ]] || exit 2
(( total_events % nchunks == 0 )) || { echo "Total events must divide evenly" >&2; exit 2; }
chunk_events=$((total_events / nchunks))
[[ -z ${KEY4HEP_STACK:-} ]] || { echo "Run without a sourced Key4hep stack" >&2; exit 2; }

stack=${GEN_SETUP:-/cvmfs/sw.hsf.org/spackages7/key4hep-stack/2023-04-08/x86_64-centos7-gcc11.2.0-opt/urwcv/setup.sh}
output="outputs/delphes/${sample}_nev${total_events}_IDEA_edm4hep.root"
partial="${output}.partial.root"
log="outputs/logs/${sample}_nev${total_events}.merge.log"
inputs=()
for (( chunk=0; chunk<nchunks; chunk++ )); do
    file="outputs/delphes/chunks/${sample}_nev${total_events}_chunk${chunk}_IDEA_edm4hep.root"
    [[ -s "$file" ]] || { echo "Missing chunk: $file" >&2; exit 1; }
    inputs+=("$file")
done

set +u
source "$stack" > "$log" 2>&1
set -u
if [[ -e "$output" ]]; then
    python3 scripts/check_root_entries.py "$output" "$total_events"
    echo "Existing verified merged sample: $output"
    exit 0
fi
[[ ! -e "$partial" ]] || { echo "Incomplete merge exists: $partial" >&2; exit 1; }
{
    hadd "$partial" "${inputs[@]}"
    python3 scripts/check_root_entries.py "$partial" "$total_events"
} >> "$log" 2>&1
mv "$partial" "$output"
echo "Completed merged sample: $output ($nchunks x $chunk_events events)"

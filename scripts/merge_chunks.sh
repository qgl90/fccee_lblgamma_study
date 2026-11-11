#!/usr/bin/env bash
# Merge checked EDM4hep chunks into one checked final sample.
set -euo pipefail

repo_dir=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
cd "$repo_dir"

usage() {
    cat <<'EOF'
Merge and validate ordered EDM4hep chunks for one generated sample.

Usage:
  bash scripts/merge_chunks.sh SAMPLE TOTAL_EVENTS NCHUNKS

SAMPLE is Lb2LambdaGamma, Lb2LambdaGammaPhysics,
Lb2LambdaEta, Lb2LambdaEtaPhysics, Lb2LambdaPi0,
or Lb2LambdaPi0Physics.
TOTAL_EVENTS must divide evenly by NCHUNKS. Inputs are read from
outputs/delphes/chunks/ and the merged file is written under outputs/delphes/.
Set GEN_SETUP to choose the Key4hep generation setup script.
EOF
}
if [[ ${1:-} == "--help" || ${1:-} == "-h" ]]; then usage; exit 0; fi
if (( $# != 3 )); then
    usage >&2
    exit 2
fi
sample=$1
total_events=$2
nchunks=$3
[[ "$sample" == Lb2LambdaGamma || "$sample" == Lb2LambdaGammaPhysics ||
   "$sample" == Lb2LambdaEta || "$sample" == Lb2LambdaEtaPhysics ||
   "$sample" == Lb2LambdaPi0 || "$sample" == Lb2LambdaPi0Physics ]] || exit 2
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
if [[ -e "$partial" ]]; then
    if python3 scripts/check_root_entries.py "$partial" "$total_events"; then
        mv "$partial" "$output"
        echo "Recovered verified merged sample: $output"
        exit 0
    fi
    echo "Partial merge is not complete; inspect or remove it before retrying: $partial" >&2
    exit 1
fi
{
    hadd "$partial" "${inputs[@]}"
    python3 scripts/check_root_entries.py "$partial" "$total_events"
} >> "$log" 2>&1
mv "$partial" "$output"
echo "Completed merged sample: $output ($nchunks x $chunk_events events)"

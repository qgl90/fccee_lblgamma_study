#!/usr/bin/env bash
# Produce one independent Pythia8/EvtGen/Delphes EDM4hep chunk.
set -euo pipefail

repo_dir=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
cd "$repo_dir"

usage() {
    cat <<'EOF'
Produce and validate one independent Pythia8/EvtGen/Delphes chunk.

Usage:
  bash scripts/produce_chunk.sh SAMPLE CHUNK SEED CHUNK_EVENTS TOTAL_EVENTS

Samples: Lb2LambdaGamma, Lb2LambdaGammaPhysics, Lb2LambdaEta
Outputs: outputs/delphes/chunks/ and outputs/logs/.
Set GEN_SETUP to choose the Key4hep generation setup script.
EOF
}
if [[ ${1:-} == "--help" || ${1:-} == "-h" ]]; then usage; exit 0; fi
if (( $# != 5 )); then
    usage >&2
    exit 2
fi
sample=$1
chunk=$2
seed=$3
chunk_events=$4
total_events=$5
case "$sample" in
    Lb2LambdaGamma) decay_file=evtgen/Lb2LambdaGamma.dec ;;
    Lb2LambdaGammaPhysics) decay_file=evtgen/Lb2LambdaGamma_trpol.dec ;;
    Lb2LambdaEta) decay_file=evtgen/Lb2LambdaEta.dec ;;
    *) echo "Unknown sample: $sample" >&2; exit 2 ;;
esac
for value in "$chunk" "$seed" "$chunk_events" "$total_events"; do
    [[ "$value" =~ ^[0-9]+$ ]] || { echo "Arguments must be nonnegative integers" >&2; exit 2; }
done
(( seed > 0 && chunk_events > 0 && total_events > 0 )) || exit 2
[[ -z ${KEY4HEP_STACK:-} ]] || { echo "Run without a sourced Key4hep stack" >&2; exit 2; }

stack=${GEN_SETUP:-/cvmfs/sw.hsf.org/spackages7/key4hep-stack/2023-04-08/x86_64-centos7-gcc11.2.0-opt/urwcv/setup.sh}
stem="${sample}_nev${total_events}_chunk${chunk}"
card="work/cards/${stem}.cmd"
output="outputs/delphes/chunks/${stem}_IDEA_edm4hep.root"
partial="${output}.partial.root"
log="outputs/logs/${stem}.production.log"
mkdir -p work/cards outputs/delphes/chunks outputs/logs

if [[ -e "$output" ]]; then
    [[ -f "$log" ]] || { echo "Existing chunk has no provenance log: $log" >&2; exit 1; }
    [[ $(head -n 1 "$log") == "sample=$sample chunk=$chunk total_events=$total_events chunk_events=$chunk_events seed=$seed" ]] || {
        echo "Existing chunk was generated with different settings: $output" >&2; exit 1;
    }
    set +u
    source "$stack" >/dev/null 2>&1
    set -u
    python3 scripts/check_root_entries.py "$output" "$chunk_events"
    echo "Existing verified chunk: $output"
    exit 0
fi
if [[ -e "$partial" ]]; then
    [[ -f "$log" && $(head -n 1 "$log") == \
        "sample=$sample chunk=$chunk total_events=$total_events chunk_events=$chunk_events seed=$seed" ]] || {
        echo "Partial chunk has missing or mismatched provenance: $partial" >&2
        exit 1
    }
    set +u
    source "$stack" >/dev/null 2>&1
    set -u
    if python3 scripts/check_root_entries.py "$partial" "$chunk_events"; then
        mv "$partial" "$output"
        echo "Recovered verified chunk: $output"
        exit 0
    fi
    echo "Partial chunk is not complete; inspect or remove it before retrying: $partial" >&2
    exit 1
fi

python3 scripts/prepare_pythia_card.py \
    --input cards/p8_ee_Zbb_ecm91_EVTGEN.cmd \
    --output "$card" --nevents "$chunk_events" --seed "$seed"
printf 'sample=%s chunk=%s total_events=%s chunk_events=%s seed=%s\n' \
    "$sample" "$chunk" "$total_events" "$chunk_events" "$seed" > "$log"
set +u
source "$stack" >> "$log" 2>&1
set -u
{
    command -v DelphesPythia8EvtGen_EDM4HEP_k4Interface
    DelphesPythia8EvtGen_EDM4HEP_k4Interface \
        cards/card_IDEA.tcl cards/edm4hep_IDEA.tcl \
        "$card" "$partial" \
        evtgen/DECAY.DEC evtgen/evt.pdl \
        "$decay_file" \
        5122 Lambdab0_SIGNAL 1
    python3 scripts/check_root_entries.py "$partial" "$chunk_events"
} >> "$log" 2>&1
mv "$partial" "$output"
echo "Completed chunk: $output"

#!/usr/bin/env bash
# Direct Bash equivalent of the Snakefile's Lambda-gamma production job.
set -euo pipefail

repo_dir=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
cd "$repo_dir"

nevents=${1:-50000}
seed=${2:-12345}
[[ "$nevents" =~ ^[1-9][0-9]*$ && "$seed" =~ ^[1-9][0-9]*$ ]] || { echo "Usage: bash $0 [positive_event_count] [positive_seed]" >&2; exit 2; }
[[ -z ${KEY4HEP_STACK:-} ]] || { echo "Run from a shell without a sourced Key4hep stack" >&2; exit 2; }

stack=/cvmfs/sw.hsf.org/spackages7/key4hep-stack/2023-04-08/x86_64-centos7-gcc11.2.0-opt/urwcv/setup.sh
pythia_card="work/cards/Lb2LambdaGamma_nev${nevents}.cmd"
output="outputs/delphes/Lb2LambdaGamma_nev${nevents}_IDEA_edm4hep.root"
partial="${output}.partial.root"
log="outputs/logs/Lb2LambdaGamma_nev${nevents}.production.log"

mkdir -p work/cards outputs/delphes outputs/logs
if [[ -e "$output" ]]; then
    set +u
    source "$stack" >/dev/null 2>&1
    set -u
    python3 scripts/check_root_entries.py "$output" "$nevents"
    echo "Output already exists; leaving it unchanged: $output"
    exit 0
fi
[[ ! -e "$partial" ]] || { echo "Incomplete file exists: $partial" >&2; exit 1; }

# Step 1: write a sample-specific Pythia card.
python3 scripts/prepare_pythia_card.py \
    --input cards/p8_ee_Zbb_ecm91_EVTGEN.cmd \
    --output "$pythia_card" --nevents "$nevents" --seed "$seed"

# Step 2: enter the legacy generation stack in this process only.
printf 'sample=Lb2LambdaGamma nevents=%s seed=%s\n' "$nevents" "$seed" > "$log"
set +u  # The Key4hep setup script reads optional unset variables.
source "$stack" >> "$log" 2>&1
set -u

# Step 3: force Lambda_b -> Lambda gamma, run IDEA Delphes, then verify ROOT.
{
    command -v DelphesPythia8EvtGen_EDM4HEP_k4Interface
    DelphesPythia8EvtGen_EDM4HEP_k4Interface \
        cards/card_IDEA.tcl cards/edm4hep_IDEA.tcl \
        "$pythia_card" "$partial" \
        evtgen/DECAY.DEC evtgen/evt.pdl \
        evtgen/Lb2LambdaGamma.dec \
        5122 Lambdab0_SIGNAL 1
    python3 scripts/check_root_entries.py "$partial" "$nevents"
} >> "$log" 2>&1
mv "$partial" "$output"
echo "Completed: $output"
echo "Log: $log"

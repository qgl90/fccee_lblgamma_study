#!/usr/bin/env bash
set -euo pipefail

repo_dir=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
base_url=https://raw.githubusercontent.com/HEP-FCC/FCC-config/winter2023/FCCee

fetch_missing() {
    local relative_path=$1
    local url=$2
    local target="$repo_dir/$relative_path"
    if [[ -s "$target" ]]; then
        echo "Keeping local input: $relative_path"
        return
    fi
    mkdir -p "$(dirname "$target")"
    echo "Downloading $relative_path"
    curl --fail --location --silent --show-error --output "$target.tmp" "$url"
    mv "$target.tmp" "$target"
}

fetch_missing cards/p8_ee_Zbb_ecm91_EVTGEN.cmd "$base_url/Generator/Pythia8/p8_ee_Zbb_ecm91_EVTGEN.cmd"
fetch_missing cards/card_IDEA.tcl "$base_url/Delphes/card_IDEA.tcl"
fetch_missing cards/edm4hep_IDEA.tcl "$base_url/Delphes/edm4hep_IDEA.tcl"
fetch_missing evtgen/DECAY.DEC "$base_url/Generator/EvtGen/DECAY.DEC"
fetch_missing evtgen/evt.pdl "$base_url/Generator/EvtGen/evt.pdl"

echo "Signal decay files are maintained locally in evtgen/."

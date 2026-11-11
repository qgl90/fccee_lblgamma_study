#!/usr/bin/env bash
set -euo pipefail

repo_dir=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
generation_setup=/cvmfs/sw.hsf.org/spackages7/key4hep-stack/2023-04-08/x86_64-centos7-gcc11.2.0-opt/urwcv/setup.sh

[[ -f "$generation_setup" ]] || { echo "Missing generation stack: $generation_setup" >&2; exit 1; }
[[ -f "$repo_dir/external/FCCAnalyses/setup.sh" ]] || { echo "Missing local FCCAnalyses checkout" >&2; exit 1; }
for local_input in \
    cards/p8_ee_Zbb_ecm91_EVTGEN.cmd \
    cards/card_IDEA.tcl \
    cards/edm4hep_IDEA.tcl \
    evtgen/DECAY.DEC \
    evtgen/evt.pdl \
    evtgen/Lb2LambdaGamma.dec \
    evtgen/Lb2LambdaGamma_trpol.dec \
    evtgen/Lb2LambdaEta.dec \
    evtgen/Lb2LambdaEtaPhysics.dec \
    evtgen/Lb2LambdaPi0PHSP.dec \
    evtgen/Lb2LambdaPi0.dec; do
    [[ -s "$repo_dir/$local_input" ]] || { echo "Missing local input: $local_input" >&2; exit 1; }
done

echo "Generation stack: $generation_setup"
bash --noprofile --norc -c 'source "$1" >/dev/null 2>&1; command -v DelphesPythia8EvtGen_EDM4HEP_k4Interface' _ "$generation_setup"
echo "FCCAnalyses checkout: $repo_dir/external/FCCAnalyses"
git -C "$repo_dir/external/FCCAnalyses" log -1 --format='%h %D %s'
echo "FCCAnalyses build stack: Key4hep 2024-03-10 (pinned by setup.sh)"

import os
from pathlib import Path

configfile: "config/config.yaml"


def cfg(path, default=None):
    cur = config
    for part in path.split("."):
        if part not in cur:
            return default
        cur = cur[part]
    return cur


SIGNAL = cfg("signal.name")
NEVENTS = int(cfg("production.nevents"))
SEED = int(cfg("production.seed"))

URL_PYTHIA = cfg("urls.pythia_cmd")
URL_DELPHES = cfg("urls.delphes_card")
URL_EDM4HEP = cfg("urls.edm4hep_tcl")
URL_DECAY = cfg("urls.decay_dec")
URL_PDL = cfg("urls.evt_pdl")

DELPHES_OUT = cfg("paths.delphes_out")
ANALYSIS_OUT = cfg("paths.analysis_out")


rule all:
    input:
        ANALYSIS_OUT


rule fetch_cards:
    output:
        pythia="cards/p8_ee_Zbb_ecm91_EVTGEN.cmd",
        delphes="cards/card_IDEA.tcl",
        edm4hep="cards/edm4hep_IDEA.tcl",
        decay="evtgen/DECAY.DEC",
        pdl="evtgen/evt.pdl",
    params:
        pythia_url=URL_PYTHIA,
        delphes_url=URL_DELPHES,
        edm4hep_url=URL_EDM4HEP,
        decay_url=URL_DECAY,
        pdl_url=URL_PDL,
    shell:
        r"""
        set -euo pipefail
        mkdir -p cards evtgen
        curl -L -o {output.pythia} {params.pythia_url}
        curl -L -o {output.delphes} {params.delphes_url}
        curl -L -o {output.edm4hep} {params.edm4hep_url}
        curl -L -o {output.decay} {params.decay_url}
        curl -L -o {output.pdl} {params.pdl_url}
        """


rule pythia_card:
    input:
        base="cards/p8_ee_Zbb_ecm91_EVTGEN.cmd",
        prep="scripts/prepare_pythia_card.py",
    output:
        card=f"work/cards/p8_ee_Zbb_ecm91_EVTGEN_nev{NEVENTS}_seed{SEED}.cmd",
    params:
        nevents=NEVENTS,
        seed=SEED,
    shell:
        r"""
        set -euo pipefail
        python3 {input.prep} --input {input.base} --output {output.card} --nevents {params.nevents} --seed {params.seed}
        """


rule delphes_edm4hep:
    input:
        delphes="cards/card_IDEA.tcl",
        edm4hep="cards/edm4hep_IDEA.tcl",
        decay="evtgen/DECAY.DEC",
        pdl="evtgen/evt.pdl",
        pythia=rules.pythia_card.output.card,
        user_dec="evtgen/Lb2LambdaGamma.dec",
    output:
        root=DELPHES_OUT,
    params:
        pdg_mother=cfg("signal.pdg_mother"),
        label=f"{SIGNAL}_SIGNAL",
        force=1,
    shell:
        r"""
        set -euo pipefail
        mkdir -p $(dirname {output.root})
        DelphesPythia8EvtGen_EDM4HEP_k4Interface \
          {input.delphes} {input.edm4hep} \
          {input.pythia} {output.root} \
          {input.decay} {input.pdl} \
          {input.user_dec} \
          {params.pdg_mother} {params.label} {params.force}
        """


rule fccanalyses_tree:
    input:
        root=DELPHES_OUT,
        script="analysis/analysis_lb2lgamma.py",
    output:
        root=ANALYSIS_OUT,
    threads:
        int(cfg("resources.analysis_cores", 1)),
    params:
        pdg_mother=str(cfg("signal.pdg_mother")),
        pdg_daughters=",".join(str(x) for x in cfg("signal.pdg_daughters")),
    shell:
        r"""
        set -euo pipefail
        mkdir -p $(dirname {output.root})
        FCC_SIG_PDG_MOTHER="{params.pdg_mother}" \
        FCC_SIG_PDG_DAUGHTERS="{params.pdg_daughters}" \
          fccanalysis run {input.script} --input {input.root} --output {output.root}
        """

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
ANALYSIS_MODE = cfg("analysis.mode", "truth")

KEY4HEP_SETUP = cfg("env.key4hep_setup", "") or ""
KEY4HEP_ARGS = cfg("env.key4hep_args", "") or ""
FCCANALYSES_SETUP = cfg("env.fccanalyses_setup", "") or ""


def setup_cmd(needs_fccanalyses: bool) -> str:
    parts = []
    if KEY4HEP_SETUP:
        if KEY4HEP_ARGS:
            parts.append(f"source {KEY4HEP_SETUP} {KEY4HEP_ARGS}")
        else:
            parts.append(f"source {KEY4HEP_SETUP}")
    if needs_fccanalyses and FCCANALYSES_SETUP:
        parts.append(f"source {FCCANALYSES_SETUP}")
    if not parts:
        return ""
    return " && ".join(parts) + " && "

URL_PYTHIA = cfg("urls.pythia_cmd")
URL_DELPHES = cfg("urls.delphes_card")
URL_EDM4HEP = cfg("urls.edm4hep_tcl")
URL_DECAY = cfg("urls.decay_dec")
URL_PDL = cfg("urls.evt_pdl")

DELPHES_OUT = cfg("paths.delphes_out")
ANALYSIS_DIR = cfg("paths.analysis_dir", "outputs/analysis")
PLOTS_DIR = cfg("paths.plots_dir", "outputs/plots")

_bgs_raw = cfg("backgrounds", []) or []
BACKGROUNDS = [b for b in _bgs_raw if b.get("enabled", True) and b.get("name")]
SAMPLES = ["signal"] + [b["name"] for b in BACKGROUNDS]


def analysis_script():
    if ANALYSIS_MODE == "reco":
        return "analysis/analysis_lb2lgamma_reco.py"
    return "analysis/analysis_lb2lgamma.py"


def filelist_out(sample: str) -> str:
    return f"work/filelists/{sample}.txt"


def background_by_name(name: str):
    for b in BACKGROUNDS:
        if b.get("name") == name:
            return b
    raise ValueError(f"Unknown background sample: {name}")


rule all:
    input:
        expand(f"{ANALYSIS_DIR}/{{sample}}_tree.root", sample=SAMPLES),
        f"{PLOTS_DIR}/lb_reco_m.png"


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
        setup=setup_cmd(needs_fccanalyses=False),
    shell:
        r"""
        set -euo pipefail
        mkdir -p $(dirname {output.root})
        {params.setup}DelphesPythia8EvtGen_EDM4HEP_k4Interface \
          {input.delphes} {input.edm4hep} \
          {input.pythia} {output.root} \
          {input.decay} {input.pdl} \
          {input.user_dec} \
          {params.pdg_mother} {params.label} {params.force}
        """


def _filelist_inputs(wc):
    if wc.sample == "signal":
        return [DELPHES_OUT]
    bg = background_by_name(wc.sample)
    if bg.get("input_file_list"):
        return [bg["input_file_list"]]
    return []


rule make_input_filelist:
    output:
        flist="work/filelists/{sample}.txt",
    input:
        _filelist_inputs,
    run:
        Path(output.flist).parent.mkdir(parents=True, exist_ok=True)
        if wildcards.sample == "signal":
            Path(output.flist).write_text(str(Path(DELPHES_OUT).resolve()) + "\n")
            return

        bg = background_by_name(wildcards.sample)
        if bg.get("input_file_list"):
            src = Path(bg["input_file_list"])
            if not src.exists():
                raise FileNotFoundError(
                    f"Background file list not found: {src} (edit config/config.yaml)"
                )
            lines = []
            for line in src.read_text().splitlines():
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                lines.append(line)
            if not lines:
                raise ValueError(f"Background file list is empty: {src}")
            Path(output.flist).write_text("\n".join(lines) + "\n")
            return

        files = bg.get("input_files") or []
        if not files:
            raise ValueError(
                f"Background '{wildcards.sample}' has no input_file_list or input_files (edit config/config.yaml)"
            )
        Path(output.flist).write_text("\n".join(files) + "\n")


rule fccanalyses_tree:
    input:
        flist="work/filelists/{sample}.txt",
        script=lambda wc: analysis_script(),
    output:
        root=f"{ANALYSIS_DIR}/{{sample}}_tree.root",
    threads:
        int(cfg("resources.analysis_cores", 1)),
    params:
        pdg_mother=str(cfg("signal.pdg_mother")),
        pdg_daughters=",".join(str(x) for x in cfg("signal.pdg_daughters")),
        setup=setup_cmd(needs_fccanalyses=True),
    shell:
        r"""
        set -euo pipefail
        mkdir -p $(dirname {output.root})
        {params.setup}FCC_SIG_PDG_MOTHER="{params.pdg_mother}" \
          FCC_SIG_PDG_DAUGHTERS="{params.pdg_daughters}" \
            fccanalysis run {input.script} --input-file-list {input.flist} --output {output.root}
        """


def _bg_plot_args():
    args = []
    for b in BACKGROUNDS:
        name = b.get("name")
        if not name:
            continue
        scale = float(b.get("scale", 1.0))
        args.append(f"{name}|{ANALYSIS_DIR}/{name}_tree.root|{scale}")
    return ";".join(args)


rule plot_mass_overlay:
    input:
        trees=expand(f"{ANALYSIS_DIR}/{{sample}}_tree.root", sample=SAMPLES),
        script="plots/plot_mass_overlay.py",
    output:
        png=f"{PLOTS_DIR}/lb_reco_m.png",
    params:
        branch=cfg("plot.branch", "lb_reco_m"),
        nbins=int(cfg("plot.nbins", 120)),
        xmin=float(cfg("plot.xmin", 4.8)),
        xmax=float(cfg("plot.xmax", 6.4)),
        normalize=str(cfg("plot.normalize", "none")),
        signal_scale=float(cfg("plot.signal_scale", 1.0)),
        backgrounds=_bg_plot_args(),
        setup=setup_cmd(needs_fccanalyses=False),
    shell:
        r"""
        set -euo pipefail
        mkdir -p $(dirname {output.png})
        {params.setup}python3 {input.script} \
          --out {output.png} \
          --branch {params.branch} \
          --nbins {params.nbins} --xmin {params.xmin} --xmax {params.xmax} \
          --normalize {params.normalize} \
          --signal {ANALYSIS_DIR}/signal_tree.root|{params.signal_scale} \
          --backgrounds {params.backgrounds}
        """

"""Local chunked EvtGen + Delphes production of EDM4hep samples.

The generator stack stays separate from the pinned FCCAnalyses build.
Reconstruction and physics studies consume these final files later.
"""

configfile: "config/config.yaml"

SAMPLES = config["samples"]
NEVENTS = int(config["production"]["nevents"])
NCHUNKS = int(config["production"]["chunks"])
OUT_DIR = config["paths"]["delphes_out_dir"]
GEN_SETUP = config["env"]["key4hep_generation"]

if NEVENTS <= 0 or NCHUNKS <= 0 or NEVENTS % NCHUNKS:
    raise ValueError("production.nevents must divide evenly by production.chunks")
if not SAMPLES:
    raise ValueError("At least one production sample is required")
CHUNK_EVENTS = NEVENTS // NCHUNKS
PRESELECT = config["preselection"]
PRESELECT_EVENTS = int(PRESELECT["events"])
PRESELECT_DIR = PRESELECT["output_dir"]
PRESELECT_CONFIG = PRESELECT["reconstruction_config"]
PRESELECT_INPUTS = PRESELECT["inputs"]
PRESELECT_SOURCE_IDS = PRESELECT["source_ids"]
PRESELECT_SAMPLES = tuple(PRESELECT_INPUTS)
PRESELECT_GEN = config["preselection_generation"]
PRESELECT_GEN_EVENTS = int(PRESELECT_GEN["events"])
PRESELECT_GEN_CHUNKS = int(PRESELECT_GEN["chunks"])
PRESELECT_GEN_SAMPLES = PRESELECT_GEN["samples"]
PRESELECT_GEN_CHUNK_EVENTS = PRESELECT_GEN_EVENTS // PRESELECT_GEN_CHUNKS
PRESELECT_FULL_DIR = "outputs/analysis/studies/nominal_preselection_100k"
PRESELECT_FULL_INPUTS = {
    "signal_phsp": f"{OUT_DIR}/Lb2LambdaGamma_nev{PRESELECT_GEN_EVENTS}_IDEA_edm4hep.root",
    "signal_physics": f"{OUT_DIR}/Lb2LambdaGammaPhysics_nev{PRESELECT_GEN_EVENTS}_IDEA_edm4hep.root",
    "lbgamma_eta": f"{OUT_DIR}/Lb2LambdaEta_nev{PRESELECT_GEN_EVENTS}_IDEA_edm4hep.root",
    "lbgamma_eta_physics": f"{OUT_DIR}/Lb2LambdaEtaPhysics_nev{PRESELECT_GEN_EVENTS}_IDEA_edm4hep.root",
    "lbgamma_pi0_phsp": f"{OUT_DIR}/Lb2LambdaPi0_nev{PRESELECT_GEN_EVENTS}_IDEA_edm4hep.root",
    "lbgamma_pi0": f"{OUT_DIR}/Lb2LambdaPi0Physics_nev{PRESELECT_GEN_EVENTS}_IDEA_edm4hep.root",
}
PRESELECT_FULL_SOURCE_IDS = {"signal_phsp": 100, "signal_physics": 101,
                             "lbgamma_eta": 102, "lbgamma_pi0": 103,
                             "lbgamma_eta_physics": 104,
                             "lbgamma_pi0_phsp": 105}

if PRESELECT_EVENTS <= 0 or PRESELECT_EVENTS > 1000:
    raise ValueError("preselection.events must be between 1 and 1,000 for validation")
if set(PRESELECT_SAMPLES) != {"signal_phsp", "signal_physics", "lbgamma_eta", "zbb"}:
    raise ValueError("preselection.inputs must define signal_phsp, signal_physics, lbgamma_eta, and zbb")
if (PRESELECT_GEN_EVENTS <= 0 or PRESELECT_GEN_CHUNKS <= 0 or
        PRESELECT_GEN_EVENTS % PRESELECT_GEN_CHUNKS):
    raise ValueError("preselection_generation.events must divide evenly by chunks")

wildcard_constraints:
    sample="|".join([*SAMPLES, *PRESELECT_SAMPLES, *PRESELECT_FULL_INPUTS,
                     *PRESELECT_GEN_SAMPLES]),
    chunk="|".join(str(i) for i in range(NCHUNKS))


def output_root(sample):
    return f"{OUT_DIR}/{sample}_nev{NEVENTS}_IDEA_edm4hep.root"


def chunk_roots(sample):
    return [
        f"{OUT_DIR}/chunks/{sample}_nev{NEVENTS}_chunk{i}_IDEA_edm4hep.root"
        for i in range(NCHUNKS)
    ]


rule all:
    input:
        [output_root(sample) for sample in SAMPLES]


def preselection_root(wc):
    return f"{PRESELECT_DIR}/{wc.sample}_reco.root"


def preselection_parquet(wc):
    return f"{PRESELECT_DIR}/{wc.sample}_candidates.parquet"


rule preselection_reconstruct:
    input:
        edm4hep=lambda wc: PRESELECT_INPUTS[wc.sample],
        config=PRESELECT_CONFIG,
        runner="scripts/run_reco_preselection.sh",
        analysis="analysis/studies/lb2lambda_gamma_reco.py",
    output:
        f"{PRESELECT_DIR}/{{sample}}_reco.root",
    log:
        f"{PRESELECT_DIR}/logs/{{sample}}_reco.log",
    params:
        events=PRESELECT_EVENTS,
    threads: 1
    shell:
        "bash {input.runner} {wildcards.sample} {input.edm4hep} {output} "
        "{params.events} {input.config} > {log} 2>&1"


rule preselection_flatten:
    input:
        root=preselection_root,
        script="studies/reconstruction/flatten_candidates.py",
    output:
        parquet=f"{PRESELECT_DIR}/{{sample}}_candidates.parquet",
        summary=f"{PRESELECT_DIR}/{{sample}}_candidates.summary.json",
    log:
        f"{PRESELECT_DIR}/logs/{{sample}}_flatten.log",
    params:
        source_id=lambda wc: PRESELECT_SOURCE_IDS[wc.sample],
    shell:
        "env -u PYTHONPATH -u PYTHONHOME myenv/bin/python {input.script} "
        "--mode gamma --input {input.root} --output {output.parquet} "
        "--source-id {params.source_id} --chunk-events 500 > {log} 2>&1"


rule preselection_filter:
    input:
        parquet=preselection_parquet,
        script="studies/reconstruction/preselect_candidates.py",
    output:
        selected=f"{PRESELECT_DIR}/{{sample}}_selected.parquet",
        rejected=f"{PRESELECT_DIR}/{{sample}}_rejected.parquet",
        summary=f"{PRESELECT_DIR}/{{sample}}_summary.json",
    log:
        f"{PRESELECT_DIR}/logs/{{sample}}_preselection.log",
    shell:
        "env -u PYTHONPATH -u PYTHONHOME myenv/bin/python {input.script} "
        "--input {input.parquet} --output-prefix {PRESELECT_DIR}/{wildcards.sample} "
        "> {log} 2>&1"


def full_preselection_root(wc):
    return f"{PRESELECT_FULL_DIR}/{wc.sample}_reco.root"


def full_preselection_parquet(wc):
    return f"{PRESELECT_FULL_DIR}/{wc.sample}_candidates.parquet"


rule preselection_100k_reconstruct:
    input:
        edm4hep=lambda wc: PRESELECT_FULL_INPUTS[wc.sample],
        config=PRESELECT_CONFIG,
        runner="scripts/run_reco_preselection.sh",
    output:
        f"{PRESELECT_FULL_DIR}/{{sample}}_reco.root",
    log:
        f"{PRESELECT_FULL_DIR}/logs/{{sample}}_reco.log",
    threads: 4
    shell:
        "bash {input.runner} {wildcards.sample} {input.edm4hep} {output} "
        "all {input.config} {threads} > {log} 2>&1"


rule preselection_100k_flatten:
    input:
        root=full_preselection_root,
        script="studies/reconstruction/flatten_candidates.py",
    output:
        parquet=f"{PRESELECT_FULL_DIR}/{{sample}}_candidates.parquet",
        root=f"{PRESELECT_FULL_DIR}/{{sample}}_candidates.root",
        summary=f"{PRESELECT_FULL_DIR}/{{sample}}_candidates.summary.json",
    log:
        f"{PRESELECT_FULL_DIR}/logs/{{sample}}_flatten.log",
    params:
        source_id=lambda wc: PRESELECT_FULL_SOURCE_IDS[wc.sample],
    shell:
        "env -u PYTHONPATH -u PYTHONHOME myenv/bin/python {input.script} "
        "--mode gamma --input {input.root} --output {output.parquet} "
        "--root-output {output.root} --source-id {params.source_id} "
        "--chunk-events 500 > {log} 2>&1"


rule preselection_100k_filter:
    input:
        parquet=full_preselection_parquet,
        script="studies/reconstruction/preselect_candidates.py",
    output:
        selected=f"{PRESELECT_FULL_DIR}/{{sample}}_selected.parquet",
        rejected=f"{PRESELECT_FULL_DIR}/{{sample}}_rejected.parquet",
        summary=f"{PRESELECT_FULL_DIR}/{{sample}}_summary.json",
    log:
        f"{PRESELECT_FULL_DIR}/logs/{{sample}}_preselection.log",
    shell:
        "env -u PYTHONPATH -u PYTHONHOME myenv/bin/python {input.script} "
        "--input {input.parquet} --output-prefix {PRESELECT_FULL_DIR}/{wildcards.sample} "
        "> {log} 2>&1"


rule preselection_generate_chunk:
    input:
        base="cards/p8_ee_Zbb_ecm91_EVTGEN.cmd",
        delphes="cards/card_IDEA.tcl",
        edm4hep="cards/edm4hep_IDEA.tcl",
        decay_table="evtgen/DECAY.DEC",
        pdl="evtgen/evt.pdl",
        decay=lambda wc: PRESELECT_GEN_SAMPLES[wc.sample]["decay_file"],
        command="scripts/produce_chunk.sh",
    output:
        f"{OUT_DIR}/chunks/{{sample}}_nev{PRESELECT_GEN_EVENTS}_chunk{{chunk}}_IDEA_edm4hep.root",
    params:
        setup=GEN_SETUP,
        seed=lambda wc: int(PRESELECT_GEN_SAMPLES[wc.sample]["seed"]) + int(wc.chunk),
        chunk_events=PRESELECT_GEN_CHUNK_EVENTS,
        total_events=PRESELECT_GEN_EVENTS,
    threads: 1
    wildcard_constraints:
        sample="|".join(PRESELECT_GEN_SAMPLES),
        chunk="|".join(str(i) for i in range(PRESELECT_GEN_CHUNKS))
    shell:
        "GEN_SETUP={params.setup} bash {input.command} {wildcards.sample} "
        "{wildcards.chunk} {params.seed} {params.chunk_events} {params.total_events}"


def preselection_generation_chunks(wc):
    return [
        f"{OUT_DIR}/chunks/{wc.sample}_nev{PRESELECT_GEN_EVENTS}_chunk{i}_IDEA_edm4hep.root"
        for i in range(PRESELECT_GEN_CHUNKS)
    ]


rule preselection_merge_generation:
    input:
        chunks=preselection_generation_chunks,
        command="scripts/merge_chunks.sh",
    output:
        f"{OUT_DIR}/{{sample}}_nev{PRESELECT_GEN_EVENTS}_IDEA_edm4hep.root",
    params:
        setup=GEN_SETUP,
        total_events=PRESELECT_GEN_EVENTS,
        nchunks=PRESELECT_GEN_CHUNKS,
    threads: 1
    wildcard_constraints:
        sample="|".join(PRESELECT_GEN_SAMPLES)
    shell:
        "GEN_SETUP={params.setup} bash {input.command} {wildcards.sample} "
        "{params.total_events} {params.nchunks}"


rule delphes_chunk:
    input:
        base="cards/p8_ee_Zbb_ecm91_EVTGEN.cmd",
        delphes="cards/card_IDEA.tcl",
        edm4hep="cards/edm4hep_IDEA.tcl",
        decay="evtgen/DECAY.DEC",
        pdl="evtgen/evt.pdl",
        user_dec=lambda wc: SAMPLES[wc.sample]["decay_file"],
        prep="scripts/prepare_pythia_card.py",
        check="scripts/check_root_entries.py",
        command="scripts/produce_chunk.sh",
    output:
        f"{OUT_DIR}/chunks/{{sample}}_nev{NEVENTS}_chunk{{chunk}}_IDEA_edm4hep.root",
    params:
        setup=GEN_SETUP,
        seed=lambda wc: int(SAMPLES[wc.sample]["seed"]) + int(wc.chunk),
        chunk_events=CHUNK_EVENTS,
        total_events=NEVENTS,
    threads: 1
    shell:
        "GEN_SETUP={params.setup} bash {input.command} {wildcards.sample} {wildcards.chunk} "
        "{params.seed} {params.chunk_events} {params.total_events}"


rule merge_edm4hep:
    input:
        chunks=lambda wc: chunk_roots(wc.sample),
        command="scripts/merge_chunks.sh",
        check="scripts/check_root_entries.py",
    output:
        f"{OUT_DIR}/{{sample}}_nev{NEVENTS}_IDEA_edm4hep.root",
    params:
        setup=GEN_SETUP,
        total_events=NEVENTS,
        nchunks=NCHUNKS,
    threads: 1
    shell:
        "GEN_SETUP={params.setup} bash {input.command} {wildcards.sample} "
        "{params.total_events} {params.nchunks}"

# FCC-ee IDEA Delphes study: `Lambda_b0 -> Lambda0(p pi) gamma`

This repo is a **minimal template** to run a full chain:

1. **Production + fast simulation** with `DelphesPythia8EvtGen_EDM4HEP_k4Interface` (IDEA Delphes card, EDM4hep output).
2. **FCCAnalyses** step to produce a **flat tree** (truth-seeded: MC decay products matched to reco objects).
3. Orchestrated with **Snakemake**.

## Prerequisites

- A Key4hep environment that provides `DelphesPythia8EvtGen_EDM4HEP_k4Interface` and `python3`.
- An FCCAnalyses setup that provides `fccanalysis` (usually by cloning + building FCCAnalyses).
- `snakemake` available in your environment.

If you want to stay compatible with **winter2023** centrally-produced samples, you typically need a matching Key4hep + FCCAnalyses setup (often `FCCAnalyses` `pre-edm4hep1` with the Key4hep release used for that campaign). See FCCAnalyses docs for details.

## CERN / lxplus environment setup (example)

In a fresh shell:

```bash
# 1) Key4hep (pick ONE)
source /cvmfs/sw.hsf.org/key4hep/setup.sh --latest
# or (commonly used for winter2023 compatibility)
# source /cvmfs/sw.hsf.org/key4hep/setup.sh -r 2024-03-10

# 2) Build FCCAnalyses locally *inside this repo* (pick the matching branch)
cd /path/to/fccee_lblgamma_study
mkdir -p external && cd external
git clone --branch master https://github.com/HEP-FCC/FCCAnalyses.git
# or: git clone --branch pre-edm4hep1 https://github.com/HEP-FCC/FCCAnalyses.git
cd FCCAnalyses
source ./setup.sh
fccanalysis build -j 8

# (optional) go back to the study repo root
cd /path/to/fccee_lblgamma_study

# 3) Install snakemake if not available
python3 -m pip install --user snakemake
```

Then keep the same shell for running this repo (so `fccanalysis` stays on `PATH`).

## Local Snakemake virtualenv (recommended on CERN)

Some CERN environments have a broken `snakemake` wrapper function. A robust setup is to create a **local venv** inside the repo and run Snakemake via `python -m snakemake`.

```bash
cd /path/to/fccee_lblgamma_study
./scripts/setup_venv.sh
source .venv/bin/activate
```

Note: the venv is created with `--system-site-packages` so that `import ROOT` (from Key4hep) still works for the plotting step.

## Using LHCb conda / lbconda for Snakemake (avoid Python mixing)

If you run Snakemake from an LHCb conda env (python3.11) and also `source key4hep`, you can end up with **Key4hep Python packages (python3.10) on `PYTHONPATH`**, which breaks Snakemake (typical symptom: pandas/numpy import errors).

Workaround: **do NOT `source key4hep` in the parent shell**. Instead, let each Snakemake job source Key4hep in its own subshell:

1) Edit `/Users/renato/Desktop/fcee_b2lbgamma/config/config.yaml:1`:

- `env.key4hep_setup: "/cvmfs/sw.hsf.org/key4hep/setup.sh"`
- `env.key4hep_args: "--latest"` (or `-r 2024-03-10`)
- `env.fccanalyses_setup: "external/FCCAnalyses/setup.sh"` (if you built FCCAnalyses locally)

2) Run Snakemake from your conda env (without sourcing key4hep):

```bash
./scripts/run_snakemake.sh -j 4
```

## Quick run

```bash
cd /Users/renato/Desktop/fcee_b2lbgamma

# 1) enter your key4hep environment first (example)
# source /cvmfs/sw.hsf.org/key4hep/setup.sh

# 2) run the chain
snakemake -j 4
```

If Snakemake fails with a cache permission error on your system, use:

```bash
./scripts/run_snakemake.sh -j 4
```

If `snakemake` fails immediately because your shell defines a broken wrapper function (common on some CERN setups), do one of:

```bash
unset -f snakemake
command snakemake -j 4
```

or just always use:

```bash
./scripts/run_snakemake.sh -j 4
```

Outputs:

- Delphes EDM4hep ROOT (signal): `outputs/delphes/Lb2LambdaGamma_IDEA_edm4hep.root`
- FCCAnalyses flat tree(s): `outputs/analysis/signal_tree.root` (and one `*_tree.root` per enabled background)
- Quick overlay plot: `outputs/plots/lb_reco_m.png`

## What to edit for your study

- `config/config.yaml`: number of events, √s, seed, detector card URLs.
- `evtgen/Lb2LambdaGamma.dec`: your forced decay(s).
- `config/config.yaml`:
  - `analysis.mode` = `truth` (sanity check) or `reco` (simple combinatorial)
  - `backgrounds`: set `enabled: true` and point `input_file_list` to your background sample(s)
- `analysis/analysis_lb2lgamma.py`: truth-seeded sanity-check analysis.
- `analysis/analysis_lb2lgamma_reco.py`: simple combinatorial reconstruction (first-pass background shape).

Useful targets:

```bash
# Only produce the Delphes EDM4hep file
snakemake -j 4 outputs/delphes/Lb2LambdaGamma_IDEA_edm4hep.root

# Re-run only the FCCAnalyses step
snakemake -j 4 outputs/analysis/Lb2LambdaGamma_tree.root
```

## Notes / common gotchas

- The forced-decay mechanism overrides the decay of PDG `5122` (and charge conjugate) **when present** in the event.
  - At the Z pole, `Lambda_b` production fraction is not huge, so you may need large statistics (or add an event-filter strategy in production if you need “N signal decays” rather than “N Z→bb events”).
- Collection names in EDM4hep files can differ between stacks / branches.
  - If `fccanalysis run` errors on missing collections, adjust the aliases at the top of `analysis/analysis_lb2lgamma.py`.
- The analysis reads the signal PDGs from env vars (set by the Snakefile):
  - `FCC_SIG_PDG_MOTHER` (default `5122`)
  - `FCC_SIG_PDG_DAUGHTERS` (default `2212,-211,22`)
- Background vs signal:
  - `analysis.mode: truth` uses truth matching, so it is **not** a realistic estimate of combinatorial background.
  - Use `analysis.mode: reco` to get a first background shape (still simplified).

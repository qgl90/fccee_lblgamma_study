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

1) Edit `/Users/renato/Desktop/fcee_b2lbgamma/config/config_lb2lgamma.yaml:1`:

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

## Manual run (no Snakemake)

This section lists the same chain as explicit commands.

### 0) Environment (do this once)

Run in a clean shell and keep that shell:

```bash
source /cvmfs/sw.hsf.org/key4hep/setup.sh --latest
# or: source /cvmfs/sw.hsf.org/key4hep/setup.sh -r 2024-03-10

# FCCAnalyses (if built locally under ./external)
source external/FCCAnalyses/setup.sh
```

If you are using an LHCb conda env (python3.11), do not mix it with Key4hep python in the same shell (use the Snakemake per-job setup described above, or run the manual recipe from a Key4hep shell).

### 1) Fetch cards + EvtGen tables

```bash
mkdir -p cards evtgen work/cards work/filelists outputs/delphes outputs/analysis outputs/plots

curl -L -o cards/p8_ee_Zbb_ecm91_EVTGEN.cmd https://raw.githubusercontent.com/HEP-FCC/FCC-config/winter2023/FCCee/Generator/Pythia8/p8_ee_Zbb_ecm91_EVTGEN.cmd
curl -L -o cards/card_IDEA.tcl https://raw.githubusercontent.com/HEP-FCC/FCC-config/winter2023/FCCee/Delphes/card_IDEA.tcl
curl -L -o cards/edm4hep_IDEA.tcl https://raw.githubusercontent.com/HEP-FCC/FCC-config/winter2023/FCCee/Delphes/edm4hep_IDEA.tcl
curl -L -o evtgen/DECAY.DEC https://raw.githubusercontent.com/HEP-FCC/FCC-config/winter2023/FCCee/Generator/EvtGen/DECAY.DEC
curl -L -o evtgen/evt.pdl https://raw.githubusercontent.com/HEP-FCC/FCC-config/winter2023/FCCee/Generator/EvtGen/evt.pdl
```

### 2) Prepare the Pythia card (nevents + seed)

```bash
python3 scripts/prepare_pythia_card.py \
  --input cards/p8_ee_Zbb_ecm91_EVTGEN.cmd \
  --output work/cards/p8_ee_Zbb_ecm91_EVTGEN_nev20000_seed12345.cmd \
  --nevents 20000 \
  --seed 12345
```

### 3) Run Delphes IDEA + write EDM4hep ROOT (signal)

Forced decay is defined in `evtgen/Lb2LambdaGamma.dec`.

```bash
DelphesPythia8EvtGen_EDM4HEP_k4Interface \
  cards/card_IDEA.tcl cards/edm4hep_IDEA.tcl \
  work/cards/p8_ee_Zbb_ecm91_EVTGEN_nev20000_seed12345.cmd \
  outputs/delphes/Lb2LambdaGamma_IDEA_edm4hep.root \
  evtgen/DECAY.DEC evtgen/evt.pdl \
  evtgen/Lb2LambdaGamma.dec \
  5122 Lb2LambdaGamma_SIGNAL 1
```

### 4) Create input file lists (signal + background)

Signal:

```bash
printf "%s\n" "$PWD/outputs/delphes/Lb2LambdaGamma_IDEA_edm4hep.root" > work/filelists/signal.txt
```

Backgrounds:

1) Put your background EDM4hep ROOT files (one per line) into `data/background_Zbb_files.txt`
2) Then:

```bash
cp data/background_Zbb_files.txt work/filelists/Zbb.txt
```

### 5) Run FCCAnalyses (produce flat trees)

Truth-seeded (fast sanity check, not a realistic background estimate):

```bash
FCC_SIG_PDG_MOTHER=5122 FCC_SIG_PDG_DAUGHTERS=2212,-211,22 \
  fccanalysis run analysis/analysis_lb2lgamma.py \
    --input-file-list work/filelists/signal.txt \
    --output outputs/analysis/signal_tree.root

FCC_SIG_PDG_MOTHER=5122 FCC_SIG_PDG_DAUGHTERS=2212,-211,22 \
  fccanalysis run analysis/analysis_lb2lgamma.py \
    --input-file-list work/filelists/Zbb.txt \
    --output outputs/analysis/Zbb_tree.root
```

Reco/combinatorial (first-pass background shape):

```bash
fccanalysis run analysis/analysis_lb2lgamma_reco.py --input-file-list work/filelists/signal.txt --output outputs/analysis/signal_tree.root
fccanalysis run analysis/analysis_lb2lgamma_reco.py --input-file-list work/filelists/Zbb.txt --output outputs/analysis/Zbb_tree.root
```

### 6) Overlay plot (signal vs background)

```bash
python3 plots/plot_mass_overlay.py \
  --out outputs/plots/lb_reco_m.png \
  --branch lb_reco_m \
  --nbins 120 --xmin 4.8 --xmax 6.4 \
  --normalize none \
  --signal outputs/analysis/signal_tree.root|1.0 \
  --backgrounds "Zbb|outputs/analysis/Zbb_tree.root|1.0"
```

Result: `outputs/plots/lb_reco_m.png`

## What to edit for your study

- `config/config_lb2lgamma.yaml`: number of events, √s, seed, detector card URLs.
- `evtgen/Lb2LambdaGamma.dec`: your forced decay(s).
- `config/config_lb2lgamma.yaml`:
  - `analysis.mode` = `truth` (sanity check) or `reco` (simple combinatorial)
  - `backgrounds`: set `enabled: true` and point `input_file_list` to your background sample(s)
- `analysis/analysis_lb2lgamma.py`: truth-seeded sanity-check analysis.
- `analysis/analysis_lb2lgamma_reco.py`: simple combinatorial reconstruction (first-pass background shape).

Useful targets:

```bash
# Only produce the Delphes EDM4hep file
snakemake -j 4 outputs/delphes/Lb2LambdaGamma_IDEA_edm4hep.root

# Re-run only the FCCAnalyses step
snakemake -j 4 outputs/analysis/signal_tree.root
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

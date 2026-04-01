# FCC-ee IDEA Delphes study: `Lambda_b0 -> Lambda0(p pi) gamma`

This repo is a **minimal template** to run a full chain:

1. **Production + fast simulation** with `DelphesPythia8EvtGen_EDM4HEP_k4Interface` (IDEA Delphes card, EDM4hep output).
2. **FCCAnalyses** step to produce a **flat tree** (truth-seeded: MC decay products matched to reco objects).
3. Orchestrated with **Snakemake**.

## Prerequisites

- A Key4hep environment that provides:
  - `DelphesPythia8EvtGen_EDM4HEP_k4Interface`
  - `fccanalysis`
  - `python3`
- `snakemake` available in your environment.

If you want to stay compatible with **winter2023** centrally-produced samples, you typically need a matching Key4hep + FCCAnalyses setup (often `FCCAnalyses` `pre-edm4hep1` with the Key4hep release used for that campaign). See FCCAnalyses docs for details.

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

Outputs:

- Delphes EDM4hep ROOT: `outputs/delphes/Lb2LambdaGamma_IDEA_edm4hep.root`
- FCCAnalyses flat tree: `outputs/analysis/Lb2LambdaGamma_tree.root`

## What to edit for your study

- `config/config.yaml`: number of events, √s, seed, detector card URLs.
- `evtgen/Lb2LambdaGamma.dec`: your forced decay(s).
- `analysis/analysis_lb2lgamma.py`: selections + branches to snapshot.

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

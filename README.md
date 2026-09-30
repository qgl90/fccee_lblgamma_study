# Λb → Λ⁰γ FCC-ee study

This repository separates event generation, detector response, candidate
reconstruction, and downstream studies. Start with
[`docs/REPOSITORY_GUIDE.md`](docs/REPOSITORY_GUIDE.md) for executable workflows
and [`docs/ANALYSIS_WORKFLOW.md`](docs/ANALYSIS_WORKFLOW.md) for the analysis
contracts and review gates. The local working rules are in [`AGENTS.md`](AGENTS.md).

## Main workflows

| Task | Entry point | Guide |
|---|---|---|
| Generate forced Λb samples | `Snakefile`, `scripts/produce_chunk.sh` | [`README_GEN.md`](README_GEN.md) |
| Reconstruct and preselect Λb candidates | `scripts/run_reco_preselection.sh`, `analysis/studies/lb2lambda_gamma_reco.py` | [`studies/reconstruction/README.md`](studies/reconstruction/README.md) |
| Reconstruct the Winter2023 Z→bb inputs in Condor batches | `scripts/run_zbb_preselection_shard.sh` | [`docs/REPOSITORY_GUIDE.md`](docs/REPOSITORY_GUIDE.md#3-reconstruction-and-preselection) |
| Make analysis tables, plots, and BDT/NN studies | `studies/reconstruction/`, `scripts/run_bdt_study.sh`, `scripts/run_nn_study.sh` | [`docs/BDT_WORKFLOW.md`](docs/BDT_WORKFLOW.md) |
| Study detector resolution and acceptance | `analysis/studies/resolutions.py`, `analysis/studies/displaced_daughters.py` | [`studies/resolutions/README.md`](studies/resolutions/README.md) |

Generated and derived data live under ignored `outputs/`, cached central input
files under ignored `work/`, and build products under ignored `external/`.
The current reference reconstruction config is
`config/lb_reco_preselection_15mev_45_65.json`; it uses the fitted Λ⁰ ±15 MeV
window, 4.5–6.5 GeV Λγ mass range, configured vertex/displacement cuts, and
same-thrust-hemisphere requirement. Truth is attached after candidate building.

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
| End-to-end generation, reconstruction, and offline analysis tutorial | [`tutorial/README.md`](tutorial/README.md) | Shell commands and output inspection |
| Reconstruct and preselect Λb candidates | `scripts/run_reco_preselection.sh`, `analysis/studies/lb2lambda_gamma_reco.py` | [`studies/reconstruction/README.md`](studies/reconstruction/README.md) |
| Prepare, validate, and submit all Winter2023 Z→bb Condor batches | `studies/reconstruction/split_input_file_list.py`, `scripts/submit_zbb_full_condor.sh` | [`tutorial/README.md`](tutorial/README.md) |
| Make analysis tables, plots, and BDT/NN studies | `studies/reconstruction/`, `scripts/run_bdt_study.sh`, `scripts/run_nn_study.sh` | [`docs/BDT_WORKFLOW.md`](docs/BDT_WORKFLOW.md) |
| Study detector resolution and acceptance | `analysis/studies/resolutions.py`, `analysis/studies/displaced_daughters.py` | [`studies/resolutions/README.md`](studies/resolutions/README.md) |

Generated and derived data live under ignored `outputs/`, cached central input
files under ignored `work/`, and build products under ignored `external/`.
The current reference reconstruction config is
`config/lb_reco_preselection_15mev_45_65.json`; it uses the fitted Λ⁰ ±15 MeV
window, 4.5–6.5 GeV Λγ mass range, configured vertex/displacement cuts, and
same-thrust-hemisphere requirement. Truth is attached after candidate building.

## Submit the full Winter2023 Z→bb reconstruction

The ordered source manifest is tracked at
[`config/zbb_winter2023_full_file_list.txt`](config/zbb_winter2023_full_file_list.txt).
It contains 4,398 EOS ROOT paths. The generator writes 600 batch lists, one
job card per batch, a Condor queue file, and a provenance manifest under
[`condor/zbb_winter2023_full/`](condor/zbb_winter2023_full/). Each batch has 7
or 8 files. To regenerate those files from the repository root:

```bash
env -u PYTHONPATH -u PYTHONHOME myenv/bin/python \
  studies/reconstruction/split_input_file_list.py \
  --input-list config/zbb_winter2023_full_file_list.txt \
  --output-dir condor/zbb_winter2023_full/batches \
  --n-shards 600 \
  --job-spec-dir condor/zbb_winter2023_full/job_cards \
  --queue-list condor/zbb_winter2023_full/jobs.txt \
  --output-root /eos/lhcb/lbdt3/user/rquaglia/fcc_ee/lblgamma/outputs/zbb_full_condor \
  --ncpus 4 --event-limit all \
  --reco-config config/lb_reco_preselection_15mev_45_65.json
```

Inspect a batch and its job settings, optionally execute that same card locally,
then validate and submit all 600 Condor jobs:

```bash
cat condor/zbb_winter2023_full/batches/file_list_chunk0.txt
cat condor/zbb_winter2023_full/job_cards/job_000.txt
# This runs a complete 7–8-file production batch; use the bounded pilot below for local smoke tests.
bash scripts/run_zbb_preselection_shard.sh condor/zbb_winter2023_full/job_cards/job_000.txt
scripts/submit_zbb_full_condor.sh --dry-run
scripts/submit_zbb_full_condor.sh
```

The submitter checks the manifest, every chunk, every card, and all 600 queue
entries before calling `condor_submit`. Outputs and scheduler logs go to
`/eos/lhcb/lbdt3/user/rquaglia/fcc_ee/lblgamma/outputs/zbb_full_condor/`.
The job description assumes that the repository and EOS inputs/outputs are
mounted on Condor execute nodes. See the
[`full tutorial`](tutorial/README.md#run-one-condor-style-job-locally) for the
bounded 1,000-event local and Condor pilot, monitoring, and merge commands.

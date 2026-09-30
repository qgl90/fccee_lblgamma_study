# Repository run guide

Work from the repository root. Keep generation, detector-response studies,
reconstruction, and physics plots in separate stages. Every long run should
record its input list, config/cards, software revision, event limit, seeds, and
output directory. Generated ROOT files and plots are ignored under `outputs/`;
central samples are cached under `work/`.

## Repository map

| Path | Role | Use it for |
|---|---|---|
| `Snakefile`, `config/config.yaml` | Local staged workflows and canonical event counts/seeds | Reproducible generation and 1k/100k preselection targets |
| `scripts/produce_chunk.sh`, `scripts/merge_chunks.sh`, `scripts/prepare_pythia_card.py` | One generated chunk, checked merge, Pythia card preparation | Local or Condor forced-sample generation |
| `evtgen/`, `cards/` | Decay models and detector/generator cards | Generation provenance |
| `analysis/studies/lb2lambda_gamma_*.py`, `analysis/studies/lb_candidate_*.h`, `analysis/studies/lb_event_selection.h` | Current reconstructed candidate builder, truth annotation, and event requirements | Nominal Λb preselection |
| `scripts/run_reco_preselection.sh`, `scripts/run_zbb_preselection_shard.sh` | Single/list input reconstruction and source-preserving Zbb batches | Local validation or Condor reconstruction |
| `studies/reconstruction/` | Flattening, candidate preselection, cutflows, plots, BDT/NN datasets and studies | Post-reconstruction analysis |
| `analysis/studies/resolutions.py`, `analysis/studies/displaced_daughters.py` | FCCAnalyses extraction of truth and reconstructed detector-response quantities | Inputs to acceptance/resolution studies only |
| `studies/resolutions/` | Standalone response plots and tabulated fits | Track, photon, displaced-daughter resolution/acceptance |
| `docs/` | Workflow, variables, provenance and PI review notes | Physics and software decisions |

Early `analysis/*.py` studies and loose root-level notebooks/commands are
archived under `archive/prototypes/`. Historical parquet and plot outputs were
moved under ignored `outputs/` paths. The current reconstruction entry point
is `analysis/studies/lb2lambda_gamma_reco.py`; new preselection work starts
there rather than combining prototype scripts into the production chain.

## 0. Environment setup

Use separate Key4hep environments for generation and FCCAnalyses. Generation
uses the `2023-04-08` stack configured in `config/config.yaml`; the local
FCCAnalyses checkout supplies the reconstruction environment. From the repo
root, check local inputs and build once:

```bash
bash scripts/fetch_local_inputs.sh
bash scripts/check_environment.sh
bash scripts/build_fccanalyses.sh 4
```

The build script checks the pinned FCCAnalyses checkout and records its
revision. Do not source the generation stack in the shell that launches
Snakemake. `produce_chunk.sh` sources it inside each generation job, while
`run_reco_preselection.sh` sources the FCCAnalyses setup for reconstruction.

## 1. Event generation

The default `Snakefile` target makes the 500k PHSP Λγ and Λη files. For the
three explicitly named 100k samples used in the present preselection, the
configuration is `preselection_generation` in `config/config.yaml`:

| Label | Decay file | Base seed | Output stem |
|---|---|---:|---|
| `signal_phsp` / `Lb2LambdaGamma` | `evtgen/Lb2LambdaGamma.dec` | 71501 | `Lb2LambdaGamma_nev100000` |
| `signal_physics` / `Lb2LambdaGammaPhysics` | `evtgen/Lb2LambdaGamma_trpol.dec` | 71601 | `Lb2LambdaGammaPhysics_nev100000` |
| `lbgamma_eta` / `Lb2LambdaEta` | `evtgen/Lb2LambdaEta.dec` | 71701 | `Lb2LambdaEta_nev100000` |

Each uses ten independent chunks of 10,000 events; chunk seed is base seed plus
the zero-based chunk number. These are forced-decay samples, not physical-rate
predictions. The HELAMP file is an angular-model scenario; it does not by
itself specify the Λb production polarization at the Z pole.

### Local Snakemake generation

From a shell where the Key4hep generation stack is not already sourced, inspect
and then run the three merge targets:

```bash
env -u PYTHONPATH -u PYTHONHOME XDG_CACHE_HOME="$PWD/.snakemake/cache" \
  myenv/bin/python -m snakemake --snakefile Snakefile --cores 12 \
  --printshellcmds --dry-run \
  outputs/delphes/Lb2LambdaGamma_nev100000_IDEA_edm4hep.root \
  outputs/delphes/Lb2LambdaGammaPhysics_nev100000_IDEA_edm4hep.root \
  outputs/delphes/Lb2LambdaEta_nev100000_IDEA_edm4hep.root

env -u PYTHONPATH -u PYTHONHOME XDG_CACHE_HOME="$PWD/.snakemake/cache" \
  myenv/bin/python -m snakemake --snakefile Snakefile --cores 12 \
  --printshellcmds \
  outputs/delphes/Lb2LambdaGamma_nev100000_IDEA_edm4hep.root \
  outputs/delphes/Lb2LambdaGammaPhysics_nev100000_IDEA_edm4hep.root \
  outputs/delphes/Lb2LambdaEta_nev100000_IDEA_edm4hep.root
```

Snakemake runs all 30 chunk jobs, validates each ROOT `events` count, then
merges the ten chunks per sample. Logs are in `outputs/logs/`.

### Condor generation

For shared-filesystem Condor, edit `REPO_DIR` in
`scripts/condor_forced_samples_100k.sub`, then inspect the queue without
submitting:

```bash
scripts/submit_forced_samples_100k_condor.sh --dry-run
```

When the printed 30 rows and paths are correct, submit:

```bash
scripts/submit_forced_samples_100k_condor.sh
```

The queue is generated from `config/config.yaml`, not maintained separately.
Every Condor job runs the same `produce_chunk.sh` helper as Snakemake and writes
to unique chunk/log names. This submit file assumes the repository and CVMFS
are visible on execute nodes (`should_transfer_files = NO`). After all jobs
complete, merge and validate:

```bash
bash scripts/merge_chunks.sh Lb2LambdaGamma 100000 10
bash scripts/merge_chunks.sh Lb2LambdaGammaPhysics 100000 10
bash scripts/merge_chunks.sh Lb2LambdaEta 100000 10
```

Use `--help` on the shell helpers for argument descriptions. If a job is
interrupted, keep its log and partial ROOT file until the exact entry-count
check identifies whether it is recoverable or incomplete.

## 2. Reconstruction and preselection

The reference config is `config/lb_reco_preselection_15mev_45_65.json`:

- reconstruct opposite-charge displaced track pairs and fit the two-track Λ⁰
  vertex once per pair;
- apply the fitted Λ⁰ mass window of ±15 MeV before Λγ combinations;
- apply the 4.5–6.5 GeV Λγ mass window, configured vertex/displacement cuts,
  and same-thrust-hemisphere requirement;
- attach truth labels after candidate construction;
- filter the reconstruction output to events with `n_lb > 0`.

The `n_lb > 0` filter is after the fits and combinations. It reduces output and
later flattening, but not reconstruction CPU. Use the generated/input count or
a separate cutflow as the event-efficiency denominator. Candidate tables have
one row per selected candidate and do not contain empty events.

For the standard 100k three-sample run, request the candidate Parquet and flat
ROOT files. This target also triggers missing generation and reconstruction
dependencies:

```bash
env -u PYTHONPATH -u PYTHONHOME XDG_CACHE_HOME="$PWD/.snakemake/cache" \
  myenv/bin/python -m snakemake --snakefile Snakefile --cores 12 \
  --printshellcmds --dry-run \
  outputs/analysis/studies/nominal_preselection_100k/signal_phsp_candidates.parquet \
  outputs/analysis/studies/nominal_preselection_100k/signal_physics_candidates.parquet \
  outputs/analysis/studies/nominal_preselection_100k/lbgamma_eta_candidates.parquet

env -u PYTHONPATH -u PYTHONHOME XDG_CACHE_HOME="$PWD/.snakemake/cache" \
  myenv/bin/python -m snakemake --snakefile Snakefile --cores 12 \
  --printshellcmds \
  outputs/analysis/studies/nominal_preselection_100k/signal_phsp_candidates.parquet \
  outputs/analysis/studies/nominal_preselection_100k/signal_physics_candidates.parquet \
  outputs/analysis/studies/nominal_preselection_100k/lbgamma_eta_candidates.parquet
```

The paired `.root` candidate tables and `*_candidates.summary.json` files are
also written. Use the ROOT source files under
`outputs/delphes/*_nev100000_IDEA_edm4hep.root` as reconstruction inputs. For a
single file or a text list (comments beginning with `#` are ignored), the
runner is:

```bash
scripts/run_reco_preselection.sh --help
scripts/run_reco_preselection.sh signal_phsp INPUT.root OUTPUT.root all \
  config/lb_reco_preselection_15mev_45_65.json 4
```

For the first 1,000 events of each cached input, use
`scripts/run_preselection_pilot.sh --help` and its paired baseline/nominal
output. See [`studies/reconstruction/README.md`](../studies/reconstruction/README.md)
for column names, cutflows, plots, BDT and NN commands.

### Winter2023 Z→bb batches

Catalog the central input and create 600 ordered file lists using
[`catalog_zbb_winter2023.py`](../studies/reconstruction/catalog_zbb_winter2023.py)
and [`split_input_file_list.py`](../studies/reconstruction/split_input_file_list.py).
The verified campaign list contains 4,398 files and 438,738,637 events, slightly
below the 440,140,845-event target. The generator writes 600 contiguous input
lists plus one `job_NNN.txt` card per list. Each card records the input batch,
full manifest, output directory, CPU count, event limit, and reconstruction
config. The shard runner accepts that card as its only argument; Condor and a
local test use the same command. Per-file `source_id` values are recovered
from the full manifest for held-out BDT splits.

```bash
env -u PYTHONPATH -u PYTHONHOME myenv/bin/python \
  studies/reconstruction/split_input_file_list.py \
  --input-list config/zbb_winter2023_full_file_list.txt \
  --output-dir condor/zbb_winter2023_full/batches \
  --n-shards 600 \
  --job-spec-dir condor/zbb_winter2023_full/job_cards \
  --queue-list condor/zbb_winter2023_full/jobs.txt \
  --output-root /eos/lhcb/lbdt3/user/rquaglia/fcc_ee/lblgamma/outputs/zbb_full_condor \
  --ncpus 4 --event-limit all
cat condor/zbb_winter2023_full/job_cards/job_000.txt
bash scripts/run_zbb_preselection_shard.sh \
  condor/zbb_winter2023_full/job_cards/job_000.txt
scripts/submit_zbb_full_condor.sh --dry-run
scripts/submit_zbb_full_condor.sh
```

The submitter validates that all 600 ordered batches and job cards match the
tracked manifest before queuing the jobs. It creates the EOS Condor log
directory and submits `scripts/condor_zbb_full_eos_600.sub`. Use
`condor_q -nobatch` to monitor active jobs and count `SHARD_COMPLETE.txt`
markers on EOS before merging.

The exact catalog, list-generation, submission, and merge commands are in
[`studies/reconstruction/README.md`](../studies/reconstruction/README.md).

## 3. Analysis studies and plots

Run only after reconstruction and flattening. Main entry points are:

```bash
bash scripts/run_bdt_study.sh --help
bash scripts/run_nn_study.sh --help
```

The BDT workflow stages are documented in
[`docs/BDT_WORKFLOW.md`](BDT_WORKFLOW.md), feature definitions in
[`docs/BDT_FEATURES.md`](BDT_FEATURES.md), and the current interpretation and
statistics limits in [`docs/BDT_REVIEW_2026-09-29.md`](BDT_REVIEW_2026-09-29.md).
Additional cut scans and candidate plots are in `studies/reconstruction/`.
Keep training labels/ancestry separate from the reconstructed features, and
report candidate counts and distinct event counts separately.

## 4. Resolution and acceptance inputs

These are detector-response studies, not candidate preselection or BDT stages.
The FCCAnalyses extraction scripts are
`analysis/studies/resolutions.py` and
`analysis/studies/displaced_daughters.py`; the latter selects truth Λ⁰ and K⁰S
daughters for response measurement. Run these against the generated EDM4hep
inputs using the command blocks in
[`analysis/studies/README.md`](../analysis/studies/README.md). Then make
standalone plots/tables with the scripts under `studies/resolutions/`; see
[`studies/resolutions/README.md`](../studies/resolutions/README.md) and
[`FINDINGS.md`](../studies/resolutions/FINDINGS.md).

Report generated-object denominators, matching/selected-container efficiencies,
and resolution widths in their defined fiducial regions. Do not use truth as a
candidate-building or data-selection input. Resolution/acceptance runs and
plots belong under their own named output subdirectories and should not be
mixed with reconstruction or BDT outputs.

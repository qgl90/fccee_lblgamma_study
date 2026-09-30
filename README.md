# Local Λb production and FCCAnalyses workflow

For the PI-reviewed analysis decisions, stage gates, provenance, and planned
event-level/detector/veto extensions, see
[docs/ANALYSIS_WORKFLOW.md](docs/ANALYSIS_WORKFLOW.md). Future analysis agents
should also read [AGENTS.md](AGENTS.md).

This repository is being organized into distinct stages. The Snakemake workflow stops after producing local EDM4hep files. An independent FCCAnalyses detector-response study now consumes the Λb → Λγ output; decay reconstruction and later physics studies remain separate.

## 1. Environment and local FCCAnalyses checkout

Use the local `external/FCCAnalyses` checkout. The required branch is **`pre-edm4hep1`**, at commit **`91c7d6c5a5c8ad5c3848d6d7cf8383e93c9b74e3`**. This is one local commit after upstream `origin/pre-edm4hep1` and corresponds to the `rquaglia/pre-edm4hep1_lblgamm` ref in the current checkout. Its `setup.sh` pins Key4hep **`2024-03-10`** for the FCCAnalyses build and later reconstruction. The checkout currently also contains uncommitted edits in `myUtils.h` and `myUtils.cc`; these are included when building locally. Preserve or commit those edits before trying to reproduce the build elsewhere.

The generator uses the older Key4hep **`2023-04-08`** stack, which provides `DelphesPythia8EvtGen_EDM4HEP_k4Interface`. Its setup path is in `config/config.yaml`. Keep these two environments in separate shells.

From the repository root:

```bash
bash scripts/fetch_local_inputs.sh
bash scripts/check_environment.sh
```

The fetch script downloads only missing winter2023 Pythia, Delphes, and EvtGen reference cards. It preserves local copies. The two signal decay files are maintained in this repository.

If `external/FCCAnalyses` is absent on another machine, obtain the local commit from the `qgl90/FCCAnalyses` fork before building:

```bash
git clone --branch pre-edm4hep1 https://github.com/HEP-FCC/FCCAnalyses.git external/FCCAnalyses
git -C external/FCCAnalyses remote add rquaglia https://github.com/qgl90/FCCAnalyses.git
git -C external/FCCAnalyses fetch rquaglia pre-edm4hep1_lblgamm
git -C external/FCCAnalyses merge --ff-only 91c7d6c5a5c8ad5c3848d6d7cf8383e93c9b74e3
```

The branch and commit are checked by the build script. It will stop on a mismatch instead of silently using another FCCAnalyses version.

## 2. Build FCCAnalyses source

```bash
bash scripts/build_fccanalyses.sh 4
```

The argument is the number of build jobs. The script sources the checkout's `setup.sh` and runs `fccanalysis build` locally. Build products stay under `external/FCCAnalyses`. It records the branch, commit, stack, and local source status in `outputs/build/fccanalyses_revision.txt`.

## 3. Produce local Pythia8 + EvtGen + Delphes EDM4hep files

See [README_GEN.md](README_GEN.md) for exact Snakemake commands and the direct Bash alternative.

The `Snakefile` default target produces both samples with **500,000 events**, in ten independently seeded chunks of 50,000 per sample. It merges the chunks only after all counts pass validation:

| Sample | Forced decay file | Pythia seed range | Output |
| --- | --- | ---: | --- |
| `Lb2LambdaGamma` | `evtgen/Lb2LambdaGamma.dec` | 22345–22354 | `outputs/delphes/Lb2LambdaGamma_nev500000_IDEA_edm4hep.root` |
| `Lb2LambdaEta` | `evtgen/Lb2LambdaEta.dec` | 22355–22364 | `outputs/delphes/Lb2LambdaEta_nev500000_IDEA_edm4hep.root` |

Both use the local winter2023 Pythia, IDEA Delphes, EDM4hep, `DECAY.DEC`, and `evt.pdl` cards under `cards/` and `evtgen/`. The Pythia card sets `eCM = 91.188` GeV. These card files must be present locally; Snakemake does not download or replace them. The EvtGen decay fractions are forced to one for sample generation and do not represent physical branching fractions.

Run Snakemake outside a sourced Key4hep shell to avoid mixing its Python packages with the Snakemake environment:

```bash
env -u PYTHONPATH -u PYTHONHOME XDG_CACHE_HOME="$PWD/.snakemake/cache" \
  myenv/bin/python -m snakemake --cores 20 --dry-run
env -u PYTHONPATH -u PYTHONHOME XDG_CACHE_HOME="$PWD/.snakemake/cache" \
  myenv/bin/python -m snakemake --cores 20
```

If `myenv` is unavailable, any Python environment with Snakemake can run the same commands. Each chunk job sources the configured `2023-04-08` stack itself. Logs are written to `outputs/logs/`, and chunks remain under `outputs/delphes/chunks/`. The event count is in the output name so the earlier 50,000 and 10,000 event files are preserved. The new seeds differ from the earlier 50,000-event runs, avoiding repeated events. A completed merged job must produce a ROOT `events` tree with exactly 500,000 entries. Detailed decay validation remains a separate check.

## 4. Detector response and reconstruction studies

The EDM4hep files feed separate FCCAnalyses reconstruction scripts with
explicit inputs and output trees. Standalone uproot/awkward code consumes
those trees for physics plots; generation and reconstruction are not part
of the same Snakemake target.

The independent detector-response studies are described in [analysis/studies/README.md](analysis/studies/README.md): `fccanalysis run` scripts for all generated charged particles and photons, and for displaced proton and pion daughters of Lambda0 and K0S.
Their standalone uproot/awkward plotting workspace, using mplhep LHCb2 style, is [studies/resolutions/README.md](studies/resolutions/README.md).
The [response findings](studies/resolutions/FINDINGS.md) compare card inputs with measured acceptance, matching and displaced-daughter behaviour.
The direct `Lambda_b -> Lambda0 gamma` photon matching and selection study uses [run_signal_photons.py](studies/resolutions/run_signal_photons.py) on the full 500,000-event Gamma extraction.
The study slide deck is [slides/resolution.tex](slides/resolution.tex); compile it from `slides/` so its relative figure paths resolve.
The shared `Lambda_b -> Lambda0 gamma` and `Lambda_b -> Lambda0 eta(gamma gamma)` candidate builder, 1,000-event reconstruction commands, truth ancestry checks, candidate-level Parquet files, mass plots, and staged study plan are in [studies/reconstruction/README.md](studies/reconstruction/README.md).

### Nominal preselection test

The staged target keeps labels `signal_phsp`, `signal_physics`,
`lbgamma_eta`, and `zbb`. It processes the first 1,000 events of each local
input, applies the fitted-Λ ±15 MeV window before photon combinations, then
applies 4.5–6.5 GeV in m(Λγ). Candidate Parquet tables retain kinematics,
displacement, photon measurements, and truth labels. Preview and run the
same Snakemake targets with:

```bash
env -u PYTHONPATH -u PYTHONHOME XDG_CACHE_HOME="$PWD/.snakemake/cache" \
  myenv/bin/python -m snakemake --snakefile Snakefile --cores 1 --printshellcmds \
  --allowed-rules preselection_reconstruct preselection_flatten preselection_filter \
  --dry-run \
  outputs/analysis/studies/nominal_preselection_1000/signal_phsp_summary.json \
  outputs/analysis/studies/nominal_preselection_1000/signal_physics_summary.json \
  outputs/analysis/studies/nominal_preselection_1000/lbgamma_eta_summary.json \
  outputs/analysis/studies/nominal_preselection_1000/zbb_summary.json

env -u PYTHONPATH -u PYTHONHOME XDG_CACHE_HOME="$PWD/.snakemake/cache" \
  myenv/bin/python -m snakemake --snakefile Snakefile --cores 1 --printshellcmds \
  --allowed-rules preselection_reconstruct preselection_flatten preselection_filter \
  outputs/analysis/studies/nominal_preselection_1000/signal_phsp_summary.json \
  outputs/analysis/studies/nominal_preselection_1000/signal_physics_summary.json \
  outputs/analysis/studies/nominal_preselection_1000/lbgamma_eta_summary.json \
  outputs/analysis/studies/nominal_preselection_1000/zbb_summary.json
```

The local test reuses existing EDM4hep files and does not invoke the default
500k-event generator target. The per-file runner documents its arguments with
`scripts/run_reco_preselection.sh --help`.

### 100k signal samples and full Winter2023 Zbb processing

Generate the three forced samples as explicit 100k-event Snakemake targets;
this does not change the default 500k PHSP/η generation:

```bash
env -u PYTHONPATH -u PYTHONHOME XDG_CACHE_HOME="$PWD/.snakemake/cache" \
  myenv/bin/python -m snakemake --snakefile Snakefile --cores 20 --printshellcmds \
  --dry-run \
  outputs/delphes/Lb2LambdaGamma_nev100000_IDEA_edm4hep.root \
  outputs/delphes/Lb2LambdaGammaPhysics_nev100000_IDEA_edm4hep.root \
  outputs/delphes/Lb2LambdaEta_nev100000_IDEA_edm4hep.root
```

Remove `--dry-run` to generate them. Winter2023 campaign metadata declares
438,738,637 Zbb events in 4,398 files, which is 1,402,208 below 440,140,845.
All 4,398 ROOT headers were readable, with no failures, and their event-count
sum matches the campaign metadata exactly. The requested 440,140,845 events
therefore are not present in this Winter2023 list.

To generate the same three 100k samples and run their 15 MeV / 4.5–6.5 GeV
preselection, target these summaries (preview first with `--dry-run`, then
remove that flag to execute):

```bash
env -u PYTHONPATH -u PYTHONHOME XDG_CACHE_HOME="$PWD/.snakemake/cache" \
  myenv/bin/python -m snakemake --snakefile Snakefile --cores 20 --printshellcmds \
  --dry-run \
  outputs/analysis/studies/nominal_preselection_100k/signal_phsp_summary.json \
  outputs/analysis/studies/nominal_preselection_100k/signal_physics_summary.json \
  outputs/analysis/studies/nominal_preselection_100k/lbgamma_eta_summary.json
```

For the full catalog and 600 Condor jobs, write the readable ROOT-file list
and inspect the event total:

```bash
env -u PYTHONPATH -u PYTHONHOME myenv/bin/python \
  studies/reconstruction/catalog_zbb_winter2023.py \
  --output outputs/analysis/studies/Zbb_winter2023_catalog_all.json \
  --all-files-output outputs/analysis/studies/Zbb_winter2023_all_files.txt \
  --target-events 1 --workers 32
```

The verified ordered manifest has already been split into 600 lists under
`outputs/analysis/studies/Zbb_winter2023_chunks_600/` (402 lists of 7 files,
198 lists of 8). Recreate them with:

```bash
myenv/bin/python studies/reconstruction/split_input_file_list.py \
  --input-list outputs/analysis/studies/Zbb_winter2023_all_files.txt \
  --output-dir outputs/analysis/studies/Zbb_winter2023_chunks_600 \
  --n-shards 600
```

To run reconstruction on chunk 0 as one combined FCCAnalyses input chain:

```bash
scripts/run_reco_preselection.sh zbb \
  outputs/analysis/studies/Zbb_winter2023_chunks_600/file_list_chunk0.txt \
  outputs/analysis/studies/zbb_chunk0_reco.root all \
  config/lb_reco_preselection_15mev_45_65.json 4
```

This command makes one combined ROOT output. Use the Condor shard helper below
for the full flattening/preselection chain, which reconstructs files separately
to retain their source IDs.

The shard helper assigns 7 or 8 source files per job and processes each file
separately to preserve its `source_id` for BDT splits. The [Condor submit
template](scripts/condor_zbb_preselection_600.sub) assumes the repository,
EOS inputs, CVMFS environments, and output directory are visible on execute
nodes. Check those paths, then submit:

```bash
mkdir -p outputs/analysis/studies/zbb_preselection15_all/condor_logs
condor_submit scripts/condor_zbb_preselection_600.sub
```

After the jobs finish, merge their selected/rejected candidate tables:

```bash
env -u PYTHONPATH -u PYTHONHOME myenv/bin/python \
  studies/reconstruction/merge_preselection_parquets.py \
  --input-dir outputs/analysis/studies/zbb_preselection15_all \
  --output-dir outputs/analysis/studies/zbb_preselection15_merged
```

## 5. Winter2023 Zbb BDT study

The [stage-by-stage runner](scripts/run_bdt_study.sh) processes local PHSP
and HELAMP signal, Λη feed-down, and ten central Winter2023 IDEA Zbb files.
[Workflow instructions](docs/BDT_WORKFLOW.md),
[current BDT input definitions](docs/BDT_FEATURES.md), and the
[PI review with observed counts and limitations](docs/BDT_REVIEW_2026-09-29.md)
document the study. The generated
[34-page review presentation](slides/bdt_winter2023_v1.pdf) contains the
resolution, selection, mass–angle, and held-out BDT plots.

The [neural-network runner](scripts/run_nn_study.sh) trains and scores three
reconstructed-input variants on the same frozen split. Its
[PI review](docs/NN_REVIEW_2026-09-29.md) compares the selected network
with the BDT and states the finite-Zbb-MC purity limit. The
[NN presentation](slides/nn_winter2023_v1.pdf) and
[independent Zbb extension runner](scripts/run_nn_zbb_extension.sh) are
separate from stage-1 candidate reconstruction.

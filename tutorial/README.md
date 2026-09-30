# Λb → Λ⁰γ workflow tutorial

This tutorial gives a shell-first path from forced event generation through Delphes, nominal reconstruction, candidate tables, and first offline plots. Run commands from the repository root. The current reconstruction scenario is [`config/lb_reco_preselection_15mev_45_65.json`](../config/lb_reco_preselection_15mev_45_65.json): fitted Λ⁰ mass within 15 MeV of 1.115683 GeV, Λγ mass from 4.5 to 6.5 GeV, vertex and displacement requirements, and the same-thrust-hemisphere requirement.

Use PHSP as the acceptance reference, `signal_physics` for the HELAMP angular model, and `lbgamma_eta` as a partially reconstructed one-photon background study. Forced-decay sample fractions are not physical event yields. Both Λb charges are generated. Keep event counts, candidate counts, and truth-matched counts separate in every report.

## 0. Check the local setup

Generation uses the Key4hep setup in `config/config.yaml`; reconstruction uses the local FCCAnalyses build. Do not source both setups in the same shell.

```bash
bash scripts/fetch_local_inputs.sh
bash scripts/check_environment.sh
bash scripts/build_fccanalyses.sh 4
scripts/produce_chunk.sh --help
scripts/merge_chunks.sh --help
scripts/run_reco_preselection.sh --help
```

Generator chunks and merged ROOT samples are under `outputs/delphes/`; generation logs are under `outputs/logs/`. The FCC revision is recorded under `outputs/build/`.

## 1. Generate 100k Delphes samples

The three named samples each contain ten independent 10,000-event chunks. Base seeds and EvtGen files are in `config/config.yaml` under `preselection_generation`.

Inspect the planned commands:

```bash
env -u PYTHONPATH -u PYTHONHOME XDG_CACHE_HOME="$PWD/.snakemake/cache" \
  myenv/bin/python -m snakemake --snakefile Snakefile --cores 12 \
  --printshellcmds --dry-run \
  outputs/delphes/Lb2LambdaGamma_nev100000_IDEA_edm4hep.root \
  outputs/delphes/Lb2LambdaGammaPhysics_nev100000_IDEA_edm4hep.root \
  outputs/delphes/Lb2LambdaEta_nev100000_IDEA_edm4hep.root
```

Generate and merge:

```bash
env -u PYTHONPATH -u PYTHONHOME XDG_CACHE_HOME="$PWD/.snakemake/cache" \
  myenv/bin/python -m snakemake --snakefile Snakefile --cores 12 \
  --printshellcmds \
  outputs/delphes/Lb2LambdaGamma_nev100000_IDEA_edm4hep.root \
  outputs/delphes/Lb2LambdaGammaPhysics_nev100000_IDEA_edm4hep.root \
  outputs/delphes/Lb2LambdaEta_nev100000_IDEA_edm4hep.root
```

Snakemake can rerun generation when an input script or card changes. Existing chunks are reused only after provenance and entry-count checks. Do not remove a `.partial.root` file until its production log and entry count have been checked.

Verify each merged `events` tree:

```bash
source /cvmfs/sw.hsf.org/spackages7/key4hep-stack/2023-04-08/x86_64-centos7-gcc11.2.0-opt/urwcv/setup.sh
python3 scripts/check_root_entries.py outputs/delphes/Lb2LambdaGamma_nev100000_IDEA_edm4hep.root 100000
python3 scripts/check_root_entries.py outputs/delphes/Lb2LambdaGammaPhysics_nev100000_IDEA_edm4hep.root 100000
python3 scripts/check_root_entries.py outputs/delphes/Lb2LambdaEta_nev100000_IDEA_edm4hep.root 100000
ls -lh outputs/delphes/*nev100000_IDEA_edm4hep.root
```

Use a fresh shell for the reconstruction section below; it sources the local FCCAnalyses setup itself.

Inspect production provenance in a chunk log:

```bash
head -n 1 outputs/logs/Lb2LambdaGamma_nev100000_chunk0.production.log
tail -n 5 outputs/logs/Lb2LambdaGamma_nev100000_chunk0.production.log
```

## 2. Reconstruct and apply the nominal selection

Use a 1,000-event run while developing. Pass `all` only when processing the complete input. Integer limits are capped at 1,000.

Example development run:

```bash
mkdir -p outputs/analysis/studies/tutorial_pilot/logs
bash scripts/run_reco_preselection.sh signal_phsp \
  outputs/delphes/Lb2LambdaGamma_nev100000_IDEA_edm4hep.root \
  outputs/analysis/studies/tutorial_pilot/signal_phsp_1k_reco.root \
  1000 config/lb_reco_preselection_15mev_45_65.json 1 \
  > outputs/analysis/studies/tutorial_pilot/logs/signal_phsp_reco.log 2>&1
```

Full-stat commands for the three 100k inputs (four FCCAnalyses threads per sample):

```bash
mkdir -p outputs/analysis/studies/nominal_preselection_100k/logs

bash scripts/run_reco_preselection.sh signal_phsp \
  outputs/delphes/Lb2LambdaGamma_nev100000_IDEA_edm4hep.root \
  outputs/analysis/studies/nominal_preselection_100k/signal_phsp_full100k_reco.root \
  all config/lb_reco_preselection_15mev_45_65.json 4 \
  > outputs/analysis/studies/nominal_preselection_100k/logs/signal_phsp_reco.log 2>&1

bash scripts/run_reco_preselection.sh signal_physics \
  outputs/delphes/Lb2LambdaGammaPhysics_nev100000_IDEA_edm4hep.root \
  outputs/analysis/studies/nominal_preselection_100k/signal_physics_full100k_reco.root \
  all config/lb_reco_preselection_15mev_45_65.json 4 \
  > outputs/analysis/studies/nominal_preselection_100k/logs/signal_physics_reco.log 2>&1

bash scripts/run_reco_preselection.sh lbgamma_eta \
  outputs/delphes/Lb2LambdaEta_nev100000_IDEA_edm4hep.root \
  outputs/analysis/studies/nominal_preselection_100k/lbgamma_eta_full100k_reco.root \
  all config/lb_reco_preselection_15mev_45_65.json 4 \
  > outputs/analysis/studies/nominal_preselection_100k/logs/lbgamma_eta_reco.log 2>&1
```

The builder uses reconstructed objects; truth labels are attached afterward. The `n_lb > 0` filter runs after fitting and candidate construction. The reconstruction ROOT `events` tree therefore holds candidate-bearing events only; its entry count is not the generated-event denominator. Use 100,000 as the input-event denominator. Vertex fitter covariance warnings can occur; inspect the full log and validate the output before proceeding.

Inspect a completed job and its reconstructed tree:

```bash
tail -n 20 outputs/analysis/studies/nominal_preselection_100k/logs/signal_phsp_reco.log
ls -lh outputs/analysis/studies/nominal_preselection_100k/signal_phsp_full100k_reco.root
myenv/bin/python -c 'import uproot,sys; f=uproot.open(sys.argv[1]); t=f["events"]; print("candidate-bearing events:",t.num_entries); print("branches:",len(t.keys())); print("first branches:",t.keys()[:40])' \
  outputs/analysis/studies/nominal_preselection_100k/signal_phsp_full100k_reco.root
cat config/lb_reco_preselection_15mev_45_65.json
```

## 3. Flatten candidate variables

Flatten after reconstruction. This writes one row per selected Λb candidate, with event keys, truth labels, readable LHCb-style aliases, and candidate observables. The flat ROOT tree has the same candidate rows as Parquet. See [`studies/reconstruction/readme_columns.md`](../studies/reconstruction/readme_columns.md) for column definitions.

```bash
env -u PYTHONPATH -u PYTHONHOME myenv/bin/python \
  studies/reconstruction/flatten_candidates.py --mode gamma \
  --input outputs/analysis/studies/nominal_preselection_100k/signal_phsp_full100k_reco.root \
  --output outputs/analysis/studies/nominal_preselection_100k/signal_phsp_candidates.parquet \
  --root-output outputs/analysis/studies/nominal_preselection_100k/signal_phsp_candidates.root \
  --source-id 100 --chunk-events 500

env -u PYTHONPATH -u PYTHONHOME myenv/bin/python \
  studies/reconstruction/flatten_candidates.py --mode gamma \
  --input outputs/analysis/studies/nominal_preselection_100k/signal_physics_full100k_reco.root \
  --output outputs/analysis/studies/nominal_preselection_100k/signal_physics_candidates.parquet \
  --root-output outputs/analysis/studies/nominal_preselection_100k/signal_physics_candidates.root \
  --source-id 101 --chunk-events 500

env -u PYTHONPATH -u PYTHONHOME myenv/bin/python \
  studies/reconstruction/flatten_candidates.py --mode gamma \
  --input outputs/analysis/studies/nominal_preselection_100k/lbgamma_eta_full100k_reco.root \
  --output outputs/analysis/studies/nominal_preselection_100k/lbgamma_eta_candidates.parquet \
  --root-output outputs/analysis/studies/nominal_preselection_100k/lbgamma_eta_candidates.root \
  --source-id 102 --chunk-events 500
```

Inspect the summary, a few rows, and the flat ROOT entry count:

```bash
cat outputs/analysis/studies/nominal_preselection_100k/signal_phsp_candidates.summary.json
myenv/bin/python -c 'import pyarrow.parquet as pq,sys; t=pq.read_table(sys.argv[1]); print("candidate rows:",t.num_rows); print("columns:",t.column_names); print(t.select([c for c in ["event_entry","candidate_slot","candidates_in_event","lb_mass","lambda_mass","lb_truth_matched","lb_cos_theta_p","Lambda0_d0","Lambda0_d0Significance","Gamma_RecoIndex","Gamma_IsoR03"] if c in t.column_names]).slice(0,5).to_pandas().to_string(index=False))' \
  outputs/analysis/studies/nominal_preselection_100k/signal_phsp_candidates.parquet
myenv/bin/python -c 'import uproot,sys; f=uproot.open(sys.argv[1]); t=f["events"]; print("flat candidate rows:",t.num_entries); print("branches:",len(t.keys()))' \
  outputs/analysis/studies/nominal_preselection_100k/signal_phsp_candidates.root
```

Use unique `event_entry` values for event counts and rows for candidate counts. The flattened table omits events with no candidate, so it cannot by itself provide event efficiency.

## 4. Add the inclusive Z→bb background

Start with a 1,000-event local smoke test. The cached first Winter2023 file is
downloaded by `fetch_local_inputs.sh` when available:

```bash
bash scripts/fetch_local_inputs.sh
bash scripts/run_reco_preselection.sh zbb \
  work/cache/winter2023_zbb/events_000083138.root \
  outputs/analysis/studies/tutorial_pilot/zbb_1k_reco.root \
  1000 config/lb_reco_preselection_15mev_45_65.json 1 \
  > outputs/analysis/studies/tutorial_pilot/logs/zbb_reco.log 2>&1
env -u PYTHONPATH -u PYTHONHOME myenv/bin/python \
  studies/reconstruction/flatten_candidates.py --mode zbb \
  --input outputs/analysis/studies/tutorial_pilot/zbb_1k_reco.root \
  --output outputs/analysis/studies/tutorial_pilot/zbb_1k_candidates.parquet \
  --source-id 0 --chunk-events 500
cat outputs/analysis/studies/tutorial_pilot/zbb_1k_candidates.summary.json
```

For a full campaign, the current readable Winter2023 manifest has 4,398 files
and 438,738,637 events according to its campaign metadata. This is below
440,140,845 events, so process all readable files and report the actual input
denominator. Catalog their ROOT headers and write the complete file list:

```bash
env -u PYTHONPATH -u PYTHONHOME myenv/bin/python \
  studies/reconstruction/catalog_zbb_winter2023.py \
  --output outputs/analysis/studies/Zbb_winter2023_full_manifest.json \
  --all-files-output outputs/analysis/studies/Zbb_winter2023_all_files.txt \
  --target-events 438700000 --workers 8
wc -l outputs/analysis/studies/Zbb_winter2023_all_files.txt
```

The repository keeps the ordered 4,398-path snapshot in
[`config/zbb_winter2023_full_file_list.txt`](../config/zbb_winter2023_full_file_list.txt).
Use this tracked file for reproducible splitting. The catalog command above
can still be used to refresh a campaign snapshot; compare the new paths and
counts before replacing the tracked manifest.

The generator writes plain ROOT file lists and separate job cards with all
runner settings. A job card is the sole runner argument, both locally and in
Condor. Generate the one-file, 1,000-event pilot and inspect its inputs and
settings:

```bash
env -u PYTHONPATH -u PYTHONHOME myenv/bin/python \
  studies/reconstruction/split_input_file_list.py \
  --input-list config/zbb_condor_pilot_1file.txt \
  --output-dir outputs/analysis/studies/zbb_condor_pilot/batches \
  --n-shards 1 \
  --job-spec-dir outputs/analysis/studies/zbb_condor_pilot/jobs \
  --queue-list outputs/analysis/studies/zbb_condor_pilot/jobs.txt \
  --output-root outputs/analysis/studies/zbb_condor_pilot_local \
  --ncpus 1 --event-limit 1000 \
  --reco-config config/lb_reco_preselection_15mev_45_65.json
cat outputs/analysis/studies/zbb_condor_pilot/jobs/job_000.txt
cat outputs/analysis/studies/zbb_condor_pilot/batches/file_list_chunk0.txt
```

The same pilot can be tested locally by running the generated card:

```bash
bash scripts/run_zbb_preselection_shard.sh \
  outputs/analysis/studies/zbb_condor_pilot/jobs/job_000.txt
```

For a separate Condor smoke-test card with EOS output, generate a second card
with identical input and reconstruction settings:

```bash
env -u PYTHONPATH -u PYTHONHOME myenv/bin/python \
  studies/reconstruction/split_input_file_list.py \
  --input-list config/zbb_condor_pilot_1file.txt \
  --output-dir outputs/analysis/studies/zbb_condor_pilot/batches \
  --n-shards 1 \
  --job-spec-dir outputs/analysis/studies/zbb_condor_pilot_condor/jobs \
  --queue-list outputs/analysis/studies/zbb_condor_pilot_condor/jobs.txt \
  --output-root /eos/lhcb/lbdt3/user/rquaglia/fcc_ee/lblgamma/outputs/zbb_full_condor/pilot_1000 \
  --ncpus 1 --event-limit 1000 \
  --reco-config config/lb_reco_preselection_15mev_45_65.json
```

Submit that card with Condor. First check that this pool exposes the shared
repository, reads the input EOS file, and supports writes to the requested EOS
output directory. Create the scheduler log directory before submission:

```bash
mkdir -p /eos/lhcb/lbdt3/user/rquaglia/fcc_ee/lblgamma/outputs/zbb_full_condor/pilot_1000/condor_logs
condor_submit scripts/condor_zbb_full_eos_test.sub
condor_q -nobatch
cat /eos/lhcb/lbdt3/user/rquaglia/fcc_ee/lblgamma/outputs/zbb_full_condor/pilot_1000/condor_logs/pilot.0.out
cat /eos/lhcb/lbdt3/user/rquaglia/fcc_ee/lblgamma/outputs/zbb_full_condor/pilot_1000/shard_000/SHARD_COMPLETE.txt
```

`should_transfer_files = NO` assumes shared mounts on execute nodes. If the
Condor pool does not provide them, adapt to its supported staging method before
submission. The pilot's `event_limit=1000` caps this file's reconstruction.

After checking the pilot, generate the full 600 input batches and job cards.
The complete source list currently has 4,398 files; the generated chunks have
7 or 8 files each. Inspect any exact card and batch before submission:

```bash
env -u PYTHONPATH -u PYTHONHOME myenv/bin/python \
  studies/reconstruction/split_input_file_list.py \
  --input-list config/zbb_winter2023_full_file_list.txt \
  --output-dir outputs/analysis/studies/Zbb_winter2023_chunks_600 \
  --n-shards 600 \
  --job-spec-dir outputs/analysis/studies/Zbb_winter2023_chunks_600/jobs \
  --queue-list outputs/analysis/studies/Zbb_winter2023_chunks_600/jobs.txt \
  --output-root /eos/lhcb/lbdt3/user/rquaglia/fcc_ee/lblgamma/outputs/zbb_full_condor \
  --ncpus 4 --event-limit all \
  --reco-config config/lb_reco_preselection_15mev_45_65.json
cat outputs/analysis/studies/Zbb_winter2023_chunks_600/jobs/job_000.txt
cat outputs/analysis/studies/Zbb_winter2023_chunks_600/file_list_chunk0.txt
```

Any batch is runnable locally with the same one-argument interface; choose a
pilot card for a bounded local run, since the full cards process all listed
files:

```bash
bash scripts/run_zbb_preselection_shard.sh \
  outputs/analysis/studies/Zbb_winter2023_chunks_600/jobs/job_000.txt
```

The production submit file queues the 600 paths in `jobs.txt`; each Condor
process gets one card and writes under its card's EOS `shard_NNN/` directory:

```bash
mkdir -p /eos/lhcb/lbdt3/user/rquaglia/fcc_ee/lblgamma/outputs/zbb_full_condor/condor_logs
condor_submit scripts/condor_zbb_full_eos_600.sub
```

After all 600 `SHARD_COMPLETE.txt` markers exist, merge the candidate tables
from the EOS output directory and inspect the summary:

```bash
find /eos/lhcb/lbdt3/user/rquaglia/fcc_ee/lblgamma/outputs/zbb_full_condor -name SHARD_COMPLETE.txt | wc -l
env -u PYTHONPATH -u PYTHONHOME myenv/bin/python \
  studies/reconstruction/merge_preselection_parquets.py \
  --input-dir /eos/lhcb/lbdt3/user/rquaglia/fcc_ee/lblgamma/outputs/zbb_full_condor \
  --output-dir /eos/lhcb/lbdt3/user/rquaglia/fcc_ee/lblgamma/outputs/zbb_full_condor/merged
cat /eos/lhcb/lbdt3/user/rquaglia/fcc_ee/lblgamma/outputs/zbb_full_condor/merged/merge_summary.json
```

## 5. Offline mass selection and plots

The optional candidate-level selection writes selected and rejected rows while retaining truth labels. It reapplies the nominal mass windows to flattened candidates; it is not the event-level reconstruction cutflow.

```bash
env -u PYTHONPATH -u PYTHONHOME myenv/bin/python \
  studies/reconstruction/preselect_candidates.py \
  --input outputs/analysis/studies/nominal_preselection_100k/signal_phsp_candidates.parquet \
  --output-prefix outputs/analysis/studies/nominal_preselection_100k/signal_phsp
cat outputs/analysis/studies/nominal_preselection_100k/signal_phsp_summary.json
```

Defaults are PDG Λ⁰ mass 1.115683 GeV, ±15 MeV, and 4.5–6.5 GeV for Λγ. Review candidate rows, unique selected events, truth-matched candidates, and wrong or unmatched candidates in the summary. This step cannot recover candidates removed during reconstruction.

Make mass, vertex, and truth-matching plots:

```bash
env -u PYTHONPATH -u PYTHONHOME myenv/bin/python \
  studies/reconstruction/plot_baseline.py \
  --input outputs/analysis/studies/nominal_preselection_100k/signal_phsp_full100k_reco.root \
  --selection-config config/lb_reco_preselection_15mev_45_65.json \
  --output-dir outputs/plots/tutorial/signal_phsp
```

The plot directory contains images, `summary.json`, and `truth_matched_components.csv`. Check denominators before making a signal/eta comparison. For photon isolation, recoil, pointing, and photon-pair observables, compare flattened signal, eta, and Z→bb samples:

```bash
env -u PYTHONPATH -u PYTHONHOME myenv/bin/python \
  studies/reconstruction/plot_stage1_observables.py \
  --signal outputs/analysis/studies/nominal_preselection_100k/signal_phsp_candidates.parquet \
  --eta outputs/analysis/studies/nominal_preselection_100k/lbgamma_eta_candidates.parquet \
  --zbb outputs/analysis/studies/zbb_preselection15_all/merged/zbb_selected.parquet \
  --output-dir outputs/plots/tutorial/stage1_observables
```

Stage-1 quantities are diagnostics, not additional nominal cuts. This is not a trained classifier or a physical-yield prediction. See [`docs/BDT_WORKFLOW.md`](../docs/BDT_WORKFLOW.md) for the separately reviewed BDT workflow.

## 6. Copy products to EOS

After checking each ROOT file and JSON summary, copy the reconstructed ROOT, flat candidate ROOT, and Parquet products to the shared output directory:

```bash
eos_dir=/eos/lhcb/lbdt3/user/rquaglia/fcc_ee/lblgamma/outputs
cp --preserve=mode,timestamps \
  outputs/analysis/studies/nominal_preselection_100k/signal_phsp_full100k_reco.root \
  outputs/analysis/studies/nominal_preselection_100k/signal_physics_full100k_reco.root \
  outputs/analysis/studies/nominal_preselection_100k/lbgamma_eta_full100k_reco.root \
  outputs/analysis/studies/nominal_preselection_100k/signal_phsp_candidates.root \
  outputs/analysis/studies/nominal_preselection_100k/signal_physics_candidates.root \
  outputs/analysis/studies/nominal_preselection_100k/lbgamma_eta_candidates.root \
  outputs/analysis/studies/nominal_preselection_100k/signal_phsp_candidates.parquet \
  outputs/analysis/studies/nominal_preselection_100k/signal_physics_candidates.parquet \
  outputs/analysis/studies/nominal_preselection_100k/lbgamma_eta_candidates.parquet \
  "$eos_dir/"
ls -lh "$eos_dir"
```

For each comparison, record the input file, selection JSON, FCCAnalyses revision, exact command, input-event count, output paths, and summary counts. See [`docs/ANALYSIS_WORKFLOW.md`](../docs/ANALYSIS_WORKFLOW.md) and [`docs/REPOSITORY_GUIDE.md`](../docs/REPOSITORY_GUIDE.md).

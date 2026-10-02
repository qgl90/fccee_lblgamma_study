# Stage 1: reconstruct Λb → Λ⁰(pπ)γ candidates

Run these commands from the repository root. Stage 1 reads **Delphes EDM4hep**
files and writes a ROOT `events` tree containing events with at least one
Λb candidate. Physics, PHSP, and Λb→Λη are each processed directly; the
inclusive Z-flavour samples are split into Condor chunks. The η sample is
deliberately reconstructed under the **one-photon Λb→Λγ hypothesis**.

## The reconstruction shared by both execution modes

The direct runner is [`analysis/studies/lb2lambda_gamma_reco.py`](../analysis/studies/lb2lambda_gamma_reco.py).
The batch wrapper is [`analysis/studies/analysis_preselection_zbb.py`](../analysis/studies/analysis_preselection_zbb.py),
whose `analyzers()` calls that runner's `RDFanalysis.analysers()` and whose
`output()` calls its `RDFanalysis.output()`. Both therefore use the same
[`lb_candidate_builder.h`](../analysis/studies/lb_candidate_builder.h),
[`lb_candidate_truth.h`](../analysis/studies/lb_candidate_truth.h), and
[`lb_candidate_observables.h`](../analysis/studies/lb_candidate_observables.h).
The batch wrapper's historical filename contains `zbb`, but it also handles
Zcc and Zss.

Use the same selection config in both modes:
[`config/lb_reco_preselection_15mev_45_65_3d.json`](../config/lb_reco_preselection_15mev_45_65_3d.json).
The direct command sets `LB_RECO_CONFIG` to this file. The batch wrapper uses
it as its default; the commands below explicitly unset `LB_RECO_CONFIG` to
avoid a different submit-host setting. Both modes also load
[`config/lb_observables.json`](../config/lb_observables.json) for the stored
diagnostic observables. Keep the repository checkout and FCCAnalyses build
fixed across a comparison. A different config or source revision is a new
named reconstruction scenario.

This config selects a fitted Λ⁰ candidate within ±15 MeV of 1.115683 GeV,
requires the configured 3D flight and vertex conditions, combines it with a
selected photon in the same thrust hemisphere, and keeps 4.5–6.5 GeV in
reconstructed m(Λγ). Candidate construction does not use MC truth. Truth is
attached afterward as an output label. The later ±5 MeV Λ⁰ window, photon
vetoes, K⁰S veto, and BDT belong to **offline selection**, not Stage 1.

The truth labeler saves `reco_mc_index`/`reco_mc_pdg` and four successive
ancestors for every reconstructed particle: `reco_mc_parent_*`,
`reco_mc_grandparent_*`, `reco_mc_greatgrandparent_*`, and
`reco_mc_greatgreatgrandparent_*`, where `*` is `index` or `pdg`. Candidate
proton, pion, and photon indices select the corresponding entries. The chain
follows the **first** valid parent at each generation in `Particle#0.index`.
It requires the existing unique stable MC association for the starting
reconstructed particle; otherwise ancestry indices are `-1` and PDGs are
`0`. A missing later ancestor uses the same sentinels from that generation
onward. Multiple-parent ambiguity is not resolved by this single-path
diagnostic; `reco_mc_n_parents` records the starting particle's parent count.
The candidate flattener exports these as `proton_mc_*`, `pion_mc_*`, and
`photon_mc_*` columns; Stage 2 copies the chain into prepared and scored
candidate rows as diagnostic labels. Existing Stage 1 ROOT files must be
reprocessed to contain the two newly added generations.

Current Stage 1 isolation has photon-centered `iso_RXX_*` and fitted
Λ⁰-centered `lambda0_iso_RXX_*` activity at ΔR = 0.2, 0.3, 0.5, 0.7, 1.0,
and 2.0 (`R20`). Both use the fitted Λ⁰ thrust hemisphere. Charged activity
removes the candidate p and π, neutral activity removes the candidate γ,
and all activity removes all three. The older `R70` branch belongs to the
previous observable config and is absent from newly processed tuples.
See [`understand_isolation.md`](understand_isolation.md) for exact definitions.
Use a new campaign name when reprocessing with this changed observable
config; the recorded `_v2` outputs are historical inputs, not equivalent
versions of these fields.

## Environment and provenance

On the machine with the FCCAnalyses build and EOS access:

```bash
cd /afs/cern.ch/work/r/rquaglia/fcc_ee/fccee_lblgamma_study
source external/FCCAnalyses/setup.sh
git rev-parse HEAD
git -C external/FCCAnalyses rev-parse HEAD
sha256sum config/lb_reco_preselection_15mev_45_65_3d.json config/lb_observables.json
```

Record these values, any local source edits, the exact input list and Delphes
card, the command, event limit, and output path with each production. The
completed direct v2 campaign and its hashes are in
[`config/lb_stage1_v2_samples.json`](../config/lb_stage1_v2_samples.json).
Use a fresh output directory for a new run; the examples below do not
overwrite the existing `_v2.root` files.

## Direct runs: Physics, PHSP, and Λb→Λη

Set an output directory with enough space. The following names are examples;
choose a new `RUN_TAG` for each campaign:

```bash
RUN_TAG=stage1_v3_my_run
OUT_DIR="$PWD/outputs/analysis/studies/$RUN_TAG"
mkdir -p "$OUT_DIR"
RECO_CONFIG="$PWD/config/lb_reco_preselection_15mev_45_65_3d.json"
INPUT_DIR=/eos/lhcb/lbdt3/user/rquaglia/fcc_ee/lblgamma/outputs

LB_RECO_CONFIG="$RECO_CONFIG" fccanalysis run analysis/studies/lb2lambda_gamma_reco.py \
  --files-list "$INPUT_DIR/Lb2LambdaGammaPhysics_nev100000_IDEA_edm4hep.root" \
  --output "$OUT_DIR/signal_physics.root" --ncpus 4

LB_RECO_CONFIG="$RECO_CONFIG" fccanalysis run analysis/studies/lb2lambda_gamma_reco.py \
  --files-list "$INPUT_DIR/Lb2LambdaGamma_nev100000_IDEA_edm4hep.root" \
  --output "$OUT_DIR/signal_phsp.root" --ncpus 4

LB_RECO_CONFIG="$RECO_CONFIG" fccanalysis run analysis/studies/lb2lambda_gamma_reco.py \
  --files-list "$INPUT_DIR/Lb2LambdaEta_nev100000_IDEA_edm4hep.root" \
  --output "$OUT_DIR/lbgamma_eta_as_one_photon.root" --ncpus 4
```

These commands have **no `--nevents` limit** and process all 100,000 input
events in each file. For a development check, use a distinct trial output
name and add `--nevents 1000`. Do not combine that trial with a full-run
efficiency denominator.

## Native Condor runs: Zbb, Zcc, or Zss

Run this part on a host with `condor_submit` and mounted `/eos`. Set `SAMPLE`
to `Zbb`, `Zcc`, or `Zss`. Each campaign needs a distinct EOS destination.
The wrapper infers the FCC process name from the parent directory of
`--input-glob`; `--check-only` verifies the files and settings without
submitting jobs.

```bash
cd /afs/cern.ch/work/r/rquaglia/fcc_ee/fccee_lblgamma_study
source external/FCCAnalyses/setup.sh
unset LB_RECO_CONFIG

SAMPLE=Zbb                         # or Zcc or Zss
SAMPLE_LOWER="${SAMPLE,,}"
INPUT_GLOB="/eos/experiment/fcc/ee/generation/DelphesEvents/winter2023/IDEA/p8_ee_${SAMPLE}_ecm91/events_*.root"
OUTPUT_EOS="/eos/lhcb/lbdt3/user/rquaglia/fcc_ee/lblgamma/outputs/${SAMPLE_LOWER}_full_condor/native_batch_3d_activity_v3"

fccanalysis run analysis/studies/analysis_preselection_zbb.py \
  --input-glob "$INPUT_GLOB" --chunks 1200 \
  --comp-group group_u_LHCBT3.e_lhcb_lbd --queue workday --ncpus 4 \
  --output-eos "$OUTPUT_EOS" --eos-type eoslhcb --check-only
```

Once the check prints the intended sample name, config, file count, chunk
count, and EOS destination, submit **the same command without `--check-only`**:

```bash
fccanalysis run analysis/studies/analysis_preselection_zbb.py \
  --input-glob "$INPUT_GLOB" --chunks 1200 \
  --comp-group group_u_LHCBT3.e_lhcb_lbd --queue workday --ncpus 4 \
  --output-eos "$OUTPUT_EOS" --eos-type eoslhcb
```

Repeat the variable assignment and two commands for each sample. On
2026-10-02, check-only found 4,398 Zbb, 5,018 Zcc, and 5,015 Zss ROOT
inputs with 1,200 chunks requested. These are file counts, **not event
counts**. The batch dispatcher rewrites central mounted EOS inputs to
`root://eospublic.cern.ch` and copies chunk outputs to
`$OUTPUT_EOS/p8_ee_${SAMPLE}_ecm91/chunk_N.root`. It writes generated job
scripts and logs under `external/FCCAnalyses/BatchOutputs/<timestamp>/`.
Record the actual timestamped directory printed by the submission. The
`--check-only` runs above did not submit anything; this machine does not have
Condor installed.

## Check outputs and event denominators

For each direct output, run the v2 branch-length validator and keep its JSON
beside the ROOT file:

```bash
env -u PYTHONPATH -u PYTHONHOME myenv/bin/python \
  studies/reconstruction/verify_stage1_v2_outputs.py \
  --input "$OUT_DIR/signal_physics.root" \
  --output "$OUT_DIR/signal_physics_validation.json"
```

Repeat for `signal_phsp.root` and `lbgamma_eta_as_one_photon.root`. The JSON
reports candidate-bearing events and candidates. The input denominator is
100,000 generated events for each of these three forced samples; do not use
the number of output tree entries as the generated denominator.

After **all** Condor chunks finish, catalog each campaign with the actual
job directory. The catalog verifies the source-file assignment, ROOT schema,
`eventsProcessed`, `eventsSelected`, missing chunks, and duplicates:

```bash
JOB_DIR="external/FCCAnalyses/BatchOutputs/<actual_timestamp>/p8_ee_${SAMPLE}_ecm91"
ROOT_DIR="$OUTPUT_EOS/p8_ee_${SAMPLE}_ecm91"
env -u PYTHONPATH -u PYTHONHOME myenv/bin/python \
  studies/reconstruction/catalog_condor_zbb_chunks.py \
  --job-dir "$JOB_DIR" --root-dir "$ROOT_DIR" \
  --output "outputs/analysis/studies/${SAMPLE_LOWER}_stage1_v2_catalog.json"
```

Require the catalog's `valid_chunks` to equal `job_scripts`, with no missing
or invalid chunks, before treating its summed `total_processed_events_in_valid_chunks`
as the background input-event denominator. `eventsSelected` and the ROOT
`events` entries count candidate-bearing output events. Count candidate rows
separately by summing `n_lb` or flattening the tuples. Native chunks mix
several source files, so retain the catalog's exact file-to-chunk mapping
when splitting later training and evaluation samples.

The direct v2 comparison is reviewed in
[`docs/STAGE1_V2_FULL_REPROCESS_REVIEW_2026-10-01.md`](../docs/STAGE1_V2_FULL_REPROCESS_REVIEW_2026-10-01.md).
The candidate columns and downstream steps are described in
[`studies/reconstruction/README.md`](../studies/reconstruction/README.md).
Continue with the copyable offline-selection and BDT commands in
[stage2.md](stage2.md).

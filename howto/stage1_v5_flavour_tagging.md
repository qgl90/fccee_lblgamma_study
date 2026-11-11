# v5 Stage 1: event-jet flavour tagging

## Purpose and scope

v5 is a separate Stage-1 schema for studying whether Weaver jet-flavour scores
help reject selected `Z→ss` candidates while retaining the direct
`Λb→Λ⁰γ` signal. It starts from the v4 candidate selection and pointing fields.
The training configuration applies the current `E(Λb) ≥ 10.5 GeV` event gate
immediately after candidate building and before truth annotation, offline
candidate observables, and tagger inference. It retains all candidates in an
event that has at least one candidate passing that gate; Stage 2 applies the
candidate-level energy requirement as before. This saves downstream truth,
observable, tagger, and output work, but candidate pair building and vertex
fits still run before this event gate. No tag score is a selection requirement
in this iteration.

The first iteration uses
[`lb_reco_v5_training.json`](../config/lb_reco_v5_training.json): fitted Λ⁰
mass within ±12.5 MeV, current loose flight/displacement settings, and no raw
mass prefilter. The builder already rejects primary tracks and pairs failing
both-track d0 significance before the two-track vertex fit. A trial raw-mass
prefilter of ±0.15 GeV retained only 73/129 (56.6%) of the baseline candidates
passing the same Λ⁰ mass and energy requirements in the first 200 Physics
events, so it is **not** enabled. The paired trial files and exact config are
under `outputs/analysis/studies/flavour_tagging_v5_trial/`.

The tagger clusters all event `ReconstructedParticles` into two
exclusive-ee-kt jets. It stores event-level jet kinematics and model-score
vectors, alongside the candidate vectors. It does not yet remove the selected
candidate daughters before clustering. Offline, keep an event table keyed by
`event_entry` and associate each candidate to the nearest jet by direction;
compare the candidate-associated jet and the other jet separately. Treat this
association as diagnostic until daughter-removed reclustering is implemented.
For each model score the tuple carries the original per-jet score vector plus
candidate-aligned `lb_flavtag_v5_*_associated` and
`lb_flavtag_v5_*_otherjet_max` vectors. The alignment uses the candidate and
jet momentum directions and preserves one row per candidate during normal
flattening. A missing jet/score is encoded as `-1`.

The ROOT tuple and prepared candidate table carry five model classes (B, C, S,
Q, G), each with associated-jet and other-jet scores. The named BDT feature set
currently uses the B/C/S six-column subset; Q/G are retained for diagnostics.
See [the complete v5 FT variable dictionary](../docs/STAGE1_V5_FLAVTAG_VARIABLES.md)
for exact branch names and definitions.

Unlike the upstream Weaver example, v5 supplies the reconstructed primary
vertex from the existing Stage-1 vertex fit to the impact-parameter features.
This avoids using an MC-derived PV as a tagger input. The released model was
trained with the upstream feature definition, so the reconstructed-PV variant
is a deliberate domain change and its score calibration must be checked before
any rejection efficiency is quoted. Scores and feature vectors are diagnostics
only in v5 iteration 1.

The model files default to the Winter2023 `fccee_flavtagging_edm4hep_wc_v1`
files under `/eos/experiment/fcc/ee/jet_flavour_tagging/...`. Jobs require the
JSON preprocessing and ONNX files to be readable on workers. Override paths
with `LB_FLAVTAG_PREPROCESSING` and `LB_FLAVTAG_ONNX`; `LB_FLAVTAG_NJETS`
defaults to 2. The score branch names come from the model JSON and are stored
as event-level vectors. Truth flavour is not used as a model input or cut.

## Native Z-pole check

From the repository root, after sourcing the FCCAnalyses setup, confirm the
model files are readable and check one sample without submitting:

```bash
test -r /eos/experiment/fcc/ee/jet_flavour_tagging/winter2023/wc_pt_13_01_2022/fccee_flavtagging_edm4hep_wc_v1.json
test -r /eos/experiment/fcc/ee/jet_flavour_tagging/winter2023/wc_pt_13_01_2022/fccee_flavtagging_edm4hep_wc_v1.onnx
fccanalysis run analysis/studies/analysis_preselection_v5.py \
  --input-glob '/eos/experiment/fcc/ee/generation/DelphesEvents/winter2023/IDEA/p8_ee_Zss_ecm91/events_*.root' \
  --chunks 1200 --comp-group group_u_FCC.local_gen --queue workday --ncpus 4 \
  --output-eos '/eos/lhcb/lbdt3/user/rquaglia/fcc_ee/lblgamma/outputs/zss_full_condor/stage1_v5_flavtag' \
  --eos-type eoslhcb --check-only
```

The v5 command for a real dispatch is identical with `--check-only` removed;
it must use a fresh destination. Repeat with `p8_ee_Zbb_ecm91` and
`p8_ee_Zcc_ecm91`, each with its own output path. This handoff does not submit
jobs. The 1,000-event direct signal trial below is complete. On 2026-10-05,
check-only validated the mounted input globs for Zbb (4,398 files), Zcc
(5,018), and Zss (5,015), each with 1,200 planned chunks and the v5 training
config. Both model files were readable on the submit host. Check-only does not
prove model access inside dispatched workers or compile/run the full Condor
worker graph; no jobs were submitted.

## Bounded direct trial

The completed pilot used the command below (input copied locally from the
100k Physics signal file for stable access):

```bash
LB_RECO_ANALYSIS=analysis/studies/lb2lambda_gamma_reco_v5.py \
  scripts/run_reco_preselection.sh signal_physics \
  /tmp/Lb2LambdaGammaPhysics_nev100000_IDEA_edm4hep_v5.root \
  outputs/analysis/studies/flavour_tagging_v5_trial/signal_1000_stage1_v5_training.root \
  1000 config/lb_reco_v5_training.json 1
```

For new v5 runs, point the final ROOT output under `/tmp/rquaglia/...`; the
v5 module and runner write the FCCAnalyses intermediate ROOT file in that same
directory. This avoids staging large v5 tuples under the repository's
`outputs/` tree.

The run took 2:44, processed 1,000 input events, and produced 584
candidate-bearing events. Flattening produced 627 candidates, of which 572
were truth matched. In the shared offline region `E(Λb) ≥ 10.5 GeV` and fitted
`|m(Λ⁰)-mPDG| ≤ 12.5 MeV`, there are 612 candidates (572 matched). The raw
other-jet b score retains 88.5% of matched candidates at score ≥0.8, 80.1% at
≥0.95, and 40.7% at ≥0.99. These are signal-only diagnostic efficiencies;
there is no v5 Z→ss sample or measured background rejection yet. Do not apply
these thresholds as a selection based on this pilot.

The ten candidate-aligned v5 score columns are preserved by candidate
flattening; the six B/C/S features selected for training are listed in
[`lb_bdt_features_v5_flavtag.json`](../config/lb_bdt_features_v5_flavtag.json)
as `v5_offline_plus_flavtag`. Train only after producing equivalent v5 signal
and Zbb samples; then evaluate the frozen model on independent Zss and Zcc
samples. Compare at matched signal efficiency and keep direct matched signal,
wrong signal combinations, and inclusive backgrounds as separate categories.
The all-feature pilot Parquet is
`outputs/analysis/studies/flavour_tagging_v5_trial/signal_1000_v5_candidates_all_ft.parquet`.
The subsequent six-file Zbb/Zcc/Zss check and its limits are recorded in
[`STAGE1_V5_ZFLAVOUR_PILOT_2026-10-06.md`](../docs/STAGE1_V5_ZFLAVOUR_PILOT_2026-10-06.md).

## Native inclusive Z-pole campaign

Use [`scripts/run_stage1_v5_samples.sh`](../scripts/run_stage1_v5_samples.sh)
to check direct signal, PHSP, π⁰, and η inputs or run bounded (at most 1,000
event) pilots. For Zbb, Zcc, and Zss, its `--condor-check` mode checks the
native input globs and v5 worker configuration without submitting jobs. For
example:

```bash
scripts/run_stage1_v5_samples.sh --check signal_physics signal_phsp lbgamma_pi0 lbgamma_eta
scripts/run_stage1_v5_samples.sh --condor-check zbb zcc zss
scripts/run_stage1_v5_samples.sh --run --events 1000 signal_physics signal_phsp lbgamma_pi0 lbgamma_eta
```

Direct pilot outputs default to `/tmp/rquaglia/fccee_lblgamma_study/stage1_v5`;
set `V5_OUTPUT_BASE` to choose another temporary output directory. Full-file
direct processing is deliberately outside this bounded pilot driver.

The wrapper accepts the existing `p8_ee_Zbb_ecm91`, `p8_ee_Zcc_ecm91`, and
`p8_ee_Zss_ecm91` sample names through the base dispatcher. Run each with a
distinct v5 output destination. First check the mounted input glob and model
access on the submission/worker environment; use `--check-only` before any
submission. Do not reuse the running v4 destinations.

## First comparison

After equivalent v5 signal and Zbb/Zcc/Zss samples are available, freeze the
input catalogs and compare the v4 selection with no added tag cut. Plot score
vectors per jet flavour and per sample, then evaluate candidate-associated
versus other-jet scores after the full existing selection. Report per-event
and per-candidate denominators separately, with wrong signal combinations
separate from true direct candidates. Only then scan a simple discriminator
such as the other-jet b score and quote signal retention versus Zss rejection
with finite-sample uncertainties. Keep Zcc and Zbb in the comparison; a Zss
improvement alone does not establish a useful inclusive-background cut.

Each subsequent definition, jet multiplicity, daughter-removal choice, or
model/preprocessing version gets a new named v5 iteration and output path.

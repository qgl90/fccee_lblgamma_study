# Stage 2: offline selections, veto studies, and BDT datasets

The latest [three-flavour score reoptimization](v3_three_flavour_score_reoptimization.md)
scans the unchanged 1,091-chunk Zbb-trained BDT against physically weighted
Zbb+Zcc+Zss in the peak, with Armenteros and photon-veto alternatives. Its
validation-derived score remains a proposal and has a separate PHSP angular
acceptance and stacked mass/angle fit-view check.
The PI's corrected objective is S/√(S+Bbb+Bcc+Bss). It yields an
Armenteros-only validation point 0.985562; a separately scanned
Armenteros+reconstructed Λ-IP-significance≥5 alternative selects 0.981096.
The interim 0.991889 S/√B point is a superseded diagnostic.

For the frozen **v3** Physics versus available Zbb candidate reference and
normalized plots, see [`v3_reference_plots.md`](v3_reference_plots.md).
The earlier **1,028-chunk v3 XGBoost scan** and its PI decision evidence are
in [the Stage 2 review](../docs/STAGE2_V3_BDT_REVIEW_2026-10-03.md); the
frozen catalog, model, summaries, scan rows and plots are copied into
`docs/data/stage2_v3_bdt_1028/` and `docs/figures/stage2_v3_bdt_1028/`.
The separate fixed-score K⁰S ancestry and Armenteros study is in
[the PI review](../docs/STAGE2_V3_ARMENTEROS_REVIEW_2026-10-03.md) and
[its v3 how-to](v3_post_bdt_armenteros.md).
The 100k v3 PHSP angular acceptance through this frozen score, including the
fit response and figures, is in [its PI review](../docs/STAGE2_V3_PHSP_ANGLE_REVIEW_2026-10-04.md)
and [reproduction guide](v3_phsp_angle_acceptance.md).
The proposed post-BDT Armenteros veto has a separate [PHSP angular-response
review](../docs/STAGE2_V3_PHSP_ARMENTEROS_ANGLE_REVIEW_2026-10-04.md)
and [reproduction guide](v3_phsp_armenteros_acceptance.md).
The refreshed [1,091-chunk signal-peak scan](../docs/STAGE2_V3_BDT_PEAK_REVIEW_2026-10-04.md)
uses the same offline scenario with a newly trained model. Its proposed score
is a separate snapshot. Its matching [100k PHSP angular response](../docs/STAGE2_V3_PHSP_ANGLE_BDT1091_REVIEW_2026-10-04.md)
and [100k Λη/Λπ⁰ physics-background study](../docs/STAGE2_V3_PSEUDOSCALAR_BACKGROUNDS_2026-10-04.md)
have separate figure lists and [reproduction steps](v3_pseudoscalar_backgrounds_100k.md).
The earlier PHSP response belongs to the older 1,028-chunk score.
The historical v2 workflow starts below the v3 recipe.

## Current v3 recipe: Physics + inclusive Zbb → Stage 2 → scored Stage 2

The default in [`lb_offline_selections.json`](../config/lb_offline_selections.json)
is `lambda12p5_lbE10p5_same_hemi_all`. It keeps reconstructed candidates with
`4.7 ≤ m(Λγ) ≤ 6.5 GeV`, `|m(pπ)−1.115683 GeV| ≤ 0.0125 GeV`, and
`E(Λb) ≥ 10.5 GeV`. It applies **no π⁰, η, or minimum diphoton-mass veto**.
The candidate photon is paired with other raw type-22 photons on the fitted
Λ⁰ hemisphere, and the nearest π⁰/η mass distances and minimum pair mass
become optional BDT inputs. Empty partner lists are retained; their distance
columns are `+inf` in the candidate table and treated as missing by XGBoost.
The [selection review](../docs/STAGE1_V3_MASS_ENERGY_NO_VETO_REVIEW_2026-10-02.md)
records the 191-chunk comparison and event/candidate denominators.

Use the exact v3 Physics Stage 1 ROOT tuple and a frozen catalog of valid v3
Zbb Condor ROOT chunks. The 191-chunk catalog used for the presentation is a
historical snapshot; refresh the catalog as Condor outputs arrive. Give each
catalog and model a new snapshot label, while keeping **the same `PREP`
directory**. `--resume` verifies and reuses complete previously prepared
candidate pairs, processes only the new chunk IDs, and rebuilds the combined
cutflow with the enlarged processed-event denominator. It refuses changed
selection/configuration, preparation code, input path, source size or a catalog
that drops/replaces a previously prepared chunk. From the repository root:

```bash
cd /afs/cern.ch/work/r/rquaglia/fcc_ee/fccee_lblgamma_study
PY="$PWD/myenv/bin/python"
SIGNAL=/eos/lhcb/lbdt3/user/rquaglia/fcc_ee/lblgamma/outputs/stage1_v3_my_run/signal_physics.root
JOB_DIR="$PWD/external/FCCAnalyses/BatchOutputs/2026-10-02_07-46-37/p8_ee_Zbb_ecm91"
ROOT_DIR=/eos/lhcb/lbdt3/user/rquaglia/fcc_ee/lblgamma/outputs/zbb_full_condor/native_batch_3d_activity_v3/p8_ee_Zbb_ecm91
RUN=/eos/lhcb/lbdt3/user/rquaglia/fcc_ee/lblgamma/outputs/stage2_v3_incremental
SNAPSHOT=next_v3_snapshot  # use a new name for each later catalog refresh
ZBB_CATALOG="$RUN/catalogs/$SNAPSHOT.json"
PREP="$RUN/prepared"
MODEL="$RUN/models/$SNAPSHOT"
PROJECTION="$RUN/projections/$SNAPSHOT"
FINAL="$RUN/fixed_cut_tables/$SNAPSHOT"

# This existing v3 Physics tuple predates the new `_stage1_v3.root` basename
# convention. Keep its exact path while resuming the prepared candidate set.

env -u PYTHONPATH -u PYTHONHOME "$PY" \
  studies/reconstruction/catalog_condor_zbb_chunks.py \
  --job-dir "$JOB_DIR" --root-dir "$ROOT_DIR" --output "$ZBB_CATALOG"

env -u PYTHONPATH -u PYTHONHOME "$PY" \
  studies/reconstruction/prepare_offline_bdt.py \
  --signal "$SIGNAL" --zbb-catalog "$ZBB_CATALOG" \
  --config config/lb_offline_selections.json \
  --stage1-config config/lb_reco_preselection_15mev_45_65_3d.json \
  --scenario lambda12p5_lbE10p5_same_hemi_all \
  --output-dir "$PREP" --resume

env -u PYTHONPATH -u PYTHONHOME "$PY" \
  studies/reconstruction/train_offline_bdt.py \
  --prepared-dir "$PREP" --output-dir "$MODEL" \
  --feature-config config/lb_bdt_features.json \
  --feature-set v3_offline_no_veto_proposal \
  --io-workers 8 --threads 16

env -u PYTHONPATH -u PYTHONHOME "$PY" \
  studies/reconstruction/inspect_v3_bdt_response.py \
  --prepared-dir "$PREP" --model-dir "$MODEL" \
  --output-dir "$MODEL/response_checks"
```

The first `--resume` run creates `PREP/preparation_identity.json` and prepares
every valid chunk in that snapshot. For a later refresh, change `SNAPSHOT`,
rerun the catalog command, and repeat the preparation and training commands
with the **same `RUN` and `PREP`**. Keep each catalog JSON immutable once a
training uses it. Complete old Parquets stay in `PREP`; the new `summary.json`
lists all included chunk IDs and their counters. The trainer assigns entire
Zbb chunks by `chunk_id % 10` and Physics candidates by generated event key,
so appending chunks cannot move an old source between train, validation and
test. Its default uses **all** Zbb candidates in training chunks; the optional
`--max-train-background N` is only for a named development study. All selected
candidate shards, including validation/test chunks, receive a score. Never
reuse an old trained model as if it had been trained on a refreshed catalog.
For a large incremental refresh, `make_incremental_catalog.py` isolates the
new valid chunks; `run_v3_parallel_preparation.py --workers 8` prepares that
subset in independent partitions, and `consolidate_prepared_shards.py` copies
verified pairs into `PREP`. Rerun the full `--resume` preparation afterward
to rebuild and validate its combined cutflow. The trainer uses eight Parquet
readers and sixteen XGBoost threads on the current 40-CPU host; it records
the settings and CPU affinity in `training_summary.json`.
The all-candidate audit can occupy many GB; use a durable location with enough
space for `RUN` (the command uses EOS) rather than the nearly full AFS work
volume. A scratch run is valid for speed only after copying its complete
`PREP`, model, catalog and manifests to durable storage before the scratch is
cleared. Do not run two preparations against the same `PREP` concurrently.

The pre-training cuts are exactly the named JSON scenario above. The `fit`
stage applies `4.7 <= lb_mass <= 6.5` GeV, the `lambda` stage adds the
`12.5` MeV reconstructed mass half-window, and `selected` adds
`lb_E >= 10.5` GeV. This default has no photon veto; `d_pi0`, `d_eta`, and
`min_pair` use other raw type-22 photons on the fitted Lambda hemisphere and
are kept as features. The diagnostic `pass_pi0`, `pass_eta`, and
`pass_low_mass` flags do not filter the default. Edit the JSON under a **new
scenario name** for another selection and use a new `PREP` directory; the
identity guard will prevent mixing it with the current candidate tables.

`PREP/*_selected.parquet` is **Stage 2 before BDT**: one row per candidate
passing the offline cuts, with all prepared candidate columns. The matching
`*_audit.parquet` retains rejected Stage 1 candidates and pass flags.
`MODEL/scored_selected/*_selected.parquet` is **Stage 2 with BDT response**:
the same selected rows and columns, plus `bdt_score`, with **no score cut yet**.
These per-source Parquets are directly usable for flexible downstream plots and
alternative score cuts. `summary.json` and `training_summary.json` record
inputs, configuration hashes, exact feature order, splits, counts, and model
details. The trainer writes held-out feature distributions, feature importance,
ROC, held-out score, and train-versus-test score plots. The model directory
also freezes `prepared_manifest.json`, the exact preparation summary used to
train it; the single-file scoring command can therefore use that model after
the shared `PREP` directory receives later catalog chunks. The additional
`response_checks/` figures compare held-out direct Physics, wrong Physics
combinations and nonmatched Zbb scores, then show mass and helicity-angle
shapes at fixed illustrative scores of 0.5 and 0.9. Those fixed numbers are
diagnostics, not a working-point optimization. The proposed feature list is explained in the
[v3 feature review](../docs/STAGE2_V3_FEATURE_PROPOSAL_2026-10-02.md).
Train/validation/test splitting keeps Physics events together and whole Zbb
chunks together. Truth matching labels signal and background for training;
neither truth nor `lb_mass` or `cos_theta_p` is a model feature.

To maximize central `S/sqrt(S+B)` on validation data with **both** yields
inside a named reconstructed signal-peak mass window, at least 20 observed
validation-background candidates in that window, and a projected 95% upper
background count of at most one million in that window, evaluate that fixed score
on the independent test split and make a compact post-cut tuple:

```bash
env -u PYTHONPATH -u PYTHONHOME "$PY" \
  studies/reconstruction/project_offline_bdt.py \
  --prepared-dir "$PREP" --model-dir "$MODEL" \
  --signal-mass-window 5.4 5.9 \
  --max-expected-background 1000000 --min-significance 10 \
  --output-dir "$PROJECTION"

env -u PYTHONPATH -u PYTHONHOME "$PY" \
  studies/reconstruction/assemble_stage2_output.py \
  --prepared-dir "$PREP" --scored-dir "$MODEL/scored_selected" \
  --projection "$PROJECTION/projection.json" \
  --output-dir "$FINAL"
```

`projection.json` also reports the best validation point satisfying the
95% upper-background target as `background_target_validation_choice`, plus
the unconstrained significance optimum separately. The main
`validation_choice` is the constrained point. The scan includes a dense
near-one score grid and the observed validation-background order statistics.
`working_point_scan.png`, `working_point_tail.png`, and
`working_point_purity.png` show yield, significance, and purity, including
the 95% background upper edge.
For a PI-specified expected-purity requirement, add
`--min-expected-purity FRACTION`; this uses `S/(S+B_95% upper)` in the
specified signal-peak window. The 5.4–5.9 GeV bounds are provisional until
the PI confirms the fit window. A sparse or zero-background tail is not treated
as a measured optimum. If no point has enough MC support and satisfies the
constraints, no cut is frozen.

`FINAL/signal_offline.parquet` and `FINAL/zbb_offline.parquet` are compact
**Stage 2** tables; `FINAL/signal_bdt.parquet` and `FINAL/zbb_bdt.parquet`
are **Stage 2 after the validation-fixed BDT cut**. All four preserve every
prepared per-candidate column, including charged/neutral/all activity,
charged-cone d0 extrema, same-hemisphere photon-pair lists, truth ancestry,
event/candidate keys, and `bdt_score`; the offline files also contain
`pass_bdt`. The manifest records source shards, processed-event denominators,
counts, and the score cut. The uncut scored shards remain available even if
no reliable working point satisfies the requested background limit. In that
case `projection.json` has `validation_choice: null` and the assembly command
intentionally stops; inspect `working_point_scan.png`, expand the Zbb catalog,
or define a separately named exploratory score scenario before claiming a
post-cut dataset. No BDT retraining is needed to revisit a score cut.

### Preserve every flattenable Stage 1 candidate branch

The fast Stage 2 preparation retains all new v3 activity/recoil branches and
the reconstructed variables used by the model, but its 430-column schema is
curated. For a broad diagnostic table with **every flattened Stage 1
candidate branch and alias**, flatten the same ROOT shards once and join the
scored audit by `(source_id, event_entry, candidate_slot)`. Run this after a
validation-fixed score exists:

```bash
mkdir -p "$RUN/flat"
env -u PYTHONPATH -u PYTHONHOME "$PY" \
  studies/reconstruction/flatten_candidates.py \
  --input "$SIGNAL" --mode gamma --source-id -1 \
  --output "$RUN/flat/signal_-1.parquet"

jq -r '.chunks[] | [.chunk_id, .root] | @tsv' "$ZBB_CATALOG" |
while IFS=$'\t' read -r CHUNK_ID ROOT_FILE; do
  env -u PYTHONPATH -u PYTHONHOME "$PY" \
    studies/reconstruction/flatten_candidates.py \
    --input "$ROOT_FILE" --mode zbb --source-id "$CHUNK_ID" \
    --output "$RUN/flat/zbb_${CHUNK_ID}.parquet"
done

env -u PYTHONPATH -u PYTHONHOME "$PY" \
  studies/reconstruction/apply_offline_bdt.py \
  --input-dir "$PREP" --model-dir "$MODEL" --table audit \
  --output-dir "$RUN/scored_audit"

env -u PYTHONPATH -u PYTHONHOME "$PY" \
  studies/reconstruction/materialize_stage2_candidates.py \
  --flat-dir "$RUN/flat" --prepared-dir "$PREP" \
  --scored-audit-dir "$RUN/scored_audit" \
  --projection "$PROJECTION/projection.json" \
  --output-dir "$RUN/full_branch_stage2"
```

`full_branch_stage2/audit/` retains every candidate, including those failing
offline cuts. `offline_selected/` is the full-branch Stage 2 dataset and
`bdt_selected/` applies the fixed score. All three also carry Stage 2 pass
flags, the score, the derived isolation ratios, `lb_thrust_abs_cos`, and
reconstructed `arm_alpha` and `arm_qt_gev` from the fitted daughter momenta.
The Armenteros columns support a later K_S⁰ misidentification comparison;
they do not add a cut to this reference selection or enter the proposed BDT.
The join rejects missing or repeated candidate keys. These full-branch
Parquets cost more disk and I/O than the compact prepared/scored shards.

For any later ROOT file made with the same one-photon Stage 1 v3 schema and
reconstruction scenario, apply the frozen model without training again:

```bash
env -u PYTHONPATH -u PYTHONHOME "$PY" \
  studies/reconstruction/score_stage1_v3_dataset.py \
  --input /path/to/stage1.root --sample my_sample --source-id 0 \
  --model-dir "$MODEL" --projection "$PROJECTION/projection.json" \
  --output-dir "$RUN/applied/my_sample_0"
```

Omit `--projection` if no validation-fixed score cut exists yet. The command
always writes `audit/` and `offline_selected/` with the full flattened Stage 1
candidate fields, offline pass flags, and `bdt_score`; with a fixed projection
it also writes `bdt_selected/`. Each row keeps `source_id`, `event_entry`,
`candidate_slot`, and `candidates_in_event`. Use a distinct `source-id` and
output directory per file. It records the input, model, config hash, processed
event counter, and counts in `manifest.json`. `--max-output-events 1000` is a
development check on candidate-bearing Stage 1 output events; its manifest
cannot supply a complete processed-event denominator. The flattener now
copies newly added `lb_*` candidate branches and `lambda_*` slot branches
automatically; Lambda-slot fields that collide with candidate aliases get a
`lambda_slot_*` name. The output also has `arm_alpha` and `arm_qt_gev` for
later misidentification plots; no Armenteros veto is applied by this command.

For a bounded schema check before a full campaign, add
`--max-zbb-chunks 1 --max-output-events 1000` to the preparation command and
use a **distinct pilot output directory**. Capped output is only for code
validation: it has no processed-input-event denominator, and the trainer
rejects it for yield projection. The validated pilot at
`outputs/analysis/studies/v3_offline_inspection_20261002/pilot_default_v3_1000_final/`
selected 1,021 Physics and 203 Zbb candidates; all 20 proposed feature
columns were present. Its selected Physics and Zbb candidate keys matched the
corresponding full-sample study rows exactly. The pilot retained 44 Physics
and 108 Zbb candidates that failed the diagnostic π⁰ window, confirming
that no photon veto entered the offline cut.
The full-branch join was also checked on 1,000 Physics Stage 1 output events:
1,070 candidate keys matched exactly, and the joined table retained the
flattened Stage 1 columns plus Stage 2 ratios, thrust alignment, and pass
flags. A placeholder score was used only to exercise the join; no BDT was
trained in that capped validation.

## Historical v2 recipe and optional veto studies

Start from the Stage 1 ROOT tuples described in [stage1.md](stage1.md).
This guide uses the v2 Physics and Zbb tuples as the signal and inclusive
background inputs. PHSP is an acceptance cross-check; Λb→Λη reconstructed
as one photon is the forced feed-down study. Neither is included silently
in the BDT training or the inclusive Zbb yield.

## Inputs, cuts, and output contract

[`config/lb_offline_selections.json`](../config/lb_offline_selections.json)
names the offline scenarios. All start inside 4.7–6.5 GeV in m(Λγ).
`lambda5_same_hemi_all` applies only `|m(pπ)−1.115683|≤0.005 GeV` and
computes veto metrics from **other raw type-22 photons on the reconstructed
Λ⁰ hemisphere**. `lambda5_pi0_same_hemi_all` also vetoes any partner with
`|m(γγ)−m(π⁰)|≤20 MeV`;
`lambda5_pi0_eta_same_hemi_all` additionally vetoes the ±50 MeV η window.
`lambda5_lowmass1_same_hemi_all` requires every saved partner mass to be
at least 1 GeV. An empty partner list passes every photon veto. The
`same_hemi_selected` variants instead use other selected `Photon#0`
photons. These are distinct partner definitions and need separate
preparations. The historical `lambda5_pi0` scenario used all raw photons
in both hemispheres; do not mix its result with a v2 same-hemisphere study.
Additional reconstructed scalar cuts can be added as named `reco_cuts` in
the JSON scenario, with a saved column and a `min` and/or `max` bound.
This includes v2 isolation fields such as `iso_R05_all_energy` and
`iso_R05_charged_p`, and center-of-mass closure fields such as
`z_partial_deltaE` and `z_full_deltaP`. Compare any proposed bound to the unchanged scenario
on the same audit before adopting it.

[`prepare_offline_bdt.py`](../studies/reconstruction/prepare_offline_bdt.py)
reads the jagged ROOT branches in bounded blocks, applies reconstructed
cuts before forming candidate rows, and writes both `*_audit.parquet`
(**all** Stage 1 candidates with pass flags) and `*_selected.parquet`
(passing candidates). Rows carry `source_id`, `event_entry`,
`candidate_slot`, and `candidates_in_event`. Truth is retained for
evaluation; it is not an offline or BDT input cut. The v2 preparation now
propagates **all 163 branches added to the v2 ROOT schema**, including
charged/neutral/all isolation energy, momentum components, vector-sum
magnitude, multiplicity, d0 ranges for all six cone sizes, 3D flight,
recoil, thrust, Armenteros, and the complete photon-pair mass/index lists.
The scored Parquets keep these columns and append `bdt_score`.
On new Stage 1 inputs they also retain each candidate proton, pion, and
photon's matched MC identity and four-generation first-parent chain in
`{proton,pion,photon}_mc_{parent,grandparent,greatgrandparent,greatgreatgrandparent}_{index,pdg}`
columns. These are audit labels only; they are not selection or BDT features.
When an older Stage 1 input lacks a generation, its index is `-1` and PDG is
`0` in the prepared table.
The preparation also copies photon-centered `iso_RXX_*` and Λ⁰-centered
`lambda0_iso_RXX_*` activity columns when present. New Stage 1 files use
`R20` as their widest radius; older files may instead contain `R70`.

Keep each study in a unique output directory. In the commands below,
replace `ZBB_CATALOG` with the completed **v2** Zbb catalog produced by
[stage1.md](stage1.md#check-outputs-and-event-denominators):

```bash
cd /afs/cern.ch/work/r/rquaglia/fcc_ee/fccee_lblgamma_study
PY="$PWD/myenv/bin/python"
RUN_TAG=stage2_v2_my_run
SESSION="$PWD/outputs/analysis/studies/$RUN_TAG"
mkdir -p "$SESSION"
SOURCE_DIR=/eos/lhcb/lbdt3/user/rquaglia/fcc_ee/lblgamma/outputs
SIGNAL="$SOURCE_DIR/nominal_preselection_100k_signal_physics_reco_v2.root"
ETA="$SOURCE_DIR/nominal_preselection_100k_lbgamma_eta_reco_v2.root"
ZBB_CATALOG=/path/to/completed/zbb_catalog_v2.json
```

The catalog must have all intended chunks valid, no missing/invalid chunks,
and a consistent ROOT schema. Its summed `events_processed` counts, together
with the Physics ROOT `eventsProcessed=100000`, are the input-event
denominators. Candidate-bearing events, all candidates, truth-matched
signal, and nonmatched Zbb candidates remain separate counts.

## Prepare and compare photon-veto scenarios

Prepare the no-veto ±5 MeV reference once from ROOT, retaining the full
candidate audit. The explicit Stage 1 config records that these are v2
tuples:

```bash
env -u PYTHONPATH -u PYTHONHOME "$PY" \
  studies/reconstruction/prepare_offline_bdt.py \
  --signal "$SIGNAL" --zbb-catalog "$ZBB_CATALOG" \
  --config config/lb_offline_selections.json \
  --stage1-config config/lb_reco_preselection_15mev_45_65_3d.json \
  --scenario lambda5_same_hemi_all \
  --output-dir "$SESSION/lambda5_same_hemi_all"

env -u PYTHONPATH -u PYTHONHOME "$PY" \
  studies/reconstruction/compare_offline_scenarios.py \
  --prepared-dir "$SESSION/lambda5_same_hemi_all" \
  --output-dir "$SESSION/veto_comparison_same_hemi_all"
```

The preparation writes `summary.json`, `lambda_mass.png`,
`lambda_window_scan.png`, and `selected_multiplicity.png`. The comparison
writes `scenario_counts.json`, `scenario_retention.png`, and the π⁰/η/
minimum-pair-mass distributions, separating direct Physics signal, wrong
Physics combinations, nonmatched Zbb, and genuine direct decays in Zbb.

Derive named cuts from **that same all-candidate audit**, without rereading
ROOT. Each derivative keeps the full audit and all candidate columns:

```bash
for SCENARIO in lambda5_pi0_same_hemi_all \
                lambda5_pi0_eta_same_hemi_all \
                lambda5_lowmass1_same_hemi_all; do
  env -u PYTHONPATH -u PYTHONHOME "$PY" \
    studies/reconstruction/derive_offline_scenario.py \
    --parent-dir "$SESSION/lambda5_same_hemi_all" \
    --config config/lb_offline_selections.json \
    --scenario "$SCENARIO" --output-dir "$SESSION/$SCENARIO"
done
```

To evaluate selected `Photon#0` partners on the same hemisphere, run a
second ROOT preparation with `--scenario lambda5_same_hemi_selected`, then
derive its `lambda5_pi0_same_hemi_selected`,
`lambda5_pi0_eta_same_hemi_selected`, and
`lambda5_lowmass1_same_hemi_selected` variants. The derivative rejects a
change of partner definition, so this separate preparation is required.

For the forced η feed-down comparison, flatten the **v2** Physics and η
ROOT files, then run the partner-list study. This reports no-partner
candidates explicitly. With the prepared Zbb audit above, it also includes
the Zbb same-hemisphere raw-photon counts. Forced η retention is a shape
and veto study, not a physical Zbb normalization.

```bash
mkdir -p "$SESSION/full_candidates"
env -u PYTHONPATH -u PYTHONHOME "$PY" \
  studies/reconstruction/flatten_candidates.py \
  --input "$SIGNAL" --output "$SESSION/full_candidates/signal_-1.parquet" \
  --mode gamma --source-id -1
env -u PYTHONPATH -u PYTHONHOME "$PY" \
  studies/reconstruction/flatten_candidates.py \
  --input "$ETA" --output "$SESSION/full_candidates/eta_-2.parquet" \
  --mode gamma --source-id -2
env -u PYTHONPATH -u PYTHONHOME "$PY" \
  studies/reconstruction/study_feeddown_veto.py \
  --signal "$SESSION/full_candidates/signal_-1.parquet" \
  --eta "$SESSION/full_candidates/eta_-2.parquet" \
  --zbb-audit-dir "$SESSION/lambda5_same_hemi_all" \
  --output-dir "$SESSION/feeddown_veto"
```

## Train, inspect, and freeze a BDT

The following example trains on the **π⁰-preselected, same-hemisphere
raw-photon** scenario. The explicit `v2_3d` feature set uses momentum
magnitudes and energies, 3D flight significance, same-hemisphere isolation,
thrust, and recoil. It excludes pT, Rxy-only quantities, mass, helicity
angle, truth, ancestry, and candidate multiplicity. Named feature sets live
in [`config/lb_bdt_features.json`](../config/lb_bdt_features.json); copy and
edit this JSON to try another ordered set of saved scalar columns, then pass
the copy with `--feature-config` and its name with `--feature-set`. The
trainer rejects truth, identity, mass/angle target, and cut-flag fields as
inputs. The exact ordered list and config hash are saved in
`training_summary.json`; see
[`train_offline_bdt.py`](../studies/reconstruction/train_offline_bdt.py).
This is a new model specification to review alongside the older `full` and
`topology` feature sets, not a replacement of their historical results.

```bash
PREP="$SESSION/lambda5_pi0_same_hemi_all"
MODEL="$SESSION/bdt_v2_3d_pi0_same_hemi_all"
PROJECTION="$SESSION/projection_v2_3d_pi0_same_hemi_all"

env -u PYTHONPATH -u PYTHONHOME "$PY" \
  studies/reconstruction/train_offline_bdt.py \
  --prepared-dir "$PREP" --output-dir "$MODEL" \
  --feature-config config/lb_bdt_features.json --feature-set v2_3d

env -u PYTHONPATH -u PYTHONHOME "$PY" \
  studies/reconstruction/project_offline_bdt.py \
  --prepared-dir "$PREP" --model-dir "$MODEL" \
  --output-dir "$PROJECTION"

env -u PYTHONPATH -u PYTHONHOME "$PY" \
  studies/reconstruction/plot_full_sample_projection.py \
  --prepared-dir "$PREP" --model-dir "$MODEL" \
  --projection-dir "$PROJECTION" \
  --output-dir "$SESSION/full_sample_overlay"
```

Training splits Physics by generated event and Zbb by whole catalog chunk.
It trains on truth-matched Physics versus nonmatched Zbb, keeps other
combinations for diagnostics, and writes ROC, score, feature-distribution,
and importance plots. `project_offline_bdt.py` scans validation scores,
freezes a cut subject to the configured expected-background ceiling and
minimum significance, then evaluates it on independent test partitions.
The weighted yield uses `S = (6×10¹²)(0.15)(2)(0.10)(7.1×10⁻⁶)(0.639)
× N_truth_matched/N_generated` and
`B = (6×10¹²)(0.15) × N_nonmatched_Zbb/N_processed_Zbb`.
`projection.json` records the fixed cut, denominators, raw counts, scaled
yields, and Poisson interval; `working_point_scan.png` and
`expected_mass_and_angle.png` show the scan and expected mass/angle shapes.
The independent test projection is the performance check; the all-sample
overlay includes training events and is a presentation view.

## Default compact Stage 2 output

The training command automatically scores every **offline-selected** shard.
Assemble one Parquet per sample for the pre-BDT offline selection and one
per sample after the fixed BDT cut:

```bash
env -u PYTHONPATH -u PYTHONHOME "$PY" \
  studies/reconstruction/assemble_stage2_output.py \
  --prepared-dir "$PREP" --scored-dir "$MODEL/scored_selected" \
  --projection "$PROJECTION/projection.json" \
  --output-dir "$SESSION/stage2_compact"
```

`stage2_compact/` contains `signal_offline.parquet`, `zbb_offline.parquet`,
`signal_bdt.parquet`, and `zbb_bdt.parquet`, plus `manifest.json`. Each row
is one candidate. The offline files retain **all columns in the scored
selected shards**, including all v2 isolation and center-of-mass/recoil
observables, the same-hemisphere photon-pair lists, the truth-match label,
event/candidate keys, offline pass flags, and
`bdt_score`. They also add `pass_bdt`; the BDT files contain rows where it
is true. The manifest records source paths, the fixed validation score,
input-event denominators, and candidate counts. This is the normal Stage 2
dataset for subsequent selections and plots. The output is compact relative
to Stage 1 because only candidates passing the named pre-BDT selection are
included; the original audit Parquets retain failed candidates.
The Zbb files retain rare truth-matched Λb→Λγ candidates as diagnostic
rows; the background expectation in `projection.json` counts only
nonmatched Zbb candidates.

To use a different pre-BDT selection, prepare or derive another named
scenario, train a separate model on its selected rows, freeze its own score
cut, and assemble its compact output in a distinct directory. The
feature-list JSON can change independently of the offline-selection JSON.

## Optional all-candidate scoring and full-branch join

To score the prepared audit later with the same frozen model, without
retraining:

```bash
env -u PYTHONPATH -u PYTHONHOME "$PY" \
  studies/reconstruction/apply_offline_bdt.py \
  --input-dir "$PREP" --model-dir "$MODEL" --table audit \
  --output-dir "$SESSION/scored_audit"
```

`scored_audit/*_audit.parquet` retains failed offline candidates as well as
passing ones, every propagated v2 isolation and photon-pair column, the
offline flags, and `bdt_score`. `MODEL/scored_selected/*_selected.parquet`
is the corresponding scored offline-selected table.

Verify the full set of newly added v2 branches in the audit, selected, and
scored schemas. The check compares the old and v2 Physics ROOT branch names
and fails if any new name is absent from a downstream table:

```bash
env -u PYTHONPATH -u PYTHONHOME "$PY" \
  studies/reconstruction/verify_stage2_columns.py \
  --baseline-root "$SOURCE_DIR/nominal_preselection_100k_signal_physics_reco.root" \
  --v2-root "$SIGNAL" \
  --audit "$PREP/signal_-1_audit.parquet" \
  --selected "$PREP/signal_-1_selected.parquet" \
  --scored "$MODEL/scored_selected/signal_-1_selected.parquet" \
  --final-offline "$SESSION/stage2_compact/signal_offline.parquet" \
  --final-bdt "$SESSION/stage2_compact/signal_bdt.parquet" \
  --output "$SESSION/v2_column_propagation.json"
```

The prepared tables contain every *new v2* branch but only a selected set
of older Stage 1 fields. For a diagnostic table retaining the broad flat Stage 1
candidate/ancestry schema and the full photon-pair lists, flatten each
catalogued Zbb chunk. The Physics flat table was made above:

```bash
jq -r '.chunks[] | [.chunk_id, .root] | @tsv' "$ZBB_CATALOG" |
while IFS=$'\t' read -r CHUNK_ID ROOT_FILE; do
  env -u PYTHONPATH -u PYTHONHOME "$PY" \
    studies/reconstruction/flatten_candidates.py \
    --input "$ROOT_FILE" \
    --output "$SESSION/full_candidates/zbb_${CHUNK_ID}.parquet" \
    --mode zbb --source-id "$CHUNK_ID"
done
```

Join those full candidate rows to the scored audit by the exact
`(source_id,event_entry,candidate_slot)` key. The materializer rejects
missing or duplicate joins, keeps every flat candidate column, adds offline
flags and `bdt_score`, and writes three per-shard datasets: `audit/`
(all Stage 1 candidates), `offline_selected/`, and `bdt_selected/`.
The last uses the **validation-fixed** score in `projection.json`.

```bash
env -u PYTHONPATH -u PYTHONHOME "$PY" \
  studies/reconstruction/materialize_stage2_candidates.py \
  --flat-dir "$SESSION/full_candidates" \
  --prepared-dir "$PREP" \
  --scored-audit-dir "$SESSION/scored_audit" \
  --projection "$PROJECTION/projection.json" \
  --output-dir "$SESSION/final_candidates"
```

`final_candidates/manifest.json` records the source files, fixed score,
and candidate counts at each step. The original Stage 1 ROOT files remain
the authoritative event-level source, including events with no selected
candidate. Do not infer input-event efficiency from the number of final
candidate rows.

## Historical optional fixed-model checks: η, K⁰S, and Armenteros

The commands in this section concern an older π⁰-veto scenario. For the
current no-photon-veto v3 model, use
[the 1,028-chunk Armenteros recipe](v3_post_bdt_armenteros.md).

After training, [`evaluate_post_bdt_veto.py`](../studies/reconstruction/evaluate_post_bdt_veto.py)
holds the model and score cut fixed and compares π⁰ only, π⁰+η, and
minimum m(γγ)≥1 GeV using the same prepared partner definition:

```bash
env -u PYTHONPATH -u PYTHONHOME "$PY" \
  studies/reconstruction/evaluate_post_bdt_veto.py \
  --prepared-dir "$PREP" --model-dir "$MODEL" \
  --projection-dir "$PROJECTION" \
  --output-dir "$SESSION/post_bdt_photon_veto"
```

[`study_post_bdt_kshort_veto.py`](../studies/reconstruction/study_post_bdt_kshort_veto.py)
reassigns the fitted proton-track momentum the pion mass and scans windows
around m(K⁰S). [`armenteros.py`](../studies/reconstruction/armenteros.py)
provides α and qT; [`study_armenteros_veto.py`](../studies/reconstruction/study_armenteros_veto.py)
plots an illustrative reconstructed K⁰S-like box before and after BDT.
Both studies need the scored Zbb truth-audit table for *diagnostic labels*.
Generate it only after fixing the BDT cut:

```bash
env -u PYTHONPATH -u PYTHONHOME "$PY" \
  studies/reconstruction/classify_post_bdt_zbb_truth.py \
  --prepared-dir "$PREP" --model-dir "$MODEL" \
  --projection-dir "$PROJECTION" --output-dir "$SESSION/zbb_truth"
env -u PYTHONPATH -u PYTHONHOME "$PY" \
  studies/reconstruction/summarize_post_bdt_zbb_ancestry.py \
  --rows "$SESSION/zbb_truth/post_bdt_zbb_truth_rows.parquet" \
  --output-dir "$SESSION/zbb_truth"
env -u PYTHONPATH -u PYTHONHOME "$PY" \
  studies/reconstruction/attach_post_bdt_zbb_truth.py \
  --truth-rows "$SESSION/zbb_truth/post_bdt_zbb_truth_detailed.parquet" \
  --scored-dir "$MODEL/scored_selected" \
  --projection "$PROJECTION/projection.json" \
  --output-dir "$SESSION/zbb_truth"

env -u PYTHONPATH -u PYTHONHOME "$PY" \
  studies/reconstruction/study_post_bdt_kshort_veto.py \
  --prepared-dir "$PREP" --model-dir "$MODEL" \
  --projection-dir "$PROJECTION" \
  --zbb-with-truth "$SESSION/zbb_truth/post_bdt_zbb_candidates_with_truth.parquet" \
  --output-dir "$SESSION/kshort_veto_study"
```

For Armenteros on this new scenario, copy
[`config/lb_armenteros_study.json`](../config/lb_armenteros_study.json)
to the session directory and set its `input_offline_scenario` to
`lambda5_pi0_same_hemi_all`, then run:

```bash
env -u PYTHONPATH -u PYTHONHOME "$PY" - \
  config/lb_armenteros_study.json "$SESSION/armenteros_v2.json" <<'PYCODE'
import json, sys
with open(sys.argv[1]) as source:
    config = json.load(source)
config['input_offline_scenario'] = 'lambda5_pi0_same_hemi_all'
with open(sys.argv[2], 'w') as output:
    json.dump(config, output, indent=2)
    output.write('\n')
PYCODE
env -u PYTHONPATH -u PYTHONHOME "$PY" \
  studies/reconstruction/study_armenteros_veto.py \
  --prepared-dir "$PREP" --model-dir "$MODEL" \
  --projection-dir "$PROJECTION" \
  --zbb-with-truth "$SESSION/zbb_truth/post_bdt_zbb_candidates_with_truth.parquet" \
  --config "$SESSION/armenteros_v2.json" \
  --output-dir "$SESSION/armenteros_study"
```

These K⁰S and Armenteros boxes are exploratory. Their plots and JSONs
report signal loss, Zbb reduction, candidate/event counts, and fixed-score
expectations; they do not silently change the training selection. A change
to the pre-BDT reference belongs in a new named JSON scenario and a new
training/output directory.

## Current v3 light-flavour and veto extension

For the frozen 1,091-chunk score, use
[`v3_zcc_zss_full_processing.md`](v3_zcc_zss_full_processing.md) to reproduce
the full 1,200-chunk Zcc and Zss preparation and scoring. Then use
[`v3_post_bdt_veto_sequence.md`](v3_post_bdt_veto_sequence.md) to make the
physically weighted, linear mass and cos θp plots for the BDT, Armenteros,
π⁰ veto and η veto stages. The [PI review](../docs/STAGE2_V3_ZCC_ZSS_AND_VETO_REVIEW_2026-10-04.md)
lists the frozen counts, branching assumptions, figures and limitations.
For the full Zss post-BDT truth composition and paired K⁰S rejection check,
use [`v3_zss_ancestry_armenteros.md`](v3_zss_ancestry_armenteros.md).
For the paired reconstructed Λ displacement scan on the same scored rows,
use [`v3_displacement_zss.md`](v3_displacement_zss.md); its
[review](../docs/STAGE2_V3_DISPLACEMENT_ZSS_2026-10-04.md) records the
conditional signal and background losses and frozen figures.
For the three-flavour feature distributions that precede a mixed-background
BDT training decision, use
[`v3_flavour_feature_comparison.md`](v3_flavour_feature_comparison.md)
and its [PI review](../docs/STAGE2_V3_FLAVOUR_FEATURES_2026-10-04.md).

## Photon pointing input audit

The completed [200-event calorimeter geometry audit](v3_photon_pointing_geometry.md)
provides a 2,250 mm barrel radius and endcaps at ±2,500 mm for the proposed
offline pointing approximation, without rerunning Stage 1.

The [2026-10-05 field audit](../docs/STAGE2_V3_PHOTON_POINTING_INPUT_AUDIT_2026-10-05.md)
records which photon vectors survive each stage. Inspect schemas without
loading the full EOS sample:

```bash
env -u PYTHONPATH -u PYTHONHOME myenv/bin/python - <<'PYCODE'
import pyarrow.parquet as pq
import uproot

stage0 = '/eos/lhcb/lbdt3/user/rquaglia/fcc_ee/lblgamma/outputs/Lb2LambdaGammaPhysics_nev100000_IDEA_edm4hep.root'
stage1 = '/eos/lhcb/lbdt3/user/rquaglia/fcc_ee/lblgamma/outputs/stage1_v3_my_run/signal_physics.root'
selected = 'outputs/analysis/studies/stage2_v3_incremental_20261002/prepared/signal_-1_selected.parquet'
for label, path, tokens in (
    ('Stage 0', stage0, ('Particle/Particle.momentum', 'Particle/Particle.vertex', 'EFlowPhoton/EFlowPhoton.position')),
    ('Stage 1', stage1, ('lb_photon_', 'reco_mc_')),
):
    tree = uproot.open(path)['events']
    print(label, tree.num_entries)
    print([name for name in tree.keys() if any(token in name for token in tokens)])
table = pq.ParquetFile(selected)
print('Offline candidate rows', table.metadata.num_rows)
print([name for name in table.schema_arrow.names
       if name.startswith(('gamma_', 'photon_'))])
PYCODE
```

Stage 1 keeps reconstructed photon components; the offline prepared table
keeps only their magnitude, transverse momentum, pseudorapidity and energy.
The MC `px/py/pz` and full production vertex require a Stage 0 join.

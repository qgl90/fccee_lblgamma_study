# Stage 2: offline selections, veto studies, and BDT datasets

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

## Optional fixed-model checks: η, K⁰S, and Armenteros

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

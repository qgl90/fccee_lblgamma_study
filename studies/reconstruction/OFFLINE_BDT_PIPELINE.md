# Offline candidate and BDT study

## Inputs and stage boundary

`analysis/studies/lb2lambda_gamma_baseline.py` builds the reconstructed
candidate without MC identity, and `lb2lambda_gamma_reco.py` adds stage-1
observables and truth labels. The native Zbb Condor wrapper
`analysis_preselection_zbb.py` calls the same `RDFanalysis`. The stage-1
configuration is `config/lb_reco_preselection_15mev_45_65.json`:
fitted Lambda mass within 15 MeV, Lambda-gamma mass 4.5–6.5 GeV, and the
vertex, displaced-track, selected-photon, and thrust requirements there.
The ROOT `events` tree has only candidate-bearing events. Its
`eventsProcessed` object is the input-event denominator.

This study uses the physics signal ROOT file and the frozen, schema-checked
Condor chunk catalog. PHSP and eta are separate validation/background tasks;
neither is silently included in the physical Zbb estimate. Both charge
conjugates remain in the signal. The 4.7–6.5 GeV projection range is an
offline subset of the saved stage-1 range. A window wider than 15 MeV
requires stage-1 reconstruction again.

## One run folder

Session artifacts are under
`outputs/analysis/studies/offline_bdt_session_20261001` (a link to EOS).
The ten-chunk check is in `production/`, `bdt_10chunks/`,
`scenario_comparison_10chunks/`, and `projection_10chunks/`. The 679-chunk
frozen-catalog diagnostic run uses `full679/`. A later catalog snapshot of
1,068 valid chunks (393,638,637 processed events) is
`zbb_catalog_current.json`; its ±5 MeV default run uses `lambda5_all1068/`.
The earlier capped check is in `pilot/`.
Keep each new scenario in its own subdirectory with its exact config and
catalog hashes; do not overwrite a reviewed output.

## Commands

Use `env -u PYTHONPATH -u PYTHONHOME myenv/bin/python` for these scripts.
The following shell variables are only abbreviations for the shown paths:

```bash
PY='env -u PYTHONPATH -u PYTHONHOME myenv/bin/python'
SIGNAL=/eos/lhcb/lbdt3/user/rquaglia/fcc_ee/lblgamma/outputs/nominal_preselection_100k_signal_physics_reco.root
CATALOG=outputs/analysis/studies/condor_zbb_chunk_catalog_plots_20261001.json
SESSION=/eos/lhcb/lbdt3/user/rquaglia/fcc_ee/lblgamma/outputs/offline_bdt_session_20261001
CURRENT_CATALOG=$SESSION/zbb_catalog_current.json
$PY studies/reconstruction/prepare_offline_bdt.py --signal "$SIGNAL" \
  --zbb-catalog "$CURRENT_CATALOG" --scenario lambda5 \
  --output-dir "$SESSION/lambda5_all1068"
$PY studies/reconstruction/compare_offline_scenarios.py \
  --prepared-dir "$SESSION/lambda5_all1068" --output-dir "$SESSION/scenario_comparison_all1068"
$PY studies/reconstruction/derive_offline_scenario.py \
  --parent-dir "$SESSION/lambda5_all1068" --scenario lambda5_pi0 \
  --output-dir "$SESSION/lambda5_pi0_all1068"
$PY studies/reconstruction/train_offline_bdt.py \
  --prepared-dir "$SESSION/lambda5_pi0_all1068" --output-dir "$SESSION/bdt_full_pi0_all1068" --score-audit
$PY studies/reconstruction/train_offline_bdt.py \
  --prepared-dir "$SESSION/lambda5_pi0_all1068" --output-dir "$SESSION/bdt_topology_pi0_all1068" \
  --feature-set topology
$PY studies/reconstruction/project_offline_bdt.py \
  --prepared-dir "$SESSION/lambda5_pi0_all1068" --model-dir "$SESSION/bdt_full_pi0_all1068" \
  --output-dir "$SESSION/projection_full_pi0_all1068"
$PY studies/reconstruction/plot_full_sample_projection.py \
  --prepared-dir "$SESSION/lambda5_pi0_all1068" \
  --model-dir "$SESSION/bdt_full_pi0_all1068" \
  --projection-dir "$SESSION/projection_full_pi0_all1068" \
  --output-dir "$SESSION/full_sample_overlay_pi0_all1068"
$PY studies/reconstruction/apply_offline_bdt.py \
  --input-dir "$SESSION/lambda5_pi0_all1068" \
  --model-dir "$SESSION/bdt_full_pi0_all1068" --table audit \
  --output-dir "$SESSION/bdt_full_pi0_all1068/scored_stage1"
```

For a development run, add `--max-zbb-chunks 3 --max-output-events 1000`
to preparation and use a distinct pilot directory. A capped run cannot
recover processed input events from the filtered ROOT output and cannot
quote generated-event efficiency. Training requires complete ROOT files and
at least ten Zbb chunks.

## Output contract

`prepare_offline_bdt.py` streams native jagged ROOT branches. It calculates
the cut masks in awkward arrays before making candidate rows. The audit
Parquets retain every stage-1 candidate, including failed offline cuts;
selected Parquets retain the BDT inputs, identifiers, truth labels for
evaluation, `lb_mass`, `cos_theta_p`, and pass flags. Each row has
`source_id`, `event_entry`, `candidate_slot`, and `candidates_in_event`.
`summary.json` contains ROOT processed counters, stage counts, conditional
and cumulative retention, Lambda-window scans, and selected multiplicity.
The plots compare fitted Lambda mass, scan retention, and multiplicity.

`config/lb_offline_selections.json` names the tested windows and vetoes.
`lambda5` is the default offline selection before BDT training: fitted
Lambda mass within 5 MeV and 4.7–6.5 GeV Lambda-gamma mass, with no photon
veto. The `full679/` native scan was launched for the earlier
`lambda10_pi0_eta` diagnostic and preserves every stage-1 candidate in its
audit shards. Derive the default on exactly these same candidates with:

```bash
$PY studies/reconstruction/derive_offline_scenario.py \
  --parent-dir "$SESSION/full679" --scenario lambda5 \
  --output-dir "$SESSION/lambda5_full679"
```

Then pass `lambda5_full679/` to the training and projection commands. The
comparison script can read either audit directory; because both retain all
candidates, it evaluates every named scenario on the same event set.
The current requested BDT study adds the named `lambda5_pi0` raw-photon
veto after this no-veto reference, while keeping the no-veto tables for
the same-event cutflow and comparison.

The pair list uses all raw type-22 photons other than the candidate photon;
an empty list passes. `compare_offline_scenarios.py` checks every named
scenario on the same audit candidates, retaining direct signal, wrong
signal combinations, Zbb direct decays, and other Zbb combinations as
separate categories. The selected-container same-hemisphere photon veto is
a different detector/object scenario and cannot be reconstructed from this
native pair list.

New stage-1 snapshots also persist both raw-type-22 and selected-photon
pair lists **restricted to the reconstructed Lambda0 thrust hemisphere**,
with matched partner indices. The existing stage-1 configuration already
requires Lambda0 and candidate photon to share a hemisphere. Use a named
`same_hemi_selected` or `same_hemi_all` scenario in
`config/lb_offline_selections.json` when preparing a new snapshot. The
preparation script fails explicitly if the requested list is absent;
the 1,068 older Zbb ROOT files cannot support a complete same-hemisphere
eta-veto projection from their saved branches. The earlier all-raw results
remain a separate two-hemisphere diagnostic.

`study_feeddown_veto.py` uses existing candidate Parquets containing both
the selected same-hemisphere and all-raw-photon pair lists for the 100k
physics and 100k forced-eta samples. It applies the Lambda ±5 MeV and
4.7–6.5 GeV cuts before counting the pi0, pi0+eta, and minimum diphoton
mass thresholds. Pass `--zbb-audit-dir` for the raw-pair Zbb comparison.
It reports a no-partner category explicitly; such candidates pass a veto.

`train_offline_bdt.py` uses direct physics signal and nonmatched inclusive
Zbb as classes. Signal splits are by generated event; Zbb splits are by
whole catalog chunks. The model excludes masses, helicity angle, identity,
truth, and candidate multiplicity. Its JSON model and feature list can be
used to score selected or full stage-1 audit rows. `--score-audit` writes the
latter. Wrong signal combinations and rare direct decays in Zbb remain
diagnostic rows, not training negatives.
Every training run writes held-out ROC, score, input-variable, and feature
importance plots next to the model. `--feature-set topology` trains a
separate ten-input robustness model using vertex, isolation, and thrust
only; keep its output directory distinct from the full model.

The frozen model-input list is:

| Family | Inputs |
|---|---|
| Daughter and candidate kinematics | `proton_pt`, `proton_eta`, `pion_pt`, `pion_eta`, `gamma_E`, `gamma_eta`, `lambda_pt`, `lambda_eta`, `lb_pt`, `lb_eta` |
| Vertex and displacement | `proton_d0sig`, `pion_d0sig`, `lambda_d0_sig`, `lambda_flight_rxy`, `lambda_flight_rxy_sig`, `lambda_vertex_chi2` |
| Isolation and thrust | `iso_R03_noLambda`, `iso_R05_noLambda`, `lambda_thrust_cos`, `gamma_thrust_cos` |
| Z recoil / photon energy estimate | `m_rec`, `Estar_gamma_rec` |

`proton_eta` and related columns are signed pseudorapidity, not true
rapidity. `Estar_gamma_rec` is the stage-1 reconstructed recoil estimate,
not generator truth. Nonfinite values and the stage-1 `-999` sentinel become
missing values for XGBoost. Recoil and candidate kinematics can reflect
generator-production differences; their usefulness requires a separate
feature-ablation and mass/angle-shape check.

`project_offline_bdt.py` scans validation thresholds, requires at least 20
validation-background survivors for an unconstrained diagnostic choice. The
requested working point must additionally have the upper endpoint of its
two-sided 95% validation-background Poisson interval at or below one million
expected candidates in the full 4.7–6.5 GeV range. Among such points the
script maximizes the central `S/sqrt(S+B)` expectation, then evaluates that
fixed cut on independent test partitions. If no point qualifies, the target
is reported as unresolved. The ten-chunk check cannot resolve it: one test
Zbb candidate already represents 1.125 million expected candidates.
The script uses the processed test Zbb
events and generated test signal event IDs as denominators. The candidate
projection uses the supplied branching fractions and one candidate per row;
it also reports event efficiencies and weighted expected test candidates.
The expected table is a weighted MC representation, not literal generated
FCC-ee events. A zero background bin has an approximate three-count upper
scale. Feed-down, model transfer, mass-shape, and angular acceptance need
review before a physics conclusion.
`plot_full_sample_projection.py` uses the validation-fixed score on every
available candidate, including training partitions, and divides by all
100,000 Physics and all 393,638,637 processed Zbb input events. Its single
canvas overlays scaled mass and angle distributions and labels raw MC counts.
This is a presentation view; the disjoint test projection above is the
independent estimate and determines whether the target is met.
`apply_offline_bdt.py` reapplies the frozen model and recorded feature order
to either selected or audit Parquet shards without retraining.

## Photon veto after a fixed BDT working point

For a veto study **after** the already trained `lambda5_pi0` model, use the
scored selected tables and the validation-fixed threshold. This does not
retrain the model or move the score cut:

```bash
$PY studies/reconstruction/evaluate_post_bdt_veto.py \
  --prepared-dir "$SESSION/lambda5_pi0_all1068" \
  --model-dir "$SESSION/bdt_full_pi0_all1068" \
  --projection-dir "$SESSION/projection_full_pi0_all1068" \
  --output-dir "$SESSION/post_bdt_veto_fixed_model"
```

The output compares the current pi0+BDT selection, an additional ±50 MeV
eta mass-window veto, and a stronger requirement that every saved raw
photon-pair mass be at least 1 GeV. A candidate with no saved partner passes
both vetoes. The plots and JSON give all-processed and disjoint-test counts,
scaled expectations, Poisson intervals, and mass/helicity-angle shapes.
The `post_bdt_eta_*` plots isolate the eta-veto result for presentation.
`expected_mass_and_angle.png` shows weighted signal and Zbb candidate
distributions in the full 4.7–6.5 GeV analysis range and in a diagnostic
5.4–5.9 GeV peak interval, plus the corresponding helicity-angle shapes.
The legend gives expected yields and raw test MC counts. Sparse bins retain
their raw MC Poisson error bars and should not be read as a smooth shape.

## Truth ancestry of the fixed-score Zbb survivors

The truth join is a diagnostic after all reconstructed cuts. It uses the
original stage-1 ROOT event and candidate slot, then joins by
`source_id`, `event_entry`, and `candidate_slot`. It does not alter the BDT
score or selection. Run the three steps in order:

```bash
$PY studies/reconstruction/classify_post_bdt_zbb_truth.py \
  --prepared-dir "$SESSION/lambda5_pi0_all1068" \
  --model-dir "$SESSION/bdt_full_pi0_all1068" \
  --projection-dir "$SESSION/projection_full_pi0_all1068" \
  --output-dir "$SESSION/post_bdt_zbb_truth"
$PY studies/reconstruction/summarize_post_bdt_zbb_ancestry.py \
  --rows "$SESSION/post_bdt_zbb_truth/post_bdt_zbb_truth_rows.parquet" \
  --output-dir "$SESSION/post_bdt_zbb_truth"
$PY studies/reconstruction/attach_post_bdt_zbb_truth.py \
  --truth-rows "$SESSION/post_bdt_zbb_truth/post_bdt_zbb_truth_detailed.parquet" \
  --scored-dir "$SESSION/bdt_full_pi0_all1068/scored_selected" \
  --projection "$SESSION/projection_full_pi0_all1068/projection.json" \
  --output-dir "$SESSION/post_bdt_zbb_truth"
```

`post_bdt_zbb_candidates_with_truth.parquet` and `.csv` are the complete
inspectable tables: one row per surviving candidate, with scored features,
mass, angle, event keys, veto flags, and reconstructed proton/pion/photon
indices plus each leg's MC index, signed PDG, first parent index/PDG and
first grandparent index/PDG. `post_bdt_zbb_join_validation.json` verifies
one-to-one coverage and agreement of score, mass, label, and veto quantities.
`post_bdt_zbb_truth_summary.json`, `zbb_ancestry_detailed.json`, and
`zbb_ancestry_detailed.png` give aggregate categories. A reconstructed
particle without a unique MC association has MC index `-1` and PDG `0`.
Parent/grandparent columns record the first available parent only; use the
full stage-1 MC graph if a particle has multiple parents. A direct photon
from a Lambda_b is not by itself a fully matched signal candidate: the
Lambda and photon must share the correct Lambda_b parent.

The per-event three-chain table is produced with:

```bash
$PY studies/reconstruction/export_post_bdt_zbb_ancestry_table.py \
  --input "$SESSION/post_bdt_zbb_truth/post_bdt_zbb_candidates_with_truth.parquet" \
  --output-dir "$SESSION/post_bdt_zbb_truth"
```

`zbb_nonmatched_257_ancestry_chains.md` has exactly three ancestry columns,
one candidate/event per row, with source/event/slot in the first cell. Its
CSV keeps those identifiers as separate machine-readable columns. Signed
particle names are resolved by Scikit-HEP `particle`. Every row already
passes the saved π⁰ veto over all raw type-22 partners in both hemispheres,
so an otherwise identical same-hemisphere π⁰ veto is redundant on this
post-BDT subset. This implication does not supply the missing same-hemisphere
pair masses needed for an η or 1 GeV veto.

## Post-BDT K_S0 mass-hypothesis study

The fitted pπ candidate can be reinterpreted as ππ by retaining both fitted
three-momenta and changing the proton-track mass to the pion mass. The
resulting `m(ππ)` is saved for every scored candidate; no reconstruction or
BDT retraining is involved. The named mass and trial half-windows are in
`config/lb_offline_selections.json` under `kshort_veto_study`.

```bash
$PY studies/reconstruction/study_post_bdt_kshort_veto.py \
  --prepared-dir "$SESSION/lambda5_pi0_all1068" \
  --model-dir "$SESSION/bdt_full_pi0_all1068" \
  --projection-dir "$SESSION/projection_full_pi0_all1068" \
  --zbb-with-truth "$SESSION/post_bdt_zbb_truth/post_bdt_zbb_candidates_with_truth.parquet" \
  --output-dir "$SESSION/post_bdt_kshort_veto"
```

`kshort_veto_scan.json` gives candidate/event counts and conditional
retention for true Physics signal, wrong Physics combinations, nonmatched
Zbb, and genuine direct Zbb decays, separately for all MC and the independent
test partition. It also gives scaled S, B, and S/sqrt(S+B) for each window.
`kshort_mass_hypothesis.png` shows the alternative-mass shapes;
`kshort_veto_retention_scan.png` shows the loss/rejection scan; and the
`kshort_expected_overlay_*` plots show scaled mass and helicity-angle shapes
before and after an illustrative ±5 MeV veto. The two Parquet outputs
preserve the per-candidate alternative mass and distance from the K_S0 mass.
The all-sample plots include training events; use the test-partition counts
for an independent estimate. The window scan is exploratory, not a frozen
new reference selection.

## Pending same-hemisphere post-BDT η and minimum-mass study

The old 1,068 Zbb stage-1 ROOT chunks save all-raw pair masses and indices,
but neither partner momentum nor a complete same-hemisphere pair list.
The attempted direct lookup from catalogued Delphes inputs failed a
candidate-photon index/energy consistency check on its first Zbb event, so
no same-hemisphere η or ≥1 GeV projection from those old chunks is valid.
New stage-1 source code is configured to save both complete selected-photon
and raw-type-22 same-Lambda-hemisphere pair lists. A 100-event Physics
trial passed a comparison of candidate event keys and masses with the old
output after joining by `event_entry`. The earlier apparent mismatch came
from comparing the first rows of a multithreaded ROOT output whose row order
was shuffled. The new reconstruction must now be run on the full Physics
and Zbb inputs and joined to BDT scores by validated event and candidate
keys before quoting a full-sample projection.

## New 3D/activity stage-1 scenario: commands for PI execution

The separate Armenteros study on **existing** pre-BDT selected tuples was
completed without any stage-1 rerun:

```bash
$PY studies/reconstruction/study_armenteros_veto.py \
  --prepared-dir "$SESSION/lambda5_pi0_all1068" \
  --model-dir "$SESSION/bdt_full_pi0_all1068" \
  --projection-dir "$SESSION/projection_full_pi0_all1068" \
  --zbb-with-truth "$SESSION/post_bdt_zbb_truth/post_bdt_zbb_candidates_with_truth.parquet" \
  --config config/lb_armenteros_study.json \
  --output-dir "$SESSION/armenteros_pre_bdt_all1068"
```

`armenteros.py` implements charge-signed α, qT, and a reusable rectangular
veto. The JSON, heatmaps, and candidate-level Parquets in that output
folder report direct signal, wrong signal combinations, Zbb nonmatches,
rare direct Zbb decays, and the 257 post-BDT residuals separately. See
`docs/ARMENTEROS_ACTIVITY_REVIEW_2026-10-01.md` for the observed effect.

The new source code is shared by direct Physics and the Zbb Condor wrapper.
The named config replaces the old Rxy distance/significance cuts with
Lxyz≥0.3 mm and full 3D flight significance≥2; the old scenario remains
available separately. The full direct Physics, PHSP, and η commands have now
been executed with `_v2` output names; the Zbb Condor command remains for
the PI. Keep new output names so the old files remain reviewable.
The updated observable snapshot also saves `lb_thrust_cos`, original-axis
opposite-hemisphere momentum and energy (`opp_hemi_*`), partial candidate-plus-
opposite-hemisphere Z closure (`z_partial_*`), and full reconstructed-event
closure (`z_full_*`). Candidate-removed same-Λ-hemisphere isolation sums now
cover ΔR=0.2, 0.3, 0.5, 0.7, 1.0, and 7.0, with all/charged/neutral energy
and momentum components in each cone. No new quantity changes the candidate
selection or the frozen BDT used in the older analysis.

```bash
source external/FCCAnalyses/setup.sh
LB_RECO_CONFIG="$PWD/config/lb_reco_preselection_15mev_45_65_3d.json" \
  fccanalysis run analysis/studies/lb2lambda_gamma_reco.py \
  --files-list /eos/lhcb/lbdt3/user/rquaglia/fcc_ee/lblgamma/outputs/Lb2LambdaGammaPhysics_nev100000_IDEA_edm4hep.root \
  --output /eos/lhcb/lbdt3/user/rquaglia/fcc_ee/lblgamma/outputs/nominal_preselection_100k_signal_physics_reco_3d_activity.root \
  --ncpus 4

fccanalysis run analysis/studies/analysis_preselection_zbb.py \
  --input-glob '/eos/experiment/fcc/ee/generation/DelphesEvents/winter2023/IDEA/p8_ee_Zbb_ecm91/events_*.root' \
  --chunks 1200 --comp-group group_u_LHCBT3.e_lhcb_lbd \
  --queue workday --ncpus 4 \
  --output-eos /eos/lhcb/lbdt3/user/rquaglia/fcc_ee/lblgamma/outputs/zbb_full_condor/native_batch_3d_activity_v2 \
  --eos-type eoslhcb --check-only
```

After reviewing the check-only report, the identical Zbb command without
`--check-only` submits the new campaign. The wrapper defaults to this same
3D config and the distinct `native_batch_3d_activity_v2` output location.
The check-only command was run on 2026-10-02: it found 4,398 ROOT inputs,
planned 1,200 chunks (about 3.67 files/job), printed the named 3D config
and v2 EOS destination, and submitted no jobs.

The same stage-1 Condor wrapper also accepts the winter2023 IDEA Zcc and Zss
directories. It takes the sample name from the input-glob parent directory,
uses that name for the FCCAnalyses process and chunk directory, and requires a
distinct `--output-eos` for non-Zbb samples. For example, replace the Zbb
input and destination above with
`p8_ee_Zcc_ecm91/events_*.root` and
`outputs/zcc_full_condor/native_batch_3d_activity_v2`; use `Zss` and `zss`
likewise. The 2026-10-02 check-only runs found 5,018 Zcc and 5,015 Zss input
files; neither submitted jobs. Run the same command without `--check-only` on
a Condor-enabled host to submit each campaign. The chunk cataloging helper
accepts Zbb, Zcc, and Zss process names from each job-directory basename.
Record the generated job directory and catalog the completed chunks before
offline preparation. For a new snapshot, specify a `same_hemi_all` or
`same_hemi_selected` scenario explicitly; for example
`lambda5_pi0_same_hemi_all` to apply the π⁰ veto before training, or
`lambda5_same_hemi_all` to save an unvetoed comparison. The old
`lambda5_pi0` scenario remains the both-hemisphere historical baseline.

The 100-event validation used the same direct command with
`--nevents 100 --ncpus 1`. The ROOT output and validation JSON are preserved
under `$SESSION/stage1_3d_activity_trial_100/`. Recheck the preserved ROOT with:

```bash
env -u PYTHONPATH -u PYTHONHOME myenv/bin/python \
  studies/reconstruction/validate_stage1_activity.py \
  --trial "$SESSION/stage1_3d_activity_trial_100/lblgamma_activity_3d_stage1_trial_100.root" \
  --baseline /eos/lhcb/lbdt3/user/rquaglia/fcc_ee/lblgamma/outputs/nominal_preselection_100k_signal_physics_reco.root \
  --event-limit 100 --output /tmp/lblgamma_activity_3d_validation_recheck_100.json
```

The historical Physics ROOT output was written with multiple threads and
is not sorted by `event_entry`; comparing the first output rows gave a false
candidate-set mismatch. On the first 100 input entries, joining by
`event_entry` worked. The later full old/v2 audit found that `event_entry`
is itself reassigned for many otherwise identical events, so use the
PV/thrust event fingerprint for full cross-version matching.

## Completed direct-sample v2 outputs

The full 100k Physics, PHSP, and Λb→Λη-as-γ direct runs now have distinct
`_v2.root` and `_candidates_v2.parquet` files listed with checksums in
`config/lb_stage1_v2_samples.json`. The old reference files remain intact.
See `docs/STAGE1_V2_FULL_REPROCESS_REVIEW_2026-10-01.md` and the session's
`stage1_v2_full_comparison/` folder for keyed candidate comparisons and
mass/angular overlay plots. Shared candidate truth labels and kinematics
agree, but the 3D scenario gains or loses a few candidates. Historical
`event_entry` values also differ for many identical physical events across
these two productions; use the review script's PV/thrust fingerprint for
cross-version comparisons.

When the PI's v2 Zbb Condor catalog is complete, prepare a **new** offline
dataset using the v2 Physics ROOT and the named 3D config, for example:

```bash
env -u PYTHONPATH -u PYTHONHOME myenv/bin/python \
  studies/reconstruction/prepare_offline_bdt.py \
  --signal /eos/lhcb/lbdt3/user/rquaglia/fcc_ee/lblgamma/outputs/nominal_preselection_100k_signal_physics_reco_v2.root \
  --zbb-catalog PATH_TO_V2_ZBB_CATALOG.json \
  --config config/lb_offline_selections.json \
  --stage1-config config/lb_reco_preselection_15mev_45_65_3d.json \
  --scenario lambda5_pi0_same_hemi_all \
  --output-dir PATH_TO_NEW_V2_PREPARED_OUTPUT
```

This command is a template until the v2 Zbb catalog exists. The old BDT
model and its projections remain tied to the old stage-1 inputs.

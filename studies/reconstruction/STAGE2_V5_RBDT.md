# Stage 2 v5: attach the candidate BDT score

`apply_v5_rbdt_stage2.py` reads one or more v5 Stage-1 ROOT files, evaluates
the trained `TMVA::Experimental::RBDT<>` model for each reconstructed
\(\Lambda_b\) candidate, and writes a new ROOT file with the original `events`
tree columns plus `v5_bdt_score`. The score and optional `v5_bdt_pass` branches
are candidate vectors ordered like `lb_mass`; original candidate and event
columns are retained.

The script does not change the Stage-1 selection. It adds a score and, if
requested, a mask so later analysis code can apply a candidate-level threshold.
`--filter-events-with-passing-candidate` is an optional event filter: it keeps
events with at least one passing candidate and retains all candidate vectors
for those events. Use `v5_bdt_pass` to select individual candidates.

## Model and feature provenance

The model was trained from the all-inventory v5 candidate Parquet dataset:

- Dataset: `v5_stage1_bdt_all_27features.parquet` (6,928,901 candidate rows)
- Feature order and recipes: `selected_features.json`
- Repository copy of that feature schema: `v5_bdt_feature_schema.json.in`
- Parquet schema builder: `audit_v5_bdt_features.py`
- Stage-1 vector Snapshot to Parquet: `extract_v5_chunk_rdf.py` and
  `flatten_v5_snapshot_to_parquet.py`
- Model files: `v5_weighted_bdt_all27.json` (XGBoost) and
  `v5_weighted_bdt_rbdt.root` (RDataFrame/TMVA inference)

`v5_bdt_feature_schema.json.in` records the canonical feature names, meanings,
source branches, and transforms. It mirrors the schema written beside each
training dataset as `selected_features.json`. The flattening step
reads `v5_feature_0` through `v5_feature_26` in that order, writes one Parquet
row per candidate, and records event entry and candidate slot. The Stage-2
script uses the matching branch and transform definitions from
`audit_v5_bdt_features.FEATURES`, verifies the ROOT model's `variables` list
against the JSON order, and checks that every score vector has the same
candidate count as `lb_mass`.

The model uses all 27 proposed inputs, including the two FT scores for each of
B, C, S, Q, and G hypotheses, both isolation variables at the \(R=0.20\) cone,
and the kinematic and displacement quantities. The pi0/eta vetoes and final
mass/angle selections were not applied in training.

## Reuse the trained model

From the repository root, run one Stage-1 file per job. Point `--model` and
`--features-json` to the artifacts from your completed training directory:

```bash
./myenv/run python studies/reconstruction/apply_v5_rbdt_stage2.py \
  --input /path/to/stage1_chunk.root \
  --model /path/to/model/v5_weighted_bdt_rbdt.root \
  --features-json studies/reconstruction/v5_bdt_feature_schema.json.in \
  --output /path/to/stage2_chunk.root \
  --threads 8
```

To create a per-candidate boolean mask at a chosen threshold, add
`--score-cut 0.95`. To retain only events containing at least one candidate
above that threshold, also add
`--filter-events-with-passing-candidate`. The mask stays aligned with the
candidate vectors, including when the optional event filter is used.

The output receives a `.stage2.json` sidecar recording the ordered features,
feature definitions, model SHA256, source file list and event counters, score
branch, cut semantics, and thread setting. The ROOT output also carries summed
`eventsProcessed` and `eventsSelected` counters when those counters exist in
the inputs. Use separate output names for each Stage-1 chunk; merge Stage-2
chunks only after each job has completed.

## Current training report

The completed training/report artifacts for the current fit are in
`/tmp/rquaglia/v5_bdt_all_20261007/model_complete/`:

- `training_summary.json`: split counts, physical yields, and weighted AUCs
- `weighted_roc_test.png`: weighted test ROC, including the individual Zbb,
  Zcc, and Zss comparisons
- `test_score_physical_yields.png`: physical-yield score distributions
- `feature_distributions_physical_weights.pdf`: all 27 training variables
- `correlation_signal_weighted.png` and
  `correlation_background_mixture_weighted.png` (plus CSV matrices)
- `v5_weighted_bdt_rbdt.root`: verified ROOT RBDT object and feature list

This is a high-separation pilot fit. Reassess its score threshold using the
full physical-yield projections and the later pi0/eta vetoes before quoting a
final sensitivity.

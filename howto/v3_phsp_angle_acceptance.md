# Reproduce the v3 PHSP angular acceptance

The existing `signal_phsp.root` under `stage1_v3_my_run/` has already
processed all 100,000 PHSP EDM4hep input events. Its ROOT counters are
100,000 processed and 56,737 candidate-bearing output events. Keep this
historical v3 path fixed; new v3 Stage 1 basenames follow
[the Stage 1 guide](stage1.md). The PHSP generator input is
`/eos/lhcb/lbdt3/user/rquaglia/fcc_ee/lblgamma/outputs/Lb2LambdaGamma_nev100000_IDEA_edm4hep.root`.
See the [PI review](../docs/STAGE2_V3_PHSP_ANGLE_REVIEW_2026-10-04.md) for
the exact counts and interpretation.

From the repository root, use the frozen 1,028-chunk BDT model and its
validation score. The runner applies the same Stage 2 offline config to
all Stage 1 candidates, scores them, retains audit/selected/BDT-selected
tables, and records the input, model and config hashes. Truth is carried
only for evaluation; the cut and score use reconstructed variables.

```bash
RUN=/eos/lhcb/lbdt3/user/rquaglia/fcc_ee/lblgamma/outputs
STAGE1="$RUN/stage1_v3_my_run/signal_phsp.root"
GEN="$RUN/Lb2LambdaGamma_nev100000_IDEA_edm4hep.root"
MODEL="$RUN/stage2_v3_incremental/models/20261003_1028chunks"
PROJECTION="$RUN/stage2_v3_incremental/projections/20261003_1028chunks/projection.json"
OUT="$RUN/stage2_v3_phsp_100k_bdt1028"
PY="$PWD/myenv/bin/python"

env -u PYTHONPATH -u PYTHONHOME "$PY" \
  studies/reconstruction/score_stage1_v3_dataset.py \
  --input "$STAGE1" --model-dir "$MODEL" --projection "$PROJECTION" \
  --output-dir "$OUT/stage2" --sample signal_phsp_v3 --source-id -2

env -u PYTHONPATH -u PYTHONHOME "$PY" \
  studies/reconstruction/study_v3_phsp_angle_acceptance.py \
  --generator "$GEN" --generated-events 100000 --stage1 "$STAGE1" \
  --stage2-manifest "$OUT/stage2/manifest.json" --output-dir "$OUT/angle"
```

For the run documented here, the full candidate tables were first built
under `/tmp/v3_phsp_100k_stage2_bdt_1028/` and then copied unchanged to
the durable `OUT/stage2/` directory; their manifest SHA256 matches across
those locations. The angle outputs were similarly copied from
`/tmp/v3_phsp_angle_100k_bdt1028/` to `OUT/angle/`. These copied manifests
retain the original scratch command path, so use the commands above for a
fresh run. The repository keeps the fit CSV, JSON, generated and selected
decay tables, and figures under `docs/data/` and `docs/figures/`.

The numerator uses unique fully truth-matched direct decays after each
stage, in bins of **generated** cos θp. The denominator is every generated
direct Λb or anti-Λb decay in the 100k PHSP file, including events with no
reconstructed candidate. The content match uses truth angle and charge
because Stage 1 `event_entry` is not a raw EDM4hep row ID in this
multithreaded snapshot. The final JSON also gives reconstructed-minus-truth
resolution, tails, and a truth-row/reconstructed-column response matrix.
Changing the BDT score, model, Stage 1 config, detector card, or offline
scenario requires a new named run and new response for the fit.

## Refreshed 1,091-chunk model and optional Armenteros box

The [separate PI review](../docs/STAGE2_V3_PHSP_ANGLE_BDT1091_REVIEW_2026-10-04.md)
and its results-list figures preserve this later score scenario. Use the
same Stage 1 and generator paths above, but set:

```bash
MODEL="$RUN/stage2_v3_incremental/models/20261004_1091chunks"
PROJECTION="$RUN/stage2_v3_incremental/projections/20261004_1091chunks_peak_5p4_5p9/projection.json"
OUT="$RUN/stage2_v3_phsp_100k_bdt1091peak"

env -u PYTHONPATH -u PYTHONHOME "$PY" \
  studies/reconstruction/score_stage1_v3_dataset.py \
  --input "$STAGE1" --model-dir "$MODEL" --projection "$PROJECTION" \
  --output-dir "$OUT/stage2" --sample signal_phsp_v3 --source-id -2

env -u PYTHONPATH -u PYTHONHOME "$PY" \
  studies/reconstruction/study_v3_phsp_angle_acceptance.py \
  --generator "$GEN" --generated-events 100000 --stage1 "$STAGE1" \
  --stage2-manifest "$OUT/stage2/manifest.json" --output-dir "$OUT/angle"

env -u PYTHONPATH -u PYTHONHOME "$PY" \
  studies/reconstruction/study_v3_phsp_armenteros_acceptance.py \
  --baseline-angle-dir "$OUT/angle" \
  --bdt-candidates "$OUT/stage2/bdt_selected/signal_phsp_v3_-2.parquet" \
  --box 0.67 0.78 0.075 0.120 \
  --output-dir "$OUT/angle_armenteros_broad"
```

The recorded calculation used `/tmp/v3_phsp_100k_stage2_bdt1091peak/`,
`/tmp/v3_phsp_100k_angle_bdt1091peak/`, and
`/tmp/v3_phsp_100k_angle_bdt1091peak_armenteros/` as distinct trial
locations. The fit JSONs, CSVs and plots are copied to the named
`docs/data/` and `docs/figures/` directories. The box remains a proposal;
keep both fit responses rather than overwriting either one.

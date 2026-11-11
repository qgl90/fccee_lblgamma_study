# v3 post-BDT Armenteros and ancestry study

Run from the repository root. This study reads only the frozen 1,028-chunk
v3 model's scored selected Parquets. The selected candidates already pass
the named offline selection but have **not** been filtered by score. The
script applies the frozen validation score, then a reconstructed Armenteros
box. Truth and ancestry classify the survivors afterward; they never define
the box. It does not retrain XGBoost or alter the reference selection.

```bash
RUN=/eos/lhcb/lbdt3/user/rquaglia/fcc_ee/lblgamma/outputs/stage2_v3_incremental
MODEL="$RUN/models/20261003_1028chunks"
PROJECTION="$RUN/projections/20261003_1028chunks"
PY="$PWD/myenv/bin/python"

env -u PYTHONPATH -u PYTHONHOME "$PY" \
  studies/reconstruction/study_v3_post_bdt_armenteros.py \
  --model-dir "$MODEL" --projection-dir "$PROJECTION" \
  --box 0.67 0.78 0.075 0.120 --workers 8 \
  --output-dir "$RUN/diagnostics/20261003_1028chunks/armenteros_broad"

env -u PYTHONPATH -u PYTHONHOME "$PY" \
  studies/reconstruction/study_v3_post_bdt_armenteros.py \
  --model-dir "$MODEL" --projection-dir "$PROJECTION" \
  --box 0.70 0.75 0.09 0.11 --workers 8 \
  --output-dir "$RUN/diagnostics/20261003_1028chunks/armenteros_narrow"
```

The script checks the model/projection scenario and presence of every scored
chunk, reads independent Parquet shards with eight I/O workers, and records
SHA256 of the model's immutable preparation manifest, training summary and
projection. `summary.json` contains candidate and unique output-event counts
before/after the cut for direct signal, wrong signal combinations, nonmatched
Zbb, direct-in-Zbb, and truth-labelled K⁰S pairs, separately for all,
validation, and test. The small post-BDT candidate tables preserve
`source_id`, `event_entry`, `candidate_slot`, truth audit labels, α, qT,
BDT score, mass and helicity angle. `armenteros_post_bdt_*.png` are the
PI-facing plots. Input-event denominators come from the frozen manifest and
projection, not from the number of output rows. Direct signal includes both
charge conjugates.

The [PI review](../docs/STAGE2_V3_ARMENTEROS_REVIEW_2026-10-03.md) and
repository copies under `docs/data/stage2_v3_armenteros_1028/` and
`docs/figures/stage2_v3_armenteros_1028/` freeze the observed comparison.
The old optional `study_armenteros_veto.py` example in
[howto/stage2.md](stage2.md) uses a different π⁰-veto scenario and must not
be mixed with this no-photon-veto v3 model.

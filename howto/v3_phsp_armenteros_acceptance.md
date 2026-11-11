# Reproduce the v3 PHSP acceptance after the Armenteros proposal

This is an additional stage after the [frozen 100k PHSP Stage 1/offline/BDT
chain](v3_phsp_angle_acceptance.md). It uses that chain's unchanged
generated-decay denominator and BDT-selected candidate table. The box is
the proposal in [the post-BDT ancestry review](../docs/STAGE2_V3_ARMENTEROS_REVIEW_2026-10-03.md),
not an adopted selection. The [PI acceptance review](../docs/STAGE2_V3_PHSP_ARMENTEROS_ANGLE_REVIEW_2026-10-04.md)
reports the measured effect and links the figures in its results list.

From the repository root:

```bash
RUN=/eos/lhcb/lbdt3/user/rquaglia/fcc_ee/lblgamma/outputs/stage2_v3_phsp_100k_bdt1028
env -u PYTHONPATH -u PYTHONHOME myenv/bin/python \
  studies/reconstruction/study_v3_phsp_armenteros_acceptance.py \
  --baseline-angle-dir "$RUN/angle" \
  --bdt-candidates "$RUN/stage2/bdt_selected/signal_phsp_v3_-2.parquet" \
  --box 0.67 0.78 0.075 0.120 \
  --output-dir "$RUN/angle_armenteros_broad"
```

The recorded run used the byte-identical baseline angle JSON and generated
decay Parquet copied into `docs/data/stage2_v3_phsp_angle_100k_bdt1028/`,
and wrote trial results under `/tmp/v3_phsp_armenteros_100k_bdt1028/`.
Its fit CSV, JSON, selected direct-decay table and plots are preserved in
`docs/data/stage2_v3_phsp_armenteros_100k_bdt1028/` and
`docs/figures/stage2_v3_phsp_armenteros_100k_bdt1028/`.
The JSON hashes the baseline JSON and BDT candidate table, verifies every
baseline truth-bin count, and records both the baseline and post-veto
response. The veto uses only `arm_alpha` and `arm_qt` from fitted tracks.

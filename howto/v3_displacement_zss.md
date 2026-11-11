# Reproduce the v3 Zss displacement comparison

Run from the repository root after reading the [PI review](../docs/STAGE2_V3_DISPLACEMENT_ZSS_2026-10-04.md).
This reads scored v3 candidate tables; it does not rerun Delphes or Stage 1.
The script checks model and catalog identity, selects the same candidate rows
at each threshold, and writes JSON, CSV and two PNGs. Truth pair origin is
reported after reco selection only.

```bash
BASE=/eos/lhcb/lbdt3/user/rquaglia/fcc_ee/lblgamma/outputs
SCORED="$BASE/stage2_v3_incremental/models/20261004_1091chunks/scored_selected"
FLAVOUR="$BASE/stage2_v3_zcc_zss_1200_bdt1091peak"
PSEUDO="$BASE/stage2_v3_pseudoscalar_physics_100k_bdt1091peak"
PROJECTION="$BASE/stage2_v3_incremental/projections/20261004_1091chunks_peak_5p4_5p9/projection.json"

env -u PYTHONPATH -u PYTHONHOME MPLCONFIGDIR=/tmp/rquaglia_mplconfig \
  XDG_CACHE_HOME=/tmp/rquaglia_cache myenv/bin/python \
  studies/reconstruction/study_v3_displacement_zss.py \
  --signal "$SCORED/signal_-1_selected.parquet" \
  --zbb-scored-dir "$SCORED" \
  --zbb-catalog docs/data/stage2_v3_bdt_1091_peak/20261003_1091chunks.json \
  --zcc-summary "$FLAVOUR/v3_zcc_1200_bdt1091peak/summary.json" \
  --zss-summary "$FLAVOUR/v3_zss_1200_bdt1091peak/summary.json" \
  --eta "$PSEUDO/v3_eta_physics_100k_stage2_bdt1091peak/bdt_selected/lb_lambdaeta_physics_v3_-5.parquet" \
  --pi0 "$PSEUDO/v3_pi0_physics_100k_stage2_bdt1091peak/bdt_selected/lb_lambdapi0_physics_v3_-4.parquet" \
  --eta-summary docs/data/stage2_v3_pseudoscalar_100k_bdt1091peak/eta_physics_summary.json \
  --pi0-summary docs/data/stage2_v3_pseudoscalar_100k_bdt1091peak/pi0_physics_summary.json \
  --projection "$PROJECTION" --workers 16 \
  --output-dir /tmp/v3_displacement_zss_1091peak
```

The frozen results are in `docs/data/stage2_v3_displacement_zss_1091peak/`
and `docs/figures/stage2_v3_displacement_zss_1091peak/`. The JSON stores
the config, projection, training summary and input summary hashes; it records
each peak candidate count, candidate-bearing event count, physical factor,
Poisson candidate-count interval, and conditional retention. The 95% intervals
do not include normalization or detector uncertainty. Forced Λη and Λπ⁰
outputs remain separate from inclusive Zbb.

# Reproduce the four-step v3 post-BDT veto comparison

The [PI review](../docs/STAGE2_V3_POST_BDT_VETO_SEQUENCE_2026-10-04.md)
lists exact counts and all result figures. This is a post-filter of the
frozen 1,091-chunk v3 BDT snapshot; it does not retrain the model or change
Stage 1. All rows in the scored tables retain the unvetoed diagnostics.

From the repository root, run:

```bash
RUN=/eos/lhcb/lbdt3/user/rquaglia/fcc_ee/lblgamma/outputs/stage2_v3_incremental
MODEL="$RUN/models/20261004_1091chunks"
PROJECTION="$RUN/projections/20261004_1091chunks_peak_5p4_5p9/projection.json"
ZBB_CATALOG=docs/data/stage2_v3_bdt_1091_peak/20261003_1091chunks.json
SIGNAL="$MODEL/scored_selected/signal_-1_selected.parquet"
ETA=/eos/lhcb/lbdt3/user/rquaglia/fcc_ee/lblgamma/outputs/stage2_v3_pseudoscalar_physics_100k_bdt1091peak/v3_eta_physics_100k_stage2_bdt1091peak/bdt_selected/lb_lambdaeta_physics_v3_-5.parquet
PI0=/eos/lhcb/lbdt3/user/rquaglia/fcc_ee/lblgamma/outputs/stage2_v3_pseudoscalar_physics_100k_bdt1091peak/v3_pi0_physics_100k_stage2_bdt1091peak/bdt_selected/lb_lambdapi0_physics_v3_-4.parquet

env -u PYTHONPATH -u PYTHONHOME MPLCONFIGDIR=/tmp/rquaglia_mplconfig \
  XDG_CACHE_HOME=/tmp/rquaglia_cache myenv/bin/python \
  studies/reconstruction/study_v3_post_bdt_veto_sequence.py \
  --signal "$SIGNAL" --zbb-scored-dir "$MODEL/scored_selected" \
  --zbb-catalog "$ZBB_CATALOG" --eta "$ETA" --pi0 "$PI0" \
  --eta-summary docs/data/stage2_v3_pseudoscalar_100k_bdt1091peak/eta_physics_summary.json \
  --pi0-summary docs/data/stage2_v3_pseudoscalar_100k_bdt1091peak/pi0_physics_summary.json \
  --projection "$PROJECTION" --workers 12 \
  --output-dir /tmp/v3_post_bdt_veto_sequence_1091peak_four_components
```

The tracked [scenario JSON](../config/v3_post_bdt_veto_sequence.json) fixes
the broad Armenteros box and the same-hemisphere raw-photon pair definition,
20 MeV π⁰ window and 50 MeV η window. The script requires every Zbb scored
shard named in the frozen catalog; signal true matches, signal wrong
combinations and nonmatched Zbb are counted separately. It writes exact
candidate and candidate-bearing-event counts and approximate candidate-count
95% intervals before plotting. Its linear mass and cos θp figures are copied
to the result links in the PI review.

After the separately processed Zcc and Zss samples have complete manifests,
repeat the command above, adding these two arguments before the output
directory and replacing its final `--output-dir` value:

```bash
LIGHT=/eos/lhcb/lbdt3/user/rquaglia/fcc_ee/lblgamma/outputs/stage2_v3_zcc_zss_1200_bdt1091peak
env -u PYTHONPATH -u PYTHONHOME MPLCONFIGDIR=/tmp/rquaglia_mplconfig \
  XDG_CACHE_HOME=/tmp/rquaglia_cache myenv/bin/python \
  studies/reconstruction/study_v3_post_bdt_veto_sequence.py \
  --signal "$SIGNAL" --zbb-scored-dir "$MODEL/scored_selected" \
  --zbb-catalog "$ZBB_CATALOG" --eta "$ETA" --pi0 "$PI0" \
  --eta-summary docs/data/stage2_v3_pseudoscalar_100k_bdt1091peak/eta_physics_summary.json \
  --pi0-summary docs/data/stage2_v3_pseudoscalar_100k_bdt1091peak/pi0_physics_summary.json \
  --projection "$PROJECTION" --workers 16 \
  --zcc-summary "$LIGHT/v3_zcc_1200_bdt1091peak/summary.json" \
  --zss-summary "$LIGHT/v3_zss_1200_bdt1091peak/summary.json" \
  --output-dir /tmp/v3_post_bdt_veto_sequence_1091peak_all_flavours
```

The extra curves
are individually weighted by `N_Z × B(Z→cc or ss) / processed input events`.
The Zss fraction in the scenario is the PDG down-type average applied under
an explicit equal-down-type assumption. The forced η and π⁰ estimates are
not summed with inclusive Zbb until their overlap is audited.

Audit the inclusive post-BDT ancestry separately, using truth only after
reconstructed selection:

```bash
env -u PYTHONPATH -u PYTHONHOME MPLCONFIGDIR=/tmp/rquaglia_mplconfig \
  XDG_CACHE_HOME=/tmp/rquaglia_cache myenv/bin/python \
  studies/reconstruction/audit_v3_zbb_pseudoscalar_overlap.py \
  --scored-dir "$MODEL/scored_selected" --catalog "$ZBB_CATALOG" \
  --projection "$PROJECTION" --workers 16 \
  --output /tmp/v3_zbb_pseudoscalar_overlap_1091peak.json
```

The 1,091-chunk BDT snapshot contains no true direct η or π⁰ partial chain
candidate after the score. This finite-sample observation does not remove
their physical overlap with the inclusive Zbb expectation; keep their forced
mode projections separate.

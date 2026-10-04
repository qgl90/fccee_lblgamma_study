# Reproduce the v3 three-flavour score study

This is the frozen 2026-10-04 1,091-Zbb-chunk model, 1,200-Zcc-chunk and 1,200-Zss-chunk scenario. Read the [PI review](../docs/STAGE2_V3_THREE_FLAVOUR_SCORE_REOPTIMIZATION_2026-10-04.md) and the exact input/catalog hashes in the [scan JSON](../docs/data/stage2_v3_three_flavour_score_1091peak/three_flavour_score_scan.json). It uses already scored, one-candidate-per-row Stage 2 v3 Parquet shards; no new reconstruction or training is performed here.

The current PI objective is **S/√(S+Bbb+Bcc+Bss)** with the reconstructed Armenteros box applied. The archived `stage2_v3_three_flavour_sqrtb_1091peak/` snapshot used S/√B and is a superseded diagnostic, not a selection prescription. All three backgrounds are scaled with their own processed-event counts and Z branching scenario. The current additional-cut snapshot is `stage2_v3_three_flavour_splusb_d0sig5_1091peak/`.

From the repository root, with the EOS outputs mounted and `myenv` available:

```bash
mkdir -p /tmp/v3_three_flavour_score_scan_1091peak
env -u PYTHONPATH -u PYTHONHOME myenv/bin/python \
  studies/reconstruction/scan_v3_three_flavour_score.py \
  --output-dir /tmp/v3_three_flavour_score_scan_1091peak --workers 16
```

Verify the manifest's catalog/model/config hashes and the old-score peak cutflow against the [fixed-score six-component review](../docs/STAGE2_V3_ZCC_ZSS_AND_VETO_REVIEW_2026-10-04.md). Do not overwrite the earlier four-scenario frozen snapshot at `docs/data/stage2_v3_three_flavour_score_1091peak/`; current code adds the paired Λ-IP alternatives. The script scans each unique surviving observed score exactly; the plotted grid is only a display interpolation. Six scenarios are included: Armenteros alone, +η, +π⁰, +π⁰+η, +|lambda_d0_sig|≥5 and +|lambda_d0_sig|≥5+η. For each scenario read `choices.*.validation_maximum` and `choices.*.test_at_validation_choice`; never choose a threshold from the test maximum.

Then use the frozen in-repository scan to recompute the generated-denominator PHSP curve and the physically weighted stack:

```bash
SCAN=docs/data/stage2_v3_three_flavour_score_1091peak/three_flavour_score_scan.json
OUT=docs/data/stage2_v3_three_flavour_score_1091peak
env -u PYTHONPATH -u PYTHONHOME myenv/bin/python \
  studies/reconstruction/study_v3_phsp_reoptimized_score.py \
  --scan "$SCAN" --output-dir "$OUT"
env -u PYTHONPATH -u PYTHONHOME myenv/bin/python \
  studies/reconstruction/plot_v3_reoptimized_stack.py \
  --scan "$SCAN" --output-dir "$OUT" --workers 16
```

Copy the three resulting PNGs to `docs/figures/stage2_v3_three_flavour_score_1091peak/`; retain the JSON and fit acceptance CSV in `docs/data/`. The PHSP denominator is 100,007 generated direct decays, matched by generated event and candidate identity after each reconstructed selection. The stack cross-checks its peak raw counts against the scan JSON. Forced Λη and Λπ⁰ curves are separate from the inclusive Zbb/Zcc/Zss stack to avoid potential double counting. The scan optimizes only inclusive B, not wrong combinations or forced-mode estimates.

The proposed score is a validation-derived study point. A new training mixture, detector scenario, catalog, branching scenario, or veto window requires a new snapshot name, new manifest, paired baseline and PHSP acceptance.

## Reproduce the corrected S/√(S+B) Λ-IP alternative

The `|lambda_d0_sig|≥5` threshold is inherited from the [earlier displacement review](../docs/STAGE2_V3_DISPLACEMENT_ZSS_2026-10-04.md). It is applied to reconstructed candidates **after** scoring; the BDT model and inputs are unchanged. From the repository root:

```bash
OUT=docs/data/stage2_v3_three_flavour_splusb_d0sig5_1091peak
FIG=docs/figures/stage2_v3_three_flavour_splusb_d0sig5_1091peak
mkdir -p "$OUT" "$FIG"
env -u PYTHONPATH -u PYTHONHOME myenv/bin/python \
  studies/reconstruction/scan_v3_three_flavour_score.py \
  --objective s_over_sqrt_s_plus_b --workers 16 --output-dir "$OUT"
env -u PYTHONPATH -u PYTHONHOME myenv/bin/python \
  studies/reconstruction/study_v3_phsp_reoptimized_score.py \
  --scan "$OUT/three_flavour_score_scan.json" --scenario arm_d0sig5 --output-dir "$OUT"
env -u PYTHONPATH -u PYTHONHOME myenv/bin/python \
  studies/reconstruction/plot_v3_reoptimized_stack.py \
  --scan "$OUT/three_flavour_score_scan.json" --scenario arm_d0sig5 \
  --workers 16 --output-dir "$OUT"
cp "$OUT"/*.png "$FIG"/
```

The no-IP and IP branches use the same candidate rows, model, score column and physical weights. Their thresholds are each chosen on validation: 0.9855620861 for `arm_only`, 0.9810956120 for `arm_d0sig5`. The new JSON records both cutflows, raw tail counts, expected three-component background and counting intervals. `new_bdt_arm` in the PHSP JSON denotes the chosen `scenario` field; for this run it **includes** the Λ-IP cut. The full-archive stack is descriptive because it includes model-training chunks. The IP threshold was proposed after inspecting related data, so a fresh independent confirmation is needed before adoption.

## Historical S/√B diagnostic (superseded objective)

Use a new output directory so the earlier objective is not overwritten:

```bash
OUT=docs/data/stage2_v3_three_flavour_sqrtb_1091peak
FIG=docs/figures/stage2_v3_three_flavour_sqrtb_1091peak
mkdir -p "$OUT" "$FIG"
env -u PYTHONPATH -u PYTHONHOME myenv/bin/python \
  studies/reconstruction/scan_v3_three_flavour_score.py \
  --objective s_over_sqrt_b --workers 16 --output-dir "$OUT"
env -u PYTHONPATH -u PYTHONHOME myenv/bin/python \
  studies/reconstruction/plot_v3_sqrtb_tight_scan.py \
  --scan "$OUT/three_flavour_score_scan.json" \
  --output "$FIG/three_flavour_sqrtb_tight_scan.png"
env -u PYTHONPATH -u PYTHONHOME myenv/bin/python \
  studies/reconstruction/study_v3_phsp_reoptimized_score.py \
  --scan "$OUT/three_flavour_score_scan.json" --output-dir "$OUT"
env -u PYTHONPATH -u PYTHONHOME myenv/bin/python \
  studies/reconstruction/plot_v3_reoptimized_stack.py \
  --scan "$OUT/three_flavour_score_scan.json" --output-dir "$OUT" --workers 16
cp "$OUT"/*.png "$FIG"/
```

This archive produced 0.9918887019 under S/√B and is retained for audit only. It is **not** the PI's current score objective or the operating-point recommendation. Zero-background points are undefined for central S/√B. Its PHSP acceptance and stack apply only to that superseded scenario.

# Reproduce the v3 three-flavour score study

This is the frozen 2026-10-04 1,091-Zbb-chunk model, 1,200-Zcc-chunk and 1,200-Zss-chunk scenario. Read the [PI review](../docs/STAGE2_V3_THREE_FLAVOUR_SCORE_REOPTIMIZATION_2026-10-04.md) and the exact input/catalog hashes in the [scan JSON](../docs/data/stage2_v3_three_flavour_score_1091peak/three_flavour_score_scan.json). It uses already scored, one-candidate-per-row Stage 2 v3 Parquet shards; no new reconstruction or training is performed here.

From the repository root, with the EOS outputs mounted and `myenv` available:

```bash
mkdir -p /tmp/v3_three_flavour_score_scan_1091peak
env -u PYTHONPATH -u PYTHONHOME myenv/bin/python \
  studies/reconstruction/scan_v3_three_flavour_score.py \
  --output-dir /tmp/v3_three_flavour_score_scan_1091peak --workers 16
```

Verify the manifest's catalog/model/config hashes and the old-score peak cutflow against the [fixed-score six-component review](../docs/STAGE2_V3_ZCC_ZSS_AND_VETO_REVIEW_2026-10-04.md). Preserve `three_flavour_score_scan.json` under `docs/data/stage2_v3_three_flavour_score_1091peak/` and its two PNGs under the matching `docs/figures/` directory. The script scans each unique surviving observed score exactly; the plotted grid is only a display interpolation. Four paired scenarios are included: Armenteros, Armenteros+η, Armenteros+π⁰, Armenteros+π⁰+η. For each scenario read `choices.*.validation_maximum` and `choices.*.test_at_validation_choice`; never choose a threshold from the test maximum.

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

# Reproduce the v3 Zss post-BDT ancestry audit

This is a truth-only diagnostic **after** reconstructed candidate building,
offline selection, frozen BDT scoring and the paired reconstructed vetoes.
It uses all 1,200 archived v3 Zss chunks and the same 5.4–5.9 GeV peak
window, model score and branching scenario as the
[light-flavour comparison](../docs/STAGE2_V3_ZCC_ZSS_AND_VETO_REVIEW_2026-10-04.md).
The [focused PI review](../docs/STAGE2_V3_ZSS_ANCESTRY_ARMENTEROS_2026-10-04.md)
contains the interpretation and linked plots.

From the repository root:

```bash
BASE=/eos/lhcb/lbdt3/user/rquaglia/fcc_ee/lblgamma/outputs
ZSS="$BASE/stage2_v3_zcc_zss_1200_bdt1091peak/v3_zss_1200_bdt1091peak"
PROJECTION="$BASE/stage2_v3_incremental/projections/20261004_1091chunks_peak_5p4_5p9/projection.json"

env -u PYTHONPATH -u PYTHONHOME MPLCONFIGDIR=/tmp/rquaglia_mplconfig \
  XDG_CACHE_HOME=/tmp/rquaglia_cache myenv/bin/python \
  studies/reconstruction/study_v3_zss_ancestry.py \
  --zss-summary "$ZSS/summary.json" --projection "$PROJECTION" \
  --config config/v3_post_bdt_veto_sequence.json --workers 16 \
  --output-dir /tmp/v3_zss_ancestry_1200_bdt1091peak
```

The script checks the complete archived summary, all 1,200 BDT tables,
candidate row count, unique source/event/slot keys, score and model identity.
It writes `zss_ancestry.json` and two linear-scale raw-count PNGs. Its
truth classes follow the existing
`study_v3_post_bdt_armenteros.py` ancestry definition. The output figures
and JSON are frozen under `docs/figures/` and `docs/data/` with the same
`stage2_v3_zss_ancestry_1200_bdt1091peak` label. No selection uses truth.

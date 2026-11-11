# Reproduce v3 Zbb/Zcc/Zss feature comparisons

Run from the repository root with the archived Stage 2 tables mounted at the
paths in the [PI review](../docs/STAGE2_V3_FLAVOUR_FEATURES_2026-10-04.md).
The script reads only the columns needed for plots, processes shards with 16
threads, and accumulates fixed-bin histograms without loading all candidate
tables into one frame. The full-catalogue processing here was explicitly
requested by the PI; no new simulation or reconstruction is run.

```bash
env -u PYTHONPATH -u PYTHONHOME MPLCONFIGDIR=/tmp/rquaglia_mplconfig \
  XDG_CACHE_HOME=/tmp/rquaglia_cache myenv/bin/python \
  studies/reconstruction/compare_v3_flavour_features.py \
  --config config/v3_post_bdt_veto_sequence.json \
  --catalog docs/data/stage2_v3_bdt_1091_peak/20261003_1091chunks.json \
  --workers 16 --output-dir /tmp/v3_flavour_feature_comparison_1091peak
```

The default `--base` is
`/eos/lhcb/lbdt3/user/rquaglia/fcc_ee/lblgamma/outputs` and the default
`--projection` is the frozen 20261004 1091-chunk peak projection under that
base. Supply either explicitly if the archive is mounted elsewhere. The
script checks the Zbb catalog shard set, complete Zcc/Zss summaries, model
and score identity, and all four offline/BDT aggregate row counts against
their frozen summaries. It writes `flavour_feature_comparison.json` and 12
PNG figures. The frozen copies are under `docs/data/` and `docs/figures/`
with the `stage2_v3_flavour_features_1091peak` label.

The JSON records the source hashes, FCCAnalyses revision, signal and
background factors, processed-event denominators, candidate counts, 5.4–5.9
GeV peak counts, histogram edges and full raw bin contents. Feature plots
are class-normalized candidate distributions; physically scaled mass/angle
and score-tail plots use the separate input-event denominators. Truth is a
reporting label only. The existing BDT score and veto windows are unchanged.

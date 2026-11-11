# Reproduce full v3 Zcc and Zss Stage 2 and fixed BDT outputs

These samples already have native Condor Stage 1 ROOT outputs. The input
campaigns use the same v3 reconstruction schema as frozen Zbb; the job
directories, EOS paths and Stage 1 submission commands are in
[the Stage 1 guide](stage1.md). Do not relabel an older tuple as v3.

From the repository root, freeze one catalog per flavour. The 1,200 named
chunks in each directory are independently header-checked, including ROOT
processed-event counters, candidate-bearing event counters, branch count,
schema hash and job-script input-file uniqueness. The `--workers 12` option
performs concurrent header reads but writes a sorted deterministic catalog.

```bash
BASE=/eos/lhcb/lbdt3/user/rquaglia/fcc_ee/lblgamma/outputs
CATDIR=outputs/analysis/studies/stage2_v3_zcc_zss_20261004/catalogs
mkdir -p "$CATDIR"

env -u PYTHONPATH -u PYTHONHOME myenv/bin/python \
  studies/reconstruction/catalog_condor_zbb_chunks.py \
  --job-dir external/FCCAnalyses/BatchOutputs/2026-10-02_07-58-25/p8_ee_Zcc_ecm91 \
  --root-dir "$BASE/zcc_full_condor/native_batch_3d_activity_v3/p8_ee_Zcc_ecm91" \
  --workers 12 --output "$CATDIR/zcc_1200_v3.json"

env -u PYTHONPATH -u PYTHONHOME myenv/bin/python \
  studies/reconstruction/catalog_condor_zbb_chunks.py \
  --job-dir external/FCCAnalyses/BatchOutputs/2026-10-02_07-59-58/p8_ee_Zss_ecm91 \
  --root-dir "$BASE/zss_full_condor/native_batch_3d_activity_v3/p8_ee_Zss_ecm91" \
  --workers 12 --output "$CATDIR/zss_1200_v3.json"
```

The full catalogs contain 1,200 valid chunks each with no missing IDs or
invalid ROOT files. Zcc covers **499,786,495** processed input events and
Zss **499,842,440**; each has the same 474-branch v3 schema hash as Zbb.
The tracked frozen copies are under `docs/data/stage2_v3_zcc_zss_1200/`.

The bounded 1,000-output-event pilot for each flavour used a distinct
`/tmp/v3_zcc_trial_1000_bdt1091peak` or Zss directory with
`--max-chunks 1 --max-output-events 1000 --workers 1`. After it passed,
run the full catalog without either trial cap:

```bash
MODEL="$BASE/stage2_v3_incremental/models/20261004_1091chunks"
PROJECTION="$BASE/stage2_v3_incremental/projections/20261004_1091chunks_peak_5p4_5p9/projection.json"

env -u PYTHONPATH -u PYTHONHOME myenv/bin/python \
  studies/reconstruction/score_v3_inclusive_flavour_catalog.py \
  --catalog "$CATDIR/zcc_1200_v3.json" --model-dir "$MODEL" \
  --projection "$PROJECTION" --workers 12 \
  --output-dir /tmp/v3_zcc_1200_bdt1091peak

env -u PYTHONPATH -u PYTHONHOME myenv/bin/python \
  studies/reconstruction/score_v3_inclusive_flavour_catalog.py \
  --catalog "$CATDIR/zss_1200_v3.json" --model-dir "$MODEL" \
  --projection "$PROJECTION" --workers 12 \
  --output-dir /tmp/v3_zss_1200_bdt1091peak
```

Each chunk publishes `audit.parquet`, `offline_selected.parquet`,
`bdt_selected.parquet` and a manifest atomically. A rerun validates hashes,
row counts, input ROOT identity, model/config hashes, and the validation-fixed
score before reusing a chunk. The audit preserves unselected candidates;
the selected tables keep one candidate per source/event/slot key. Truth is a
diagnostic label only. The resulting `summary.json` gives independent
processed-event denominators and per-stage candidate counts for each flavour.
To project a physical yield use the [PDG Z-boson listing](https://pdg.lbl.gov/2025/listings/rpp2025-list-z-boson.pdf)
and the tracked [branching scenario](../config/v3_post_bdt_veto_sequence.json):
`N_Z × B(Z→qq) × nonmatched selected candidate rows / processed input events`.
The Zss 15.6% fraction is a down-type average used as a flavour-symmetry
scenario; it is not a direct ss-only measurement.

The completed full summaries are frozen at
[`docs/data/stage2_v3_zcc_zss_1200/`](../docs/data/stage2_v3_zcc_zss_1200/)
and the complete per-chunk audit, offline-selected and BDT-selected tables
are archived at
`/eos/lhcb/lbdt3/user/rquaglia/fcc_ee/lblgamma/outputs/stage2_v3_zcc_zss_1200_bdt1091peak/`.
After processing, copy the two entire `/tmp/v3_*_1200_bdt1091peak`
directories there and verify that each archived `summary.json` matches the
tracked summary byte-for-byte and that each archive has 1,200 chunk
manifests. The Zcc and Zss full summaries respectively record 469 and 1,221
nonmatched BDT candidate rows in the provisional 5.4–5.9 GeV window. Use
[`v3_post_bdt_veto_sequence.md`](v3_post_bdt_veto_sequence.md) for the
linear expected mass and cos θp comparison with all backgrounds.
For the current archive, both summary comparisons and 1,200-manifest counts
passed; the first and last chunk of each flavour also passed all three
Parquet SHA-256 checks against its archived manifest.

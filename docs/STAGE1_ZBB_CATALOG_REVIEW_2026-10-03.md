# Stage 1 v3 Zbb Condor catalog refresh — PI review (3 October 2026)

## Question and scope

Which additional native Condor Zbb Stage 1 outputs are usable, and what is
their processed-event denominator? This checks already produced ROOT files;
it changes no reconstruction or offline selection. The reference is the
2026-10-02 463-chunk catalog of the same v3 campaign.

## Inputs and exact check

- Campaign ROOT directory:
  `/eos/lhcb/lbdt3/user/rquaglia/fcc_ee/lblgamma/outputs/zbb_full_condor/native_batch_3d_activity_v3/p8_ee_Zbb_ecm91/`.
- Job scripts:
  `external/FCCAnalyses/BatchOutputs/2026-10-02_07-46-37/p8_ee_Zbb_ecm91/`;
  1,200 scripts assign 4,398 distinct Winter2023 IDEA Zbb source ROOT files.
- Earlier catalog:
  `outputs/analysis/studies/stage2_v3_incremental_20261002/zbb_catalog_20261002.json`.
- New frozen catalog:
  `outputs/analysis/studies/stage2_v3_incremental_20261002/zbb_catalog_20261003.json`
  (SHA-256 `73a482b47fee1f5e72c408181211f06699ba52308ca4bd0e59082d9d63c452d3`).
- Current repository HEAD: `fca7890d347122158f211112d963bedcfc4331ad`;
  local FCCAnalyses HEAD: `0315db1e2941e2886813cb645193e348f3863d5d`.
  These are inspection-time revisions; the submitted scripts do not pin a
  source/config commit. The catalog script SHA-256 is
  `0f99a9d57bfedd94fcb31ac52785e09baa7cb47b606092e99308b72fb297e5df`.
  Current Stage 1 config and observable config SHA-256 values are
  `b872906ad0b25f94299c2ba627b0804d558c407134ca01f3e212c638e6cffa18`
  and `d0ebc4c1b8c3bfdc409515bf6e0c5fd8df5892b53fd7798ec8789484d5d9e3df`.
  The job wrapper's current SHA-256 is
  `adde26b2b5f20b3af3d1836a959836e3ecac6ade8a485cfb64b97751d27e0a67`.
  The centrally produced Delphes card revision is not established by this
  catalog; the named Winter2023 IDEA source files are retained in its mapping.

From the repository root:

```bash
env -u PYTHONPATH -u PYTHONHOME myenv/bin/python \
  studies/reconstruction/catalog_condor_zbb_chunks.py \
  --job-dir external/FCCAnalyses/BatchOutputs/2026-10-02_07-46-37/p8_ee_Zbb_ecm91 \
  --root-dir /eos/lhcb/lbdt3/user/rquaglia/fcc_ee/lblgamma/outputs/zbb_full_condor/native_batch_3d_activity_v3/p8_ee_Zbb_ecm91 \
  --output outputs/analysis/studies/stage2_v3_incremental_20261002/zbb_catalog_20261003.json
```

The script reads ROOT headers and branch types for every present chunk. It
requires `eventsProcessed >= eventsSelected`, and `eventsSelected` to equal
the `events` tree entries. It checks duplicate source assignments and ROOT
files without a matching job script. It does not process input events or
repeat candidate reconstruction. A newly added chunk, 508, was separately
opened to confirm representative v3 branches: `event_entry`, `n_lb`,
`lb_mass`, `lb_truth_matched`, `lambda0_iso_R20_all_n`,
`gamma_combo_same_hemi_all_mass`, and
`reco_mc_greatgreatgrandparent_pdg`; all were present.

## Results and denominators

| Snapshot | Valid ROOT chunks | Processed Zbb input events | Candidate-bearing Stage 1 output events |
|---|---:|---:|---:|
| Earlier 2026-10-02 | 463 | 184,858,989 | 2,310,847 |
| Added in this scan | 166 | 66,061,974 | 825,165 |
| New 2026-10-03 total | 629 | 250,920,963 | 3,136,012 |

All 463 earlier chunk records are unchanged in the new catalog: chunk ID,
ROOT path and size, job script and input list, counters, branch count and
schema signature. No earlier chunk disappeared. All 629 valid chunks share
branch/type SHA-256
`8be4dbee92339c54fba50c760b61bb1e045a3f2bf246f524516cbfbe359d1eb7`.
There are no invalid ROOT chunks. The scan found no ROOT file for 571 of
the 1,200 job IDs. The observed candidate-bearing output-event fraction is
3,136,012/250,920,963 = 1.2498%; it is an event fraction for this partial
campaign, not a candidate-combination rate. Candidate rows, direct truth
matches, wrong combinations, and offline-cut retention were not counted in
this header-level check. No forced-sample count is used to infer a physical
Zbb yield.

## PI review point

Use this catalog only as a frozen partial-campaign input for a named
downstream comparison, with its own input-event denominator. The remaining
571 job IDs need a later catalog scan; a complete-campaign claim requires
1,200 valid chunks and zero missing or invalid IDs. Before interpreting a
selection or BDT effect, count candidate rows and separate direct truth
matches from other Zbb combinations on the same catalog, then compare to
the unchanged Stage 1 baseline. The PI decides whether any offline change
becomes a reference selection.

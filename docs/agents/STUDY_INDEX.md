# Study and artifact index

This index distinguishes the active v3 path from historical studies. Detailed
commands remain in the linked stage guides; counts below are snapshot counts,
not final physics yields.

| Stage | Active scenario and output | Evidence and next action |
|---|---|---|
| 0: forced generation | Named PHSP and HELAMP decay files in `evtgen/`; EDM4hep inputs under `outputs/delphes/` or the recorded EOS paths | `howto/delphes_production.md`; validate a new decay chain before full production. |
| 1: direct v3 | `/eos/lhcb/lbdt3/user/rquaglia/fcc_ee/lblgamma/outputs/stage1_v3_my_run/` | `howto/stage1.md`; three existing ROOT basenames lack `_v3`, so use full paths and do not rename inputs used by Stage 2. New outputs use `_stage1_v3.root`. |
| 1: inclusive Zbb v3 | `.../zbb_full_condor/native_batch_3d_activity_v3/p8_ee_Zbb_ecm91/` | `studies/reconstruction/catalog_condor_zbb_chunks.py`; frozen 1,028/1,200 valid chunk snapshot at `outputs/analysis/studies/stage2_v3_incremental_20261002/catalogs/20261003_1028chunks.json`. Refresh as jobs finish. |
| 2: active v3 | `/eos/lhcb/lbdt3/user/rquaglia/fcc_ee/lblgamma/outputs/stage2_v3_incremental/` | `howto/stage2.md`; default is Λ⁰ ±12.5 MeV, Λb energy ≥10.5 GeV, no photon veto. Preparation, training, test projection and the PI plots cover all 1,028 frozen chunks; see `docs/STAGE2_V3_BDT_REVIEW_2026-10-03.md`. No BDT score is adopted yet. |
| 2: refreshed peak scan v3 | 1,091/1,200 validated Zbb chunks, new model and provisional 5.4–5.9 GeV peak objective | [PI review](../STAGE2_V3_BDT_PEAK_REVIEW_2026-10-04.md), figures and frozen scan data. The independent-test central purity is 32.3% in the peak at the validation-fixed score; no new score is adopted yet. |
| 2: post-BDT K⁰S study | Same frozen 1,028-chunk model and score ≥0.9787055254 | `docs/STAGE2_V3_ARMENTEROS_REVIEW_2026-10-03.md` and `howto/v3_post_bdt_armenteros.md`; a proposed Armenteros box suppresses K⁰S pairs with about 20% signal loss. It is not an adopted reference cut. |
| 2–3: PHSP angle response v3 | 100k PHSP events, existing Stage 1 v3 tuple, frozen 1,028-chunk BDT score | [PI review](../STAGE2_V3_PHSP_ANGLE_REVIEW_2026-10-04.md), [reproduction guide](../../howto/v3_phsp_angle_acceptance.md), and linked plots/fit response; 100,007 generated direct decays, 26,429 unique direct decays after the BDT. This response applies to this fixed-score scenario. |
| 2–3: PHSP angle after Armenteros proposal | Same 100k PHSP sample and frozen BDT plus the reconstructed broad box | [PI review](../STAGE2_V3_PHSP_ARMENTEROS_ANGLE_REVIEW_2026-10-04.md) and [reproduction guide](../../howto/v3_phsp_armenteros_acceptance.md); 20,149 unique direct decays survive and the angular retention varies strongly. The veto remains a proposal. |
| Historical v2 | `config/lb_stage1_v2_samples.json`, v2 ROOT and Parquet outputs | `docs/STAGE1_V2_FULL_REPROCESS_REVIEW_2026-10-01.md`; retain for paired historical comparison. |
| Historical BDT/NN | `docs/BDT_WORKFLOW.md`, `docs/NN_REVIEW_2026-09-29.md` | Separate older reconstruction and feature scenarios; do not mix with v3 yields. |

The 1,028-chunk catalog covers 376,723,929 processed Zbb input events and
4,710,435 candidate-bearing Stage 1 output events. It has one ROOT schema,
no invalid chunks, and 172 missing job IDs. The Stage 2 summary records
1,060,544 selected nonmatched Zbb candidates and 54,872 selected direct
signal candidates from 100,000 forced Physics events. Earlier catalog reviews remain
valid for their frozen subsets.

The current XGBoost scan and later Zcc/Zss mixture gates are in
`docs/agents/BDT_ITERATIONS.md`.

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
| 0–2: Λη and Λπ⁰ physics backgrounds v3 | 100k events per HELAMP mode, one-photon Stage 1 v3 and frozen 1,091-chunk BDT score | [PI review](../STAGE2_V3_PSEUDOSCALAR_BACKGROUNDS_2026-10-04.md), [reproduction guide](../../howto/v3_pseudoscalar_backgrounds_100k.md), figures and [study manifest](../data/stage2_v3_pseudoscalar_100k_bdt1091peak/study_manifest.json). The forced-mode peak estimates are separate from inclusive Zbb pending overlap review. |
| 1–2: inclusive Zcc/Zss v3 | 1,200/1,200 valid chunks per flavour; 499,786,495 Zcc and 499,842,440 Zss processed input events; fixed 1,091-chunk BDT | [PI review and linear mass/angle plots](../STAGE2_V3_ZCC_ZSS_AND_VETO_REVIEW_2026-10-04.md), [full processing recipe](../../howto/v3_zcc_zss_full_processing.md), [veto plot recipe](../../howto/v3_post_bdt_veto_sequence.md), [Zcc and Zss summaries](../data/stage2_v3_zcc_zss_1200/). Zss uses the 15.6% down-type average as a named branching scenario. |
| 2: Zss ancestry after v3 BDT | Same full 1,200-chunk Zss score and paired Armenteros/π⁰/η sequence | [Truth-origin PI review](../STAGE2_V3_ZSS_ANCESTRY_ARMENTEROS_2026-10-04.md), [reproduction guide](../../howto/v3_zss_ancestry_armenteros.md), raw-count figures and JSON. The broad box removes 242/273 K⁰S fakes, while true Λ pairs dominate the survivors. |
| 2: Zss displacement scan after v3 BDT | Same frozen signal/Zbb/Zcc/Zss and veto sequence; reconstructed Λ impact-parameter significance | [Paired PI review and figures](../STAGE2_V3_DISPLACEMENT_ZSS_2026-10-04.md), [reproduction guide](../../howto/v3_displacement_zss.md), [frozen scan](../data/stage2_v3_displacement_zss_1091peak/displacement_scan.json). Threshold 5 retains 65.8% of signal and 25.7% of Zss peak rows; exploratory only. |
| 2: three-flavour BDT feature comparison | Same v3 offline selection and frozen 1,091-chunk BDT; 1,091 Zbb, 1,200 Zcc and 1,200 Zss shards | [PI review and 12 figures](../STAGE2_V3_FLAVOUR_FEATURES_2026-10-04.md), [streaming recipe](../../howto/v3_flavour_feature_comparison.md), [raw histogram JSON](../data/stage2_v3_flavour_features_1091peak/flavour_feature_comparison.json). Final projected peak is 69.4% Zss among inclusive backgrounds; compare a mixed model and Λ-d0 feature by held-out ablation. |
| 2: three-flavour BDT score reoptimization | Same Zbb-trained v3 model; physical Zbb+Zcc+Zss peak; Armenteros-only validation score 0.991889 for PI-requested S/√B (earlier 0.985562 for S/√(S+B)) | [Updated PI review with figures](../STAGE2_V3_THREE_FLAVOUR_SCORE_REOPTIMIZATION_2026-10-04.md), [PI deck](../../presentations/v3_analysis_review_20261004/v3_analysis_review_20261004.pdf), [reproduction guide](../../howto/v3_three_flavour_score_reoptimization.md), [new scan/PHSP/stack outputs](../data/stage2_v3_three_flavour_sqrtb_1091peak/). Held-out central S/√B rises 166.7→234.0; PHSP acceptance is 10.96%. Score remains a proposal. |
| 2–3: PHSP angle response at refreshed score | 100k PHSP events, existing Stage 1 v3 tuple, 1,091-chunk BDT with optional post-BDT Armenteros proposal | [PI review](../STAGE2_V3_PHSP_ANGLE_BDT1091_REVIEW_2026-10-04.md), [guide](../../howto/v3_phsp_angle_acceptance.md), response JSON/CSV and figures. The BDT-only direct efficiency is 35.99% of generated decays; the box proposal gives 26.32%. |
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

# PI review: three-flavour score reoptimization

**Question.** Does the 1,091-chunk Zbb-trained XGBoost need a different score threshold when the expected peak background includes inclusive Zbb, Zcc and Zss? What do reconstructed Armenteros and photon-pair vetoes do to that optimum?

## Correct optimization objective and operating point

**PI correction.** The score must maximize **S/√(S+Bbb+Bcc+Bss)**, with the reconstructed Armenteros rejection applied and each inclusive background scaled separately to the same 6×10¹²-Z exposure. The intervening S/√B scan used the wrong objective for the selection decision. Its 0.9918887 threshold is retained only as a high-score diagnostic, **not** the recommended optimum. The Zbb-trained BDT model and its 20 inputs have not changed.

The exact observed-score **validation** maximum for Armenteros only is **score ≥0.9855620861**. The same 5.4–5.9 GeV reconstructed peak, candidate rows and generated/processed denominators are used at every point. The held-out test is evaluated at the validation-selected threshold. Values below are expected peak candidates; FoM values are central counting estimates, rounded for display.

| Partition and score | Direct S | Combined B | S/√(S+B) | Raw peak S; bb,cc,ss |
|---|---:|---:|---:|---|
| Validation, old .953827 | 230,595 | 2,204,892 | 147.8 | 2,822; 2,38,86 |
| Validation, **selected .985562** | **151,496** | **488,793** | **189.3** | 1,854; 1,5,21 |
| Validation, diagnostic .991889 | 108,352 | 243,891 | 182.6 | 1,326; 1,1,11 |
| Test, old .953827 | 229,215 | 1,889,954 | 157.5 | 5,615; 7,56,150 |
| Test at selected .985562 | **148,265** | **573,242** | **174.5** | 3,632; 1,9,53 |
| Test at diagnostic .991889 | 106,504 | 207,073 | 190.2 | 2,609; 0,4,19 |

The diagnostic .991889 point has a higher *observed test* FoM, but its validation FoM is lower than the exact validation maximum. Selecting a new threshold from this already inspected test tail would use the test sample for tuning. Sparse high-score background makes the exact optimum uncertain: at .985562, validation has only 1 Zbb, 5 Zcc and 21 Zss peak rows; at .991889 it has 1, 1 and 11. A fresh independent tail or more MC is required before claiming a stable operating point.

At the validation-selected .985562 threshold, the full descriptive archive projects **152,080 direct signal** and **547,565 combined inclusive background** peak candidates: Zbb 20,474, Zcc 66,434 and Zss 460,657. Wrong signal combinations add 629 expected candidates outside the exact optimization objective. On 100,007 generated direct PHSP decays, score .985562 plus Armenteros selects **16,050 (16.05%)**, compared with 26.32% at the old .953827 score. Use the [binned PHSP acceptance](data/stage2_v3_three_flavour_score_1091peak/phsp_reoptimized_acceptance_for_fit.csv), not a flat efficiency, for the angular fit.

The [correct S/√(S+B) scan](figures/stage2_v3_three_flavour_score_1091peak/three_flavour_fom_score_scan.png), [full scan manifest](data/stage2_v3_three_flavour_score_1091peak/three_flavour_score_scan.json), [stacked mass and angle view](figures/stage2_v3_three_flavour_score_1091peak/reoptimized_arm_only_stack.png), and [PHSP acceptance plot](figures/stage2_v3_three_flavour_score_1091peak/phsp_reoptimized_acceptance.png) are the selection evidence. The separate [S/√B archive](data/stage2_v3_three_flavour_sqrtb_1091peak/three_flavour_score_scan.json) documents the superseded objective and must not be used as the selection prescription.

## Alternative post-BDT reconstructed Λ impact-parameter cut

The previous [Zss displacement study](STAGE2_V3_DISPLACEMENT_ZSS_2026-10-04.md) found useful rejection at **|lambda_d0_sig| ≥ 5** after Armenteros and the photon-veto sequence. We added that same reconstructed cut as an **alternative after the frozen BDT**, with and without the η veto; it is not a training input and does not alter the model. The candidate column is the absolute Λ trajectory impact-parameter significance, with nonfinite values rejected. The score was reoptimized separately for each branch on validation using the corrected **S/√(S+Bbb+Bcc+Bss)** peak objective. This is a paired comparison on the same scored v3 candidate rows; all three inclusive background components retain their physical scaling.

| Armenteros branch; partition at validation-selected score | Score | Direct S | Zbb | Zcc | Zss | Combined B | S/√(S+B) | Raw peak S; bb,cc,ss |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| No added IP cut; validation | .985562 | 151,496 | 23,453 | 71,991 | 393,348 | 488,793 | 189.3 | 1,854; 1,5,21 |
| **+ Λ IP significance ≥5; validation** | **.981096** | **109,823** | **0** | **57,593** | **112,385** | **169,978** | **207.6** | 1,344; 0,4,6 |
| No added IP cut; test | .985562 | 148,265 | 11,223 | 65,086 | 496,933 | 573,242 | 174.5 | 3,632; 1,9,53 |
| **+ Λ IP significance ≥5; test** | **.981096** | **108,260** | **11,223** | **7,232** | **121,889** | **140,344** | **217.1** | 2,652; 1,1,13 |
| + IP and η; test control | .981098 | 96,217 | 11,223 | 7,232 | 103,137 | 121,591 | 206.2 | 2,357; 1,1,11 |

The added IP branch increases the held-out central FoM by **24.4%** relative to the no-IP Armenteros branch at their independently validation-selected scores. Its full-archive descriptive peak expectation is **110,114 direct signal**, **18,199 Zbb**, **30,329 Zcc** and **140,444 Zss** (188,972 inclusive background total), plus 498 wrong signal combinations. Forced Λη and Λπ⁰ remain separate sensitivity estimates, 2,652 and 34 respectively at this point. The [linear stacked mass and angle plot](figures/stage2_v3_three_flavour_splusb_d0sig5_1091peak/reoptimized_arm_only_stack.png) shows these components.

The paired [PHSP acceptance](figures/stage2_v3_three_flavour_splusb_d0sig5_1091peak/phsp_reoptimized_acceptance.png) is **11,883/100,007 generated direct decays = 11.88%** at score .981096 + Armenteros + IP, compared with 16.05% for score .985562 + Armenteros alone. Its central 68% reconstructed-minus-truth cos θp half-width is 0.0115, RMS 0.0788, and 4.93% have |Δcos θp|>0.1. The [fit CSV](data/stage2_v3_three_flavour_splusb_d0sig5_1091peak/phsp_reoptimized_acceptance_for_fit.csv) shows the angular dependence.

The gain is **provisional**. The IP threshold was proposed after inspecting these campaigns, and the validation optimum has just **0 Zbb, 4 Zcc and 6 Zss** peak rows. Its summed upper-background counting diagnostic lowers validation FoM from 207.6 to 143.2, versus 147.7 for the no-IP validation optimum; the held-out upper-background diagnostic is 167.1 versus 149.4. These intervals omit branching, detector and candidate-correlation uncertainties. In particular, the current Λ impact-parameter-significance uncertainty omits Λ direction uncertainty, as noted in the displacement review. A fresh independent high-tail sample and a PV/SV/track-resolution check are needed before adoption. No IP threshold becomes a reference cut from this comparison alone.

Figures and data: [six-scenario score scan](figures/stage2_v3_three_flavour_splusb_d0sig5_1091peak/three_flavour_fom_score_scan.png), [component-yield scan](figures/stage2_v3_three_flavour_splusb_d0sig5_1091peak/three_flavour_peak_yields_score_scan.png), [exact score/weight/count manifest](data/stage2_v3_three_flavour_splusb_d0sig5_1091peak/three_flavour_score_scan.json), [PHSP manifest](data/stage2_v3_three_flavour_splusb_d0sig5_1091peak/phsp_reoptimized_acceptance.json), and [stack manifest](data/stage2_v3_three_flavour_splusb_d0sig5_1091peak/reoptimized_arm_only_stack.json). The [how-to](../howto/v3_three_flavour_score_reoptimization.md) gives the exact commands.

## Frozen comparison

The model and its 20 reconstructed inputs are unchanged. The same v3 offline-selected, scored candidate rows are scanned at every observed score in the reconstructed 5.4–5.9 GeV signal window. The fixed comparison score is 0.9538269639. The signal direct truth flag and background truth labels enter counting only after reconstruction and scoring. The broad reconstructed Armenteros rejection removes candidates with 0.67≤|α|≤0.78 and 0.075≤qT≤0.120 GeV. A same-hemisphere additional photon gives the optional π⁰ (±20 MeV) or η (±50 MeV) veto. Each scenario is paired on identical rows; the π⁰ and η alternatives do not redefine the BDT.

The signal denominator is 100,002 generated direct decays in 100,000 Physics events. Inclusive processed-event denominators are 395,623,929 Zbb, 499,786,495 Zcc and 499,842,440 Zss. Expected candidate weights use 6×10¹² Z, B(Z→bb)=0.15, B(Z→cc)=0.1203 and B(Z→ss)=0.156 as an explicit average-down-type scenario. Signal uses 2×0.10×7.1×10⁻⁶×0.639 per Zbb event. The objective is **S/√(S+B)** with B the sum of the three independently normalized inclusive flavours **inside the peak**. Forced Λπ⁰ and Λη estimates remain separate because they may overlap inclusive Zbb.

Whole Zbb/Zcc/Zss chunks and signal event hashes define training, validation and test partitions. Each partition has its own processed-event or generated-decay denominator, so its expected yield estimates describe the same full 6×10¹²-Z exposure. The threshold is chosen on validation; the test result is evaluated at that frozen threshold. Exact assignments, catalogs, weights, thresholds and intervals are in the [scan JSON](data/stage2_v3_three_flavour_score_1091peak/three_flavour_score_scan.json).

## Result

All values below are *expected peak candidate counts* and central counting-only FoM, rounded for display. The first and third rows in each pair use the old fixed score; the second and fourth use the validation-selected score. Test rows hold the validation score fixed.

| Selection | Score | Validation S | Validation B | Validation FoM | Test S | Test B | Test FoM |
|---|---:|---:|---:|---:|---:|---:|---:|
| Armenteros, old | .953827 | 230,595 | 2,204,892 | 147.8 | 229,215 | 1,889,954 | 157.5 |
| Armenteros, reoptimized | **.985562** | 151,496 | 488,793 | **189.3** | 148,265 | 573,242 | **174.5** |
| Armenteros+η, old | .953827 | 196,439 | 1,861,614 | 136.9 | 195,292 | 1,432,764 | 153.1 |
| Armenteros+η, reoptimized | **.984990** | 136,461 | 451,331 | **178.0** | 133,365 | 500,378 | **167.5** |
| Armenteros+π⁰, reoptimized control | .984588 | 155,010 | 488,793 | 193.2 | 152,306 | 545,114 | 182.4 |
| Armenteros+π⁰+η, reoptimized control | .984588 | 137,605 | 432,600 | 182.2 | 134,549 | 491,002 | 170.1 |

Thus the old score is suboptimal for this central three-flavour objective: the Armenteros-only test FoM rises by 10.9% at the validation-selected threshold. The η veto lowers FoM in both validation and test; an η veto is not supported by this objective. The π⁰-only alternative has a somewhat higher test FoM, but its expected forced-mode background is small under the current branching scenario and its angular acceptance at the new score still needs measurement. At the proposed Armenteros-only score, the full descriptive snapshot contains 18,623 direct signal peak rows, 9 Zbb, 46 Zcc and 246 Zss rows, corresponding to 152,080 signal and 547,565 inclusive background expected peak candidates. Wrong signal combinations contribute another 629 expected peak candidates, excluded from the scan objective.

The high-score tail is sparse: validation has just **1 Zbb, 5 Zcc and 21 Zss** peak rows at the Armenteros-only optimum. Its counting-only background upper interval strongly reduces a conservative FoM, and neither branching nor detector-model systematics are included. Also, these veto alternatives and the test comparison were inspected during this study, so this is a proposal for a fresh frozen confirmation, not an adopted reference cut.

## Acceptance and fit-view check

On the same 100,007 generated direct Λb→Λγ PHSP decays, the old score plus Armenteros selects 26,321 unique direct decays (26.32%); the proposed score plus Armenteros selects **16,050 (16.05%)**. Adding η retains 14,428 (14.43%). The proposed-score Armenteros resolution has central 68% half-width 0.0122 and RMS 0.0899 in reconstructed minus truth cos θp; 6.89% have |Δcos θp|>0.1. Use the [binned acceptance CSV](data/stage2_v3_three_flavour_score_1091peak/phsp_reoptimized_acceptance_for_fit.csv) and its matched [manifest](data/stage2_v3_three_flavour_score_1091peak/phsp_reoptimized_acceptance.json) for any fit, not a flat efficiency.

The [linear stacked mass and angle plot](figures/stage2_v3_three_flavour_score_1091peak/reoptimized_arm_only_stack.png) shows direct signal, wrong combinations and physically weighted inclusive Zbb/Zcc/Zss after the proposed score and Armenteros box. Forced Λη and Λπ⁰ curves are separate sensitivity projections, **not added to the inclusive stack**. Their peak estimates at this point are 3,347 and 39 respectively. This figure is a candidate fit-view template, subject to normalization, sparse-tail and shape-systematic review.

## PI decision and next check

Score .985562 plus Armenteros is the **validation-derived no-IP S/√(S+B) study point**. Adding reconstructed Λ IP significance ≥5 after the BDT gives a separate, higher-central-FoM option at score .981096, with a lower PHSP acceptance and much sparser background tail. The previous .991889 S/√B proposal is superseded. Do not adopt the η veto on current FoM evidence. Compare Zbb-only training with a physically weighted Zbb/Zcc/Zss mixture and a named reconstructed Λ-IP feature ablation on a newly frozen held-out sample. At matched signal efficiency, inspect peak FoM, component shapes, mass sculpting, PHSP angular acceptance and track/PV/SV response assumptions. The π⁰ veto merits a paired PHSP and forced-mode check before a selection decision.

## Figures and reproduction

- [Validation/all/test FoM scans](figures/stage2_v3_three_flavour_score_1091peak/three_flavour_fom_score_scan.png) and [peak component yields versus score](figures/stage2_v3_three_flavour_score_1091peak/three_flavour_peak_yields_score_scan.png)
- [PHSP angular acceptance](figures/stage2_v3_three_flavour_score_1091peak/phsp_reoptimized_acceptance.png) and [reconstructed-minus-truth response](figures/stage2_v3_three_flavour_score_1091peak/phsp_reoptimized_response.png)
- [Expected stacked mass and cos θp](figures/stage2_v3_three_flavour_score_1091peak/reoptimized_arm_only_stack.png), with [plot counts and provenance](data/stage2_v3_three_flavour_score_1091peak/reoptimized_arm_only_stack.json)
- [Exact reproduction recipe](../howto/v3_three_flavour_score_reoptimization.md)
- [33-slide PI presentation PDF](../presentations/v3_analysis_review_20261004/v3_analysis_review_20261004.pdf), [editable Beamer source and figure hashes](../presentations/v3_analysis_review_20261004/README.md)

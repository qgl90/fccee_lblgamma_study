# PI review: three-flavour score reoptimization

**Question.** Does the 1,091-chunk Zbb-trained XGBoost need a different score threshold when the expected peak background includes inclusive Zbb, Zcc and Zss? What do reconstructed Armenteros and photon-pair vetoes do to that optimum?

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

Use score .985562 plus Armenteros as a **provisional study point** for a fresh mixed-background model comparison. Do not adopt the η veto on current FoM evidence. Compare Zbb-only training with a physically weighted Zbb/Zcc/Zss mixture and a named reconstructed Λ-displacement feature ablation on a newly frozen held-out sample. At matched signal efficiency, inspect peak FoM, component shapes, mass sculpting, PHSP angular acceptance and track/PV/SV response assumptions. The π⁰ veto merits a paired PHSP and forced-mode check before a selection decision.

## Figures and reproduction

- [Validation/all/test FoM scans](figures/stage2_v3_three_flavour_score_1091peak/three_flavour_fom_score_scan.png) and [peak component yields versus score](figures/stage2_v3_three_flavour_score_1091peak/three_flavour_peak_yields_score_scan.png)
- [PHSP angular acceptance](figures/stage2_v3_three_flavour_score_1091peak/phsp_reoptimized_acceptance.png) and [reconstructed-minus-truth response](figures/stage2_v3_three_flavour_score_1091peak/phsp_reoptimized_response.png)
- [Expected stacked mass and cos θp](figures/stage2_v3_three_flavour_score_1091peak/reoptimized_arm_only_stack.png), with [plot counts and provenance](data/stage2_v3_three_flavour_score_1091peak/reoptimized_arm_only_stack.json)
- [Exact reproduction recipe](../howto/v3_three_flavour_score_reoptimization.md)
- [28-slide PI presentation PDF](../presentations/v3_analysis_review_20261004/v3_analysis_review_20261004.pdf), [editable Beamer source and figure hashes](../presentations/v3_analysis_review_20261004/README.md)

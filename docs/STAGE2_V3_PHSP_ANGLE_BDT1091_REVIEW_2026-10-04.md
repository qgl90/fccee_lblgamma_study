# PI review: PHSP angular response for the refreshed v3 BDT

**Question.** What generated-angle acceptance and reconstructed-angle
response correspond to the new 1,091-chunk model and its provisional
5.4–5.9 GeV peak-window score? How would the proposed post-BDT
Armenteros veto change them? These are two named fit scenarios, not adopted
reference cuts.

The 100k PHSP generator, existing v3 Stage 1 tuple, offline selection,
generator-to-candidate matching and response definition are documented in
the [earlier fixed-model review](STAGE2_V3_PHSP_ANGLE_REVIEW_2026-10-04.md).
The same 100,007 generated direct decays, with both charge conjugates,
form the denominator here. Stage 1 yields 55,274 unique direct decays;
offline selection yields 54,759. The refreshed model and validation-fixed
score are in the [1,091-chunk BDT review](STAGE2_V3_BDT_PEAK_REVIEW_2026-10-04.md):
model SHA256 `e2890376c7738ca1010758bee765aa62f2425d9c18e2522f08f3b77004de5b66`,
score **≥0.9538269639**. The score was fixed without PHSP input.

| Scenario | Direct candidate rows | Unique direct decays | Cumulative / 100,007 generated direct decays | Conditional from previous |
|---|---:|---:|---:|---:|
| Offline selected | 54,779 | 54,759 | 54.76% | 99.07% of Stage 1 |
| Refreshed BDT | 36,001 | 35,991 | 35.99% | 65.73% of offline |
| BDT plus proposed Armenteros box | 26,330 | 26,321 | 26.32% | 73.13% of BDT |

The box rejects 0.67≤|α|≤0.78 and 0.075≤qT≤0.120 GeV, using only fitted
track kinematics after the BDT. The [baseline acceptance figure](figures/stage2_v3_phsp_angle_100k_bdt1091peak/bdt_acceptance.png)
and [post-box comparison](figures/stage2_v3_phsp_angle_100k_bdt1091peak/bdt_armenteros_acceptance.png)
show large, nonuniform angle dependence. The box retains 98.0% of BDT
selected signal in the most negative truth bin and only 43.2% in the
0.2–0.4 bin. After it, 13,126 Λb and 13,195 anti-Λb direct decays
survive. The box is still a proposal: its Zbb rejection needs independent
validation and its angular-fit cost must be assessed.

For the BDT-only selection, reconstructed minus generated cos θp has
median −3.34×10⁻⁵, central 68% half-width 0.01138 and RMS 0.08450;
5.02% of selected direct decays have |Δcos θp|>0.1. With the box, the
half-width is 0.01141, RMS 0.08603 and the >0.1 tail is 5.76%.
The [BDT migration](figures/stage2_v3_phsp_angle_100k_bdt1091peak/bdt_migration.png)
and [BDT-plus-box migration](figures/stage2_v3_phsp_angle_100k_bdt1091peak/bdt_armenteros_migration.png)
have generated truth bins as rows and reconstructed bins as columns.
Both JSONs include matrices normalized by *all generated decays* in each
truth bin, folding efficiency and migration into a fit response. The
precise per-bin counts and efficiencies are in the fit CSVs.

This model yields more PHSP candidates than the earlier 1,028-chunk
fixed-score scenario, as expected from its different trained score and
working point. Directly substituting an earlier acceptance curve in a fit
would be inconsistent. The nominal BDT selection and Armenteros proposal
should each retain their own response and uncertainty study.

## Results and figures

- [Refreshed BDT acceptance versus generated angle](figures/stage2_v3_phsp_angle_100k_bdt1091peak/bdt_acceptance.png) and [proposed Armenteros change](figures/stage2_v3_phsp_angle_100k_bdt1091peak/bdt_armenteros_acceptance.png)
- [BDT-only migration](figures/stage2_v3_phsp_angle_100k_bdt1091peak/bdt_migration.png) and [BDT-plus-Armenteros migration](figures/stage2_v3_phsp_angle_100k_bdt1091peak/bdt_armenteros_migration.png)
- [BDT acceptance and response JSON](data/stage2_v3_phsp_angle_100k_bdt1091peak/bdt_acceptance_resolution.json) and [fit CSV](data/stage2_v3_phsp_angle_100k_bdt1091peak/bdt_acceptance_for_fit.csv)
- [BDT-plus-Armenteros response JSON](data/stage2_v3_phsp_angle_100k_bdt1091peak/bdt_armenteros_acceptance_resolution.json) and [fit CSV](data/stage2_v3_phsp_angle_100k_bdt1091peak/bdt_armenteros_acceptance_for_fit.csv)

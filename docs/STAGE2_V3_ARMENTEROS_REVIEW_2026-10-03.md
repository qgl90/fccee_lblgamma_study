# PI review: Armenteros suppression of post-BDT K⁰S candidates

**Question.** After the named v3 offline selection and the fixed 1,028-chunk
XGBoost score ≥0.9787055254, do the reconstructed Armenteros variables
suppress K⁰S→π⁺π⁻ pairs assigned a pπ mass hypothesis? What other Zbb
background remains? This is a separate exploratory veto study. Neither the
BDT nor the reference selection has changed.

## Inputs and definitions

The exact input model, projection, and catalog are frozen in
[the BDT review](STAGE2_V3_BDT_REVIEW_2026-10-03.md). They use 100,000
generated signal input events and 1,028 valid native Zbb chunks covering
376,723,929 processed Zbb input events. The offline scenario is
`lambda12p5_lbE10p5_same_hemi_all`: Λ⁰ ±12.5 MeV, Λb energy ≥10.5 GeV,
no photon veto. The BDT score comes from the model's validation choice;
its independent test partition was fixed before this study. Every number
below counts candidates; output events equal candidate counts in these
post-BDT subsets. Input-event denominators remain separate.

Stage 1 saves charge-signed Armenteros
`α=(pL(positive)−pL(negative))/(pL(positive)+pL(negative))` and daughter
`qT` from the fitted track three-momenta. This study applies a symmetric
veto if **0.67≤|α|≤0.78 and 0.075≤qT≤0.120 GeV**. A legacy narrow
illustration (0.70–0.75 and 0.09–0.11 GeV) is retained for comparison.
The cut uses only saved reconstructed `arm_alpha` and `arm_qt`. Candidate
truth fields and ancestry are read afterward for evaluation. “Assigned pπ”
describes the mass hypothesis; it does not claim a measured particle-ID
mistake in Delphes.

## Post-BDT ancestry and veto effect

The full frozen post-BDT Zbb set has **228 nonmatched candidates**: 165
share a genuine K⁰S→ππ parent for the two charged legs, 55 share a genuine
Λ→pπ parent but fail full Λbγ matching, and 8 have another or unmatched
pair. Direct-in-Zbb candidates are kept separate. The K⁰S category is thus
the leading pair-origin contribution at this score. Its photon can have a
different origin; a genuine Λ pair also does not imply a true signal candidate.

| Partition and veto | Direct signal | Nonmatched Zbb | True K⁰S pair among Zbb | Signal kept | Zbb kept |
|---|---:|---:|---:|---:|---:|
| Validation, fixed score | 2,877 | 28 | 19 | — | — |
| Validation, narrow box | 2,652 | 17 | 9 | 92.2% | 60.7% |
| Validation, broad box | 2,324 | 7 | 0 | 80.8% | 25.0% |
| Test, fixed score | 5,719 | 56 | 37 | — | — |
| Test, narrow box | 5,195 | 43 | 25 | 90.8% | 76.8% |
| Test, broad box | 4,568 | 18 | 1 | 79.9% | 32.1% |
| All frozen chunks, broad box | 23,290 / 28,940 | 60 / 228 | 5 / 165 | 80.5% | 26.3% |

In the test partition, the broad box retains 15 of 17 nonmatched genuine
Λ pairs and 2 of 2 other or unmatched pairs. The remaining 18 candidates
are therefore mostly genuine Λ pairs with a photon that fails full direct
Λb→Λγ matching; their photon and parent categories are in the
[machine-readable audit](data/stage2_v3_armenteros_1028/broad_summary.json).
The broad box removes 36/37 test K⁰S fakes while losing 1,151/5,719 direct
signal candidates. The [post-BDT Armenteros plane](figures/stage2_v3_armenteros_1028/broad_plane.png),
[one-dimensional shapes](figures/stage2_v3_armenteros_1028/broad_1d.png),
and [validation/test retention](figures/stage2_v3_armenteros_1028/broad_retention.png)
show the geometrical overlap and cost to signal.

Using the **same** normalization as the frozen BDT review, the test sample
before this veto projects 233,460 signal and 657,999 nonmatched Zbb
candidates, central purity 26.2%. After the broad box it projects 186,474
signal and 211,500 Zbb, central purity **46.9%**. The 95% Poisson interval
for the latter Zbb projection is **125,348–334,261**, based on only 18 test
background candidates; purity using the upper B endpoint is about 35.8%.
This projection excludes Zcc/Zss and other physical backgrounds. The
signal normalization still divides by 100,000 input events although the
generator audit counts 100,002 direct decays; the resulting relative
difference is about 0.002%.

## Decision for the PI

The broader Armenteros box strongly suppresses the dominant K⁰S pair
category at a substantial **20% signal cost**. The narrow legacy box costs
less signal but leaves most test K⁰S fakes. The broad box was explored after
looking at the post-BDT distributions and both partitions, so its test numbers
are **descriptive, not a blinded independent validation of the veto**. The
remaining 18 test Zbb candidates are too few for a stable high-purity claim.
Keep the box as a named proposal; do not adopt it as a reference cut yet.
Next compare it with the alternative ππ-mass K⁰S hypothesis veto on the
same candidates, examine mass and helicity-angle acceptance by charge, and
confirm the chosen definition on newly completed Zbb chunks or a fresh
independent sample. A full background model needs Zcc/Zss normalization too.

Reproduction commands and stage boundaries are in
[howto/v3_post_bdt_armenteros.md](../howto/v3_post_bdt_armenteros.md).

## Results and figures

- [Post-BDT Armenteros plane and proposed veto box](figures/stage2_v3_armenteros_1028/broad_plane.png)
- [Armenteros α and qT projections](figures/stage2_v3_armenteros_1028/broad_1d.png)
- [Signal, Zbb and true K⁰S retention](figures/stage2_v3_armenteros_1028/broad_retention.png)
- [Broad-box counts and truth categories](data/stage2_v3_armenteros_1028/broad_summary.json) and [narrow-box comparison](data/stage2_v3_armenteros_1028/narrow_summary.json)

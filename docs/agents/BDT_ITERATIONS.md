# Stage 2 v3 model sequence for PI review

## Frozen current model

Train Physics Λb→Λγ direct truth matches against nonmatched inclusive Z→bb
Stage 1 v3 candidates after the named `lambda12p5_lbE10p5_same_hemi_all`
offline selection. Use `v3_offline_no_veto_proposal` in
`config/lb_bdt_features.json` (20 reconstructed variables). The input is the
frozen Zbb catalog and its matching prepared candidate tables. Save the
feature order and config hash, model, train/validation/test event and chunk
assignments, ROC, feature rankings, score distributions, and uncut scored
candidate shards. Mass, cos θp, truth, ancestry, and candidate keys are not
training inputs.

The projection code currently uses

```
S = (6e12)(0.15)(2)(0.10)(7.1e-6)(0.639)
    × (direct Physics candidates after cut / generated Physics events)
B = (6e12)(0.15)
    × (nonmatched Zbb candidates after cut / processed Zbb events)
```

Thus its factors are 816,642 and 9e11 respectively. These are expected
**candidate** counts in the full 4.7–6.5 GeV fit interval. It assumes one
forced direct decay per generated Physics event and does not include η/π⁰
feed-down or other physical backgrounds. Verify that assumption with the
Stage 0 generated-chain audit before interpreting S physically.
The frozen 1,028-chunk model, audit and dense score scan are complete in
`docs/STAGE2_V3_BDT_REVIEW_2026-10-03.md`. The forced signal sample has
100,002 direct decays in 100,000 events; the event-normalization difference
is about 0.002%. No score has been adopted as the reference selection.

Scan the validation score with explicit resolution near one. Show S, B,
their 95% counting interval, central and conservative purity, and
`S/sqrt(S+B)` over the scan. The current configured background goal is a
95% upper bound of one million expected Zbb candidates with at least 20
observed validation-background candidates at an eligible point. A candidate
score is fixed using validation only, then checked once on independent test
chunks and generated signal events. The PI reviews the score scan,
mass/angle shapes and uncertainty before adopting a final cut; do not treat
the algorithmic scan choice as an adopted reference selection.
The separate post-score K⁰S ancestry and Armenteros veto comparison is in
`docs/STAGE2_V3_ARMENTEROS_REVIEW_2026-10-03.md`. Its proposed box is also
not an adopted selection; the descriptive test check followed inspection of
the post-BDT distributions.

## Later feature and background iterations

Keep each feature set in `config/lb_bdt_features.json` under a new name and
train a new model on the same frozen candidate sample for an ablation. Compare
held-out performance and mass/angle sculpting at comparable signal efficiency.
Do not use the variable-ranking sample as an independent validation sample.

For Z→cc and Z→ss, first run the **same Stage 1 v3 scenario** on their central
Delphes inputs, freeze separate catalogs, and prepare the same offline
selection. Measure processed-event denominators, candidate rates, ancestry,
and mass/angle shapes separately for Zbb, Zcc, and Zss. Estimate each
physical background with an explicit Z branching fraction and any needed
sample production weights before combining expected yields. Only then define
a new weighted-mixture training scenario. Record whether weights alter the
training loss, the yield projection, or both; keep unweighted per-process
validation/test counts and intervals so a mixture cannot hide a poorly
measured tail. Review genuine direct decays inside inclusive samples and
forced η/π⁰ feed-down separately.

The full 1,200-chunk v3 Zcc and Zss catalogs have now been prepared and
scored with the frozen 1,091-chunk Zbb model. The separate candidate rates,
physical projections, four-step reconstructed veto plots, and finite-sample
intervals are in the [light-flavour PI review](../STAGE2_V3_ZCC_ZSS_AND_VETO_REVIEW_2026-10-04.md).
Zss dominates the current expected peak under the explicit down-type-average
branching scenario. A future mixture model therefore needs a frozen
light-flavour training/test split and new score optimization against all
three inclusive backgrounds; the present BDT and veto cuts remain proposals.

The [paired displacement scan](../STAGE2_V3_DISPLACEMENT_ZSS_2026-10-04.md)
finds additional Zss separation from reconstructed `|lambda_d0_sig|` after
the present veto proposals. The threshold-5 descriptive point is not an
adopted cut. Test it on an independent sample, recompute PHSP angular
acceptance and check PV/SV resolution assumptions before using it in a fit
or treating its same-sample counting metric as an optimization result.

The full [three-flavour feature comparison](../STAGE2_V3_FLAVOUR_FEATURES_2026-10-04.md)
plots offline-selected and high-score Zbb/Zcc/Zss distributions, including
the 5.4–5.9 GeV peak. After the current BDT and veto proposals, physically
scaled inclusive peak background is 4.4% Zbb, 26.2% Zcc and 69.4% Zss.
The current 20 features already contain strong energy, recoil and isolation
separators, while reconstructed absolute Λ trajectory d0 significance is a
specific additional feature candidate. The next named ablation is Zbb-only
20 features versus physical-flavour-mixture 20 features versus mixture plus
Λ d0, using frozen per-flavour held-out chunks and the same signal sample.
Do not infer a trained-model gain from the marginal feature plots alone.

The [three-flavour peak-score scan](../STAGE2_V3_THREE_FLAVOUR_SCORE_REOPTIMIZATION_2026-10-04.md)
now fixes a **provisional** Armenteros-only validation point at 0.985562 on
this unchanged Zbb-trained model. Its independent test central FoM increases
from 157.5 to 174.5 relative to the old 0.953827 score when inclusive
Zbb+Zcc+Zss are weighted into the 5.4–5.9 GeV peak. Validation has only
1/5/21 Zbb/Zcc/Zss rows at the optimum, so the tail is statistically fragile.
The explicit η veto lowers test FoM; a π⁰-only veto is a separate exploratory
control. The PHSP generated-decay acceptance is 16.05% after the provisional
score and Armenteros versus 26.32% at the old score. Preserve these as named
scenarios and compare a newly trained flavour-mixture model at matched signal
efficiency with a fresh held-out tail and angular response before adoption.

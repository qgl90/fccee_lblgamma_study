# PI review: Zbb, Zcc and Zss shapes before mixed-background BDT training

## Question and inputs

Should the next Λb→Λγ BDT train against a mixture of Zbb, Zcc and Zss, and
which additional reconstructed variables deserve a controlled feature test?
This is a distribution study, **not** a new training or selection result.

We use the frozen v3 offline selection (Λ mass ±12.5 MeV, Λb energy ≥10.5
GeV, same hemisphere, no photon veto) and the existing 1,091-chunk Zbb BDT
with score ≥0.9538269639015198. Signal is the truth-matched direct Physics
sample; inclusive backgrounds exclude truth-matched direct decays only for
reporting. No MC identity enters reconstruction, a feature or a cut. Both
charge conjugates are included. The score-tail plot is made before the
proposed Armenteros, π⁰ and η vetoes; the final-stage plots apply those same
three proposals. The provisional reconstructed peak is 5.4–5.9 GeV.

The [reproduction command](../howto/v3_flavour_feature_comparison.md) streams
the full 1,091 Zbb and 1,200 each Zcc/Zss Parquet shards using 16 workers.
It verifies the archive identities, row counts and frozen score against the
Stage 2 summaries. Exact paths, hashes, bin edges, denominators and raw
histograms are in the [frozen JSON](data/stage2_v3_flavour_features_1091peak/flavour_feature_comparison.json).
The common Stage 1 FCCAnalyses revision is
`91c7d6c5a5c8ad5c3848d6d7cf8383e93c9b74e3`; Stage 1 configuration and
card provenance are in the preparation and catalog manifests referenced by
the JSON.

## Results

Input events and candidate rows have distinct denominators. The forced direct
signal has 100,000 generated events and 100,002 generated direct decays;
its counts below are direct reconstructed candidate rows. The three inclusive
sample inputs contain respectively 395,623,929, 499,786,495 and 499,842,440
processed Zbb, Zcc and Zss events.

| Class | Offline-selected candidate rows | BDT rows | BDT + veto rows | Peak rows after BDT + vetoes | Expected peak candidates |
|---|---:|---:|---:|---:|---:|
| Direct signal | 54,872 | 37,802 | 24,434 | 23,849 | 194,757 |
| Nonmatched Zbb | 1,113,719 | 528 | 127 | 27 | 61,422 |
| Nonmatched Zcc | 1,834,608 | 1,720 | 928 | 252 | 363,943 |
| Nonmatched Zss | 2,161,759 | 4,577 | 1,968 | 514 | 962,511 |

The expected counts use 6×10¹² Z, B(Zbb)=0.15, B(Zcc)=0.1203 and the
**assumed** B(Zss)=0.156 down-type average, each divided by its own processed
input events. Signal uses the direct generated-decay denominator and the
branching/fragmentation factors in the configuration. The inclusive background
shares of the **expected peak** are Zbb/Zcc/Zss = 27.4/28.6/43.9% before the
BDT, 15.7/19.3/65.1% after it, and 4.4/26.2/69.4% after the veto proposals.
Thus the Zbb-only training background represents a small fraction of the
current projected surviving peak. The BDT tail and final mass/angle plots
show this directly; these are candidate yields, not fit components or an
independent model validation.

The shape plots normalize **each class to its own candidate count** so that
kinematic differences are visible despite unequal production weights. They
include off-axis and missing values in the denominator. A binned marginal
total-variation distance (TV, 0 for identical and 1 for disjoint histograms)
summarizes selected peak-window shapes; it is not an estimated multivariate
BDT improvement:

| Reconstructed variable, before BDT in peak | In current 20 features? | TV(signal,Zbb) | TV(signal,Zcc) | TV(signal,Zss) |
|---|:---:|---:|---:|---:|
| Λb candidate energy | yes | 0.875 | 0.860 | 0.839 |
| Partial-Z momentum residual | yes | 0.757 | 0.803 | 0.819 |
| Photon R03 isolation ΣE/Eγ | yes | 0.661 | 0.727 | 0.776 |
| **Absolute Λ trajectory d0 significance** | **no** | **0.189** | **0.356** | **0.415** |
| Absolute Armenteros α | no | 0.208 | 0.221 | 0.229 |
| Armenteros qT | no | 0.103 | 0.101 | 0.092 |
| PV-to-Λ-SV flight significance | yes | 0.232 | 0.133 | 0.098 |

The already-used energy, recoil and isolation variables remain strong broad
separators. The Zbb, Zcc and Zss **background shapes** are similar in many
pre-BDT observables, but differ most in Λ d0, flight and recoil. In the final
tail, the Λ flight distributions largely overlap, while absolute Λ d0 still
distinguishes signal from Zcc/Zss. This accords with the [paired displacement
study](STAGE2_V3_DISPLACEMENT_ZSS_2026-10-04.md), without proving that adding
it to a trained BDT will improve the joint decision. The d0 uncertainty omits
Λ direction uncertainty; its apparent advantage needs a detector-resolution
check. The diphoton distance variables already in the BDT also separate
classes; their missing/no-partner state and photon-veto correlations require
care in a retraining comparison.

Figures:

- [BDT score tail: class shapes and physically scaled yields](figures/stage2_v3_flavour_features_1091peak/pre_bdt_score_tail.png)
- [Pre-BDT kinematics](figures/stage2_v3_flavour_features_1091peak/pre_bdt_kinematics.png), [topology](figures/stage2_v3_flavour_features_1091peak/pre_bdt_topology.png), [activity and photon pairing](figures/stage2_v3_flavour_features_1091peak/pre_bdt_activity.png)
- [Pre-BDT signal-peak kinematics](figures/stage2_v3_flavour_features_1091peak/pre_bdt_peak_kinematics.png), [topology](figures/stage2_v3_flavour_features_1091peak/pre_bdt_peak_topology.png), [activity](figures/stage2_v3_flavour_features_1091peak/pre_bdt_peak_activity.png)
- [After BDT and vetoes: kinematics](figures/stage2_v3_flavour_features_1091peak/post_bdt_vetoes_kinematics.png), [topology](figures/stage2_v3_flavour_features_1091peak/post_bdt_vetoes_topology.png), [activity](figures/stage2_v3_flavour_features_1091peak/post_bdt_vetoes_activity.png)
- [Linear physically scaled mass and angle before BDT](figures/stage2_v3_flavour_features_1091peak/pre_bdt_mass_angle_linear.png) and [after BDT plus veto proposals](figures/stage2_v3_flavour_features_1091peak/post_bdt_vetoes_mass_angle_linear.png)
- [PI Beamer deck](../presentations/stage2_v3_flavour_features_1091peak/stage2_v3_flavour_features_1091peak.pdf) with [source and figure hashes](../presentations/stage2_v3_flavour_features_1091peak/README.md)

## Proposed next controlled comparison

Train three named models on the **same frozen v3 offline candidate sample**:
the existing Zbb-only 20-feature baseline; a Zbb/Zcc/Zss mixture with those
20 features; and the same mixture adding reconstructed `|lambda_d0_sig|`.
An Armenteros α/qT pair can be a separate fourth ablation rather than bundled
with d0. Give the background mixture physically motivated relative flavour
weights while setting the *overall signal/background loss balance* explicitly;
do not equate these loss weights with the final yield projection. Freeze
train/validation/test splits by source event and production chunk/seed,
including held-out Zcc and Zss chunks. Compare per-flavour unweighted counts,
peak S/√(S+B) and intervals, mass/angle shapes, and PHSP angular acceptance
at matched direct-signal efficiency. Choose score on validation and open test
once. The PI can then decide whether the mixture and d0 enter the reference.

This study uses the full Zbb sample, including chunks used to train the
existing model; its high-score tail is descriptive. The final Zbb peak has
only 27 candidates. Candidate correlations, normalization and detector
systematics are not in the central projections. No mixed BDT is trained or
adopted by this review.

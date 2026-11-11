# PI review: staged post-BDT Armenteros and photon vetoes

**Question.** With the fixed v3 BDT score, how do a reconstructed-only
Armenteros box, then a π⁰ photon-pair veto, then an η photon-pair veto change
the expected Λb→Λγ signal and the separate Zbb, Λπ⁰ and Λη components in
reconstructed mass and cos θp? Should either photon veto be investigated as
a reference selection?

## Frozen inputs and selection

The [1,091-chunk BDT snapshot](STAGE2_V3_BDT_PEAK_REVIEW_2026-10-04.md)
provides the score **≥0.9538269639**. The same offline selection requires
Λ mass within 12.5 MeV, reconstructed Λb energy ≥10.5 GeV and the same
hemisphere. Signal uses the full 100k Physics sample; Zbb uses all 1,091
frozen v3 chunks, **395,623,929 processed input events**. The η and π⁰
physics-mode samples each have 100k generated events and are documented in
the [separate forced-mode review](STAGE2_V3_PSEUDOSCALAR_BACKGROUNDS_2026-10-04.md).
Both charge conjugates are included. Every cut in this note uses reconstructed
quantities and is applied after the score; truth labels separate direct signal,
signal wrong combinations and nonmatched Zbb only when making the plots.

The sequential proposals are:

1. Fixed BDT only.
2. Reject **0.67≤|α|≤0.78 and 0.075≤qT≤0.120 GeV**, the earlier broad
   [Armenteros proposal](STAGE2_V3_ARMENTEROS_REVIEW_2026-10-03.md).
3. Also reject a candidate when its chosen photon and any other raw type-22
   photon in the same hemisphere have |m(γγ)−m(π⁰)|≤20 MeV.
4. Also reject |m(γγ)−m(η)|≤50 MeV under the same partner definition.

The photon-pair flags and Armenteros variables are saved before any of these
post-BDT cuts. They are defined in the tracked
[offline config](../config/lb_offline_selections.json) and
[normalization scenario](../config/v3_post_bdt_veto_sequence.json).
This is a paired comparison on the same candidate rows at each stage.

## Expected candidates in the provisional 5.4–5.9 GeV signal window

| Sequential stage | Direct Λγ signal | Nonmatched Zbb | Forced Λη | Forced Λπ⁰ | Signal wrong combinations |
|---|---:|---:|---:|---:|---:|
| Fixed BDT | 301,335 | 550,523 | 13,136 | 107 | 1,372 |
| + Armenteros | 231,473 | 79,621 | 9,844 | 84 | 1,053 |
| + π⁰ veto | 228,827 | 79,621 | 9,785 | 66 | 1,013 |
| + η veto | 194,757 | 61,422 | 1,924 | 60 | 841 |

These are **expected candidate rows**, not unique events. The linked JSON
and CSV also give raw candidate rows, candidate-bearing events, conditional
and cumulative retention, and approximate candidate-count intervals at each
step. The direct signal denominator is **100,002 generated direct decays**;
the inclusive Zbb denominator is its **395,623,929 processed input events**.
The forced η and π⁰ modes use **100,000 and 100,005 generated direct decays**
respectively. The exact scaling is

\[
N_{\rm signal}=N_Z\,\mathcal B(Z\to b\bar b)\,2f_{\Lambda_b}\,
\mathcal B(\Lambda_b\to\Lambda\gamma)\,
\mathcal B(\Lambda\to p\pi)\,
\frac{N_{\rm selected\ direct\ candidates}}{N_{\rm generated\ direct\ decays}},
\qquad
N_{Zq\bar q}=N_Z\,\mathcal B(Z\to q\bar q)\,
\frac{N_{\rm selected\ nonmatched\ candidates}}{N_{\rm processed\ input\ events}}.
\]

The [branching scenario](../config/v3_pseudoscalar_branching_scenarios.json)
sets the forced-mode factors, including the daughter γγ branching fractions.
The two forced b-mode estimates are **shown separately from inclusive Zbb**:
those decays can already occur in the inclusive Zbb sample. The curves must
not be added until that overlap is checked.

A post-selection ancestry audit of every one of the 1,091 inclusive Zbb
scored shards found **zero** direct Λη or Λπ⁰ partial-chain candidate rows
after the fixed BDT, versus **528** other nonmatched candidate rows (242 in
the peak). This is an observed count in a finite inclusive sample, not proof
that the physical modes do not overlap its expectation. We therefore retain
the forced-mode curves as separate sensitivity estimates and do not add them
to the inclusive Zbb total. The ancestry check never enters the selection.

## Effect and statistical limit

The Armenteros box retains **76.8%** of direct signal and **14.5%** of
nonmatched Zbb peak candidate rows. The π⁰ veto then retains **98.9%** of
that signal and **77.7%** of the remaining forced Λπ⁰ estimate; at the
present score, no additional Zbb peak candidate is removed in this 1,091
chunk snapshot. The η veto retains **85.1%** of the signal entering it and
**19.7%** of the forced η estimate. These photon-veto results are exploratory
because the windows were inspected after candidate distributions were known.

Only **242** nonmatched Zbb candidate rows are in the peak after the BDT,
falling to **35**, **35**, then **27**. The corresponding approximate 95%
candidate-count interval for the final Zbb projection is
**40,477–89,366** expected candidates; candidate correlations and detector,
normalization, BDT and branching uncertainties are not included. The full
sample curves include BDT training chunks, so they are descriptive shapes
and rates; the independent held-out test projection remains the fixed-score
check. Strong mass and angle changes warrant a new PHSP angular acceptance
and migration response for any veto sequence adopted for a fit.

The linear-scale mass and cos θp panels show the four ordered selections.
Separate feed-down and π⁰ detail figures retain a linear y-axis so those
smaller components remain visible next to Zbb and direct signal. The PI can
compare the sizable extra signal cost of the η veto against its η rejection;
neither photon veto is adopted as a reference cut by this note.

## Results and figures

- [All-component expected mass sequence](figures/stage2_v3_post_bdt_veto_sequence_1091peak_four/sequence_mass_linear.png) and [cos θp sequence](figures/stage2_v3_post_bdt_veto_sequence_1091peak_four/sequence_angle_linear.png)
- [Feed-down mass detail](figures/stage2_v3_post_bdt_veto_sequence_1091peak_four/sequence_mass_detail_linear.png) and [angle detail](figures/stage2_v3_post_bdt_veto_sequence_1091peak_four/sequence_angle_detail_linear.png)
- [π⁰ mass detail](figures/stage2_v3_post_bdt_veto_sequence_1091peak_four/sequence_mass_pi0_linear.png) and [π⁰ angle detail](figures/stage2_v3_post_bdt_veto_sequence_1091peak_four/sequence_angle_pi0_linear.png)
- [Exact counts, scales and intervals](data/stage2_v3_post_bdt_veto_sequence_1091peak_four/summary.json) and [cutflow CSV](data/stage2_v3_post_bdt_veto_sequence_1091peak_four/stage_counts.csv)
- [Inclusive Zbb η/π⁰ ancestry overlap audit](data/stage2_v3_post_bdt_veto_sequence_1091peak_four/zbb_pseudoscalar_overlap.json)

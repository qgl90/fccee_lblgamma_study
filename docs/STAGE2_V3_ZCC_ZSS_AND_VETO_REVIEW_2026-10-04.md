# PI review: inclusive Zcc/Zss and staged post-BDT vetoes

**Question.** At the frozen v3 BDT score, what do Zcc and Zss contribute
relative to direct Λb→Λγ, nonmatched Zbb, and the forced Λπ⁰ and Λη
studies? How do a broad Armenteros rejection, then π⁰ and η photon-pair
vetoes change the expected mass and cos θp distributions? This comparison
asks whether either photon veto merits a dedicated optimization; it does not
adopt a new reference cut.

## Exact samples and scaling

The [frozen 1,091-chunk BDT review](STAGE2_V3_BDT_PEAK_REVIEW_2026-10-04.md)
fixes score ≥0.9538269639015198 after the v3 offline selection (Λ mass
within 12.5 MeV, Λb energy ≥10.5 GeV, same hemisphere). The provisional
reconstructed peak is 5.4–5.9 GeV. The direct signal sample has 100,002
generated decays in 100,000 input events; the inclusive Zbb catalog has
395,623,929 processed input events. The forced η and π⁰ samples have
100,000 and 100,005 generated direct decays respectively. All include both
charge conjugates.

We catalogued and fully processed **all 1,200 valid Stage 1 v3 chunks** of
each light-flavour campaign. Zcc has **499,786,495** processed input events,
5,803,372 candidate-bearing Stage 1 output events, and 7,087,378 candidate
rows in the unselected Stage 2 audit. Zss has **499,842,440**, 5,723,761,
and 6,965,022 respectively. Both match the 474-branch v3 Stage 1 schema;
the separate frozen catalogs and Stage 2 summaries are linked below. The
Stage 2 audit preserves unselected candidates. Truth is attached only as a
post-reconstruction diagnostic; every score and veto uses reconstructed
quantities.

The full per-chunk outputs are archived at
`/eos/lhcb/lbdt3/user/rquaglia/fcc_ee/lblgamma/outputs/stage2_v3_zcc_zss_1200_bdt1091peak/`.
Both archived summaries match their completed local summaries byte-for-byte;
each archive has 1,200 chunk manifests. The first and last chunk of each
flavour passed SHA-256 checks of all three archived Parquet tables against
their manifest hashes. The runner validates hashes of every chunk on reuse.

For each inclusive flavour, the candidate weight is

\[
w_q=\frac{(6\times10^{12})\,\mathcal B(Z\to q\bar q)}
{N_{\rm processed\ input\ events,q}}.
\]

The scenario uses \(\mathcal B(Z\to b\bar b)=0.15\),
\(\mathcal B(Z\to c\bar c)=0.1203\), and
\(\mathcal B(Z\to s\bar s)=0.156\). The [PDG 2025 Z-boson listing](https://pdg.lbl.gov/2025/listings/rpp2025-list-z-boson.pdf)
quotes the cc value directly. Its 15.6% entry is an **average down-type
flavour fraction**, used here as an explicit equal-down-type scenario for
ss, not a direct ss measurement. The resulting weights are 2,274.89 per
nonmatched Zbb candidate, 1,444.22 per nonmatched Zcc candidate, and
1,872.59 per nonmatched Zss candidate. The signal and forced-mode weights
follow the separate [four-component review](STAGE2_V3_POST_BDT_VETO_SEQUENCE_2026-10-04.md).

## Paired four-step comparison

The same candidate rows are tested at each step: fixed BDT only; reject
0.67≤|α|≤0.78 and 0.075≤qT≤0.120 GeV; additionally reject a raw
same-hemisphere photon partner within 20 MeV of the π⁰ mass; additionally
reject one within 50 MeV of the η mass. The cuts and windows are in
[`config/v3_post_bdt_veto_sequence.json`](../config/v3_post_bdt_veto_sequence.json).
The following entries are **expected candidate rows in the 5.4–5.9 GeV
window**, not event counts:

| Sequential stage | Direct Λγ | Nonmatched Zbb | Nonmatched Zcc | Nonmatched Zss | Forced Λη | Forced Λπ⁰ |
|---|---:|---:|---:|---:|---:|---:|
| Fixed BDT | 301,335 | 550,523 | 677,338 | 2,286,433 | 13,136 | 107 |
| + Armenteros | 231,473 | 79,621 | 410,158 | 1,486,837 | 9,844 | 84 |
| + π⁰ veto | 228,827 | 79,621 | 410,158 | 1,308,940 | 9,785 | 66 |
| + η veto | 194,757 | 61,422 | 363,943 | 962,511 | 1,924 | 60 |

Signal wrong combinations are shown in the figures and [exact cutflow](data/stage2_v3_post_bdt_veto_sequence_1091peak_all/stage_counts.csv):
1,372, 1,053, 1,013, and 841 expected peak candidates respectively.
The forced η/π⁰ curves are **separate sensitivity estimates**, since those
modes may be contained in inclusive Zbb. The [truth-only overlap audit](data/stage2_v3_post_bdt_veto_sequence_1091peak_four/zbb_pseudoscalar_overlap.json)
found zero direct η or π⁰ partial-chain candidates after the BDT in this
finite Zbb snapshot; that does not justify adding the forced projections to
the inclusive expectation.

The raw peak rows surviving the BDT are **469 Zcc** and **1,221 Zss**;
after all proposed vetoes, **252 Zcc** and **514 Zss** remain. At the last
step, candidate-count Poisson 95% intervals alone project 320,391–411,762
Zcc and 881,089–1,049,433 Zss expected peak candidates. The corresponding
Zbb interval is 40,477–89,366 from only 27 rows. These intervals omit
candidate correlations, branching inputs, detector and model systematics,
and the fact that this descriptive full sample includes BDT training chunks.
They are not independent score-validation evidence.

The π⁰ veto conditionally retains 98.9% of direct signal and 88.0% of Zss
after Armenteros; its 20 MeV window is exploratory. The η veto then retains
85.1% of direct signal, 88.4% of Zcc and 73.5% of Zss, while retaining
19.7% of the forced η estimate. Under the stated normalization the inclusive
signal fraction \(S/(S+B_{bb}+B_{cc}+B_{ss})\) rises from 7.9% at fixed BDT
to 11.3% after π⁰ and 12.3% after η. This diagnostic is deliberately
exclusive of forced-mode estimates and signal wrong combinations; it is not
a final fit purity. The η veto's substantial signal loss and the large Zss
projection call for a dedicated light-flavour background and angular
acceptance study before any cut or training-mixture change.

The follow-up [Zss ancestry audit](STAGE2_V3_ZSS_ANCESTRY_ARMENTEROS_2026-10-04.md)
shows why the Armenteros reduction is incomplete: most Zss candidates
already contain a genuine Λ pair, and 483/514 final peak candidates still
do. Its truth classes are diagnostic only.

## Results and figures

- [Six-component linear expected mass sequence](figures/stage2_v3_post_bdt_veto_sequence_1091peak_all/sequence_mass_linear.png) and [reconstructed cos θp sequence](figures/stage2_v3_post_bdt_veto_sequence_1091peak_all/sequence_angle_linear.png)
- [Light-flavour/feed-down mass detail](figures/stage2_v3_post_bdt_veto_sequence_1091peak_all/sequence_mass_detail_linear.png) and [angle detail](figures/stage2_v3_post_bdt_veto_sequence_1091peak_all/sequence_angle_detail_linear.png)
- [π⁰ mass detail](figures/stage2_v3_post_bdt_veto_sequence_1091peak_all/sequence_mass_pi0_linear.png) and [π⁰ angle detail](figures/stage2_v3_post_bdt_veto_sequence_1091peak_all/sequence_angle_pi0_linear.png)
- [Four-component mass and angle plots](STAGE2_V3_POST_BDT_VETO_SEQUENCE_2026-10-04.md#results-and-figures) retain visibility of the smaller forced modes and direct signal on a linear scale
- [Six-component exact counts, weights, intervals and run identities](data/stage2_v3_post_bdt_veto_sequence_1091peak_all/summary.json) and [candidate/event cutflow CSV](data/stage2_v3_post_bdt_veto_sequence_1091peak_all/stage_counts.csv)
- [Zcc catalog](data/stage2_v3_zcc_zss_1200/zcc_1200_v3.json), [Zss catalog](data/stage2_v3_zcc_zss_1200/zss_1200_v3.json), [Zcc Stage 2 summary](data/stage2_v3_zcc_zss_1200/zcc_stage2_summary.json), and [Zss Stage 2 summary](data/stage2_v3_zcc_zss_1200/zss_stage2_summary.json)
- [Full processing recipe](../howto/v3_zcc_zss_full_processing.md) and [plot reproduction recipe](../howto/v3_post_bdt_veto_sequence.md)

# PI review: truth origin of the v3 Zss background

**Question.** Is the large projected post-BDT Z→ss background mainly
K⁰S→ππ reconstructed under the pπ hypothesis, and does the proposed broad
Armenteros box suppress it? What remains afterward?

## Frozen comparison and definitions

This audit reads every `bdt_selected.parquet` table from the **1,200/1,200
valid v3 Zss chunks** processed in the
[full light-flavour study](STAGE2_V3_ZCC_ZSS_AND_VETO_REVIEW_2026-10-04.md).
They represent **499,842,440 processed input events**. The upstream offline
selection is Λ mass within 12.5 MeV, Λb energy ≥10.5 GeV and same hemisphere;
the validation-fixed 1,091-chunk model score is
**≥0.9538269639015198**. Both charge conjugates are present. The paired
comparison applies reconstructed cuts to the same candidate rows in this
order: BDT only; Armenteros box; π⁰ photon-pair veto; η photon-pair veto.
The provisional reconstructed Λγ peak is **5.4–5.9 GeV**. Every row in this
peak represents a different candidate-bearing input event in this snapshot.

The Armenteros proposal rejects
**0.67≤|α|≤0.78 and 0.075≤qT≤0.120 GeV**. It uses reconstructed track
momenta only. Truth ancestry is read afterward to label pair and photon
origins; it is never a BDT feature or veto input. A **true Λ pair** requires
the proton and pion MC matches to share one Λ parent and have the expected
p/π identities. A **K⁰S pair** requires both matched tracks to be pions
from the same K⁰S parent, though the candidate assigns one a proton mass.
All other or incomplete matches remain explicit.

## What the Zss candidates are

| Reconstructed stage, peak | All nonmatched Zss rows | True Λ→pπ pair | K⁰S→ππ assigned pπ | Other/unmatched pair |
|---|---:|---:|---:|---:|
| Fixed BDT | 1,221 | 932 | 273 | 16 |
| + Armenteros | 794 | 752 | 31 | 11 |
| + π⁰ veto | 699 | 662 | 27 | 10 |
| + η veto | 514 | 483 | 24 | 7 |

Thus **76.3%** of the initial post-BDT peak candidates already have a
genuine Λ pair; after all proposals this rises to **94.0%**. The broad
Armenteros box removes **242/273 (88.6%)** of the K⁰S-pair fakes, but also
**180/932 (19.3%)** of genuine-Λ background pairs. Total Zss peak
candidate rejection is **427/1,221 (35.0%)** at that step. The matched
direct-signal sample loses **23.2%** of its peak candidates under the same
box (36,900→28,345). These are paired counts, with the same BDT and
mass window at both steps.

The final 514 Zss rows include 456 selected photons classified as other or
unmatched ancestry, 41 from π⁰ and 17 from η. **429** rows combine a true Λ
pair with a photon in the other/unmatched category. The MC parent of the
selected photon is recorded as |PDG|=3 (s quark) in **352/514** final rows;
45 photons have no MC match. For the true-Λ pairs, the Λ parent ancestry is
often recorded as |PDG|=3 (**285/483**), with substantial hyperon feed-down.
These are generator-record labels; a parent s-quark link alone does not
establish a specific photon-production mechanism. This audit supports a
dominant **real Λ plus non-signal photon combination**, not a dominant
K⁰S mass-hypothesis mistake. The photon and Λ can have distinct origins;
the [machine-readable cross-tab](data/stage2_v3_zss_ancestry_1200_bdt1091peak/zss_ancestry.json)
keeps them separate.

Under the [named scaling scenario](../config/v3_post_bdt_veto_sequence.json),
each nonmatched Zss candidate carries weight
\((6\times10^{12})(0.156)/499{,}842{,}440=1{,}872.59\).
The total peak estimate therefore falls from **2.286 million** after BDT to
**1.487 million** after Armenteros. The K⁰S-pair portion falls from about
**511,000 to 58,000** expected candidates. After all four cuts, the total is
**963,000**, of which about **904,000** come from true-Λ pairs and **45,000**
from K⁰S pairs. These are candidate projections, not measured physical
contamination. The 15.6% strange fraction is the explicit equal-down-type
scenario discussed in the full review; detector and generator systematics
are not covered by the candidate-count uncertainty.

For **Zss alone**, the central peak \(S/B_{ss}\) improves from 0.132 to
0.156 after Armenteros, while \(S/\sqrt{S+B_{ss}}\) falls from 187 to 177
because of the simultaneous signal loss. Including Zbb and Zcc at the same
fixed weights gives 154→156 for that simple counting metric. These are
diagnostics at a proposal point, not an optimized or uncertainty-aware fit
objective.

## Interpretation for the PI

The Armenteros box is effective against the K⁰S subset, but it leaves the
dominant Zss mechanism and carries a substantial signal cost. The sequential
π⁰/η vetoes leave mostly true Λ pairs with a selected photon whose immediate
MC parent is neither π⁰ nor η. A sensible next study is to inspect the
matched photon and strange-hadron ancestry and reconstructed kinematics in
these surviving candidates, then test a named discrimination strategy on
signal and independent light-flavour events. No new cut is adopted here.

## Results and figures

- [Raw peak track-pair ancestry through the four cuts](figures/stage2_v3_zss_ancestry_1200_bdt1091peak/zss_peak_pair_origin.png)
- [Selected-photon ancestry through the four cuts](figures/stage2_v3_zss_ancestry_1200_bdt1091peak/zss_peak_photon_origin.png)
- [Exact per-stage counts, photon cross-tabs, top parent PDGs, input and config hashes](data/stage2_v3_zss_ancestry_1200_bdt1091peak/zss_ancestry.json)
- [Reproduction guide](../howto/v3_zss_ancestry_armenteros.md)

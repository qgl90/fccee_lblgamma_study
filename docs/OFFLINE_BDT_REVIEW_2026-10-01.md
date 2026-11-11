# PI review: Lambda ±5 MeV and photon-veto study (1 October 2026)

## Question and current choice

The PI set `|m(pπ)-m(Λ PDG)|<5 MeV` as the default offline Lambda selection
before BDT training. The Lambda-gamma analysis interval is 4.7–6.5 GeV.
No photon veto is included in this default. The pi0, pi0+eta, and minimum
diphoton mass conditions are named optional scenarios in
`config/lb_offline_selections.json`.

## Provenance and denominators

The native stage-1 Physics MC ROOT file is
`/eos/lhcb/lbdt3/user/rquaglia/fcc_ee/lblgamma/outputs/nominal_preselection_100k_signal_physics_reco.root`.
Its `eventsProcessed` counter is 100,000. The stage-1 candidate output has
56,866 candidate-bearing events and 60,593 candidates. The candidate builder
is `analysis/studies/lb2lambda_gamma_baseline.py` called by
`lb2lambda_gamma_reco.py`; Zbb's Condor entry point delegates to the same
`RDFanalysis`. The stage-1 configuration is
`config/lb_reco_preselection_15mev_45_65.json`. The production manifest
records FCCAnalyses `pre-edm4hep1` commit
`91c7d6c5a5c8ad5c3848d6d7cf8383e93c9b74e3` and the detector input.

The first completed frozen Zbb catalog has 679 valid Condor chunks covering
267,510,122 processed central events, 3,337,613 candidate-bearing output
events, and 4,205,178 stage-1 candidates. Its exact ROOT paths, source
lists, processed counters, and schema signatures are in
`outputs/analysis/studies/condor_zbb_chunk_catalog_plots_20261001.json`.
The session's native audit is in
`outputs/analysis/studies/offline_bdt_session_20261001/full679/`.
Its default ±5 MeV derivative is in `lambda5_full679/`. This derivative
uses the **same stage-1 candidates and events** as the parent audit and
preserves all failing candidates with cut flags. The frozen catalog is a
partial Condor campaign, not all 1,200 submitted chunks.

The refreshed catalog available for this session has 1,068 complete,
schema-compatible chunks and 393,638,637 processed Zbb events. The remaining
132 submitted chunks have no valid output in this snapshot. Its catalog is
`offline_bdt_session_20261001/zbb_catalog_current.json`, and the one-pass
native stage-1 audit is `lambda5_all1068/`. The Delphes Physics input has
100,000 generated events containing 100,002 direct target decays (49,998
Lambda_b and 50,004 anti-Lambda_b); two events have two such decays.
The expected-yield formula below uses the requested per-generated-event
denominator of 100,000 and the decay denominator is recorded separately.

At the default ±5 MeV window and 4.7–6.5 GeV Lambda-gamma range, Physics MC
has 54,322 direct truth-matched candidates, 4,035 wrong combinations, and
55,504 candidate-bearing selected events. Thus the direct candidate rate is
54,322/100,000 = 54.322% per generated input event, assuming one forced
target decay per event. The Zbb sample has 2,172,832 other candidates and
1,828,274 events with at least one candidate. Its other-candidate rate is
2,172,832/267,510,122 = 0.0081224 per processed Zbb event; its event
efficiency is 1,828,274/267,510,122 = 0.0068344. Another 435 direct
truth-matched Λb→Λγ candidates in inclusive Zbb are kept in a separate
diagnostic category, not counted as combinatorial background.

Relative to the saved stage-1 ±15 MeV Lambda window *within the 4.7–6.5 GeV
analysis range*, ±5 MeV retains 54,322/55,393 = 98.07% direct Physics
signal candidates and 2,172,832/3,431,085 = 63.33% other Zbb candidates.
These conditional retentions are distinct from generated-event efficiency.

On the refreshed complete-output snapshot, the same ±5 MeV cut retains
3,200,194 nonmatched Zbb candidates in 2,692,117 selected events. The named
raw type-22 pi0 veto reduces this to 1,050,285 nonmatched candidates and
949,756 selected events; another 622 direct-in-Zbb candidates remain a
separate diagnostic category. Direct Physics candidates change from 54,322
to 52,778, with 53,672 selected Physics events after the pi0 veto.
Thus the pi0 cut conditionally retains 97.16% of direct signal and 32.82%
of nonmatched Zbb candidates after the Lambda window. The absolute Zbb
candidate rate is 1,050,285/393,638,637 = 0.0026681 per processed event;
the selected-event efficiency is 949,756/393,638,637 = 0.0024128.

## Photon veto comparison after the default Lambda cut

The paired forced-sample inputs are the 100k Physics and 100k eta-as-gamma
candidate Parquets with both photon partner lists under the EOS outputs
directory. The exact input file hashes, cut definitions, counts, and plots
are in `offline_bdt_session_20261001/feeddown_veto_full679/`. The forced
eta sample is labelled by common generated Lambda and eta ancestry, after
candidate building. Forced eta counts are not a physical Zbb normalization.

| Partner definition and cut | Direct Physics retained / 54,322 | Matched eta feed-down retained / 32,631 | Other Zbb retained / 2,172,832 |
|---|---:|---:|---:|
| Selected same hemisphere, pi0+eta windows | 54,233 | 23,017 | unavailable |
| Selected same hemisphere, every m(γγ)>1 GeV | 53,585 | 14,406 | unavailable |
| Selected same hemisphere, every m(γγ)>1.5 GeV | 52,825 | 14,114 | unavailable |
| All raw type-22, pi0+eta windows | 41,355 | 8,415 | 234,009 |
| All raw type-22, every m(γγ)>1 GeV | 13,641 | 35 | 3,732 |
| All raw type-22, every m(γγ)>1.5 GeV | 6,726 | 14 | 715 |

The candidate passes a veto when it has no eligible partner. The selected
same-hemisphere list has no partner for 46,172/54,322 direct signal and
11,915/32,631 matched eta candidates. This is why a same-hemisphere
`m(γγ)>1` or `>1.5 GeV` requirement **does not fully veto eta feed-down**.
The native Zbb Condor ROOT outputs do not store that selected same-hemisphere
pair list, so there is no like-for-like inclusive Zbb estimate for it.
The all-raw definition reaches much lower matched eta and Zbb rates but
removes most signal; it remains an optional scenario pending a physical
feed-down normalization and mass/angle acceptance review.

## BDT and expected-yield status

The ten-chunk pilot trained with the earlier ±10 MeV plus raw pi0+eta
scenario, on 4,000,000 processed Zbb events. Its independent test score
cut gave 8,353/20,005 direct Physics candidates per generated test event
and 42/800,000 other Zbb candidates per processed test event. With the PI's
normalization, the factors are 816,642 signal candidates for unit signal
efficiency and 9×10¹¹ Zbb events. The pilot therefore gives about 341,000
signal and 47.25 million Zbb candidates in the full 4.7–6.5 GeV interval.
The two-sided Poisson 95% interval for the Zbb count scales to roughly
34.1–63.9 million. This ten-chunk result cannot support a one-million
background target: one test survivor already scales to 1.125 million.

`project_offline_bdt.py` now scans validation thresholds, requires the upper
endpoint of the 95% validation-background interval below one million, then
maximizes central `S/sqrt(S+B)` among those thresholds. It checks the fixed
threshold on independent test chunks and reports if the target survives
that check. The ten-chunk pilot has no qualifying point and is reported as
unresolved. The 679-chunk and current 1,068-chunk default training and
test projections are separate larger studies. A high AUC between forced
Physics signal and centrally produced Zbb may reflect generator-production
differences; a topology-only feature model and mass/angle-shape checks are
included before accepting a working point.

The 679-chunk **default ±5 MeV, no-veto** full-feature model provides an
intermediate independent-test cross-check. Validation fixed score 0.9976384.
The test partition has 20,005 generated signal events and 53,074,083
processed Zbb events; it retains 5,114 direct signal candidates and 26
other Zbb candidates. This scales to 208,763 signal and 440,893 Zbb
candidates in 4.7–6.5 GeV, with `S/sqrt(S+B)=259.0`. The two-sided 95%
Zbb counting interval is 288,006–646,011 expected candidates. The
diagnostic 5.4–5.9 GeV interval contains only **nine** test-background
candidates, so its weighted mass and angle plots are not smooth-shape
measurements. The result passes the requested numerical targets but remains
provisional until the pi0-preselected and topology-only checks, the larger
catalog, feed-down normalization, and model-transfer review are complete.

## All available Zbb chunks: pi0-preselected BDT and scaled distributions

The 1,068-chunk analysis applies the named `lambda5_pi0` scenario before
training. It uses the raw type-22 photon partner list and a ±20 MeV pi0
mass veto. The inputs are the saved stage-1 Physics MC ROOT file and all
valid Zbb ROOT files in `zbb_catalog_current.json`. Training uses 22
reconstructed kinematic, vertex, isolation, thrust, and recoil inputs
listed in `OFFLINE_BDT_PIPELINE.md`; no mass, helicity angle, truth,
candidate count, or event ID is a BDT input. The selected model score is
frozen from 9,994 generated Physics events and 39,500,000 processed Zbb
events in the validation partitions. The independent test partitions use
20,005 generated Physics events and 78,162,817 processed Zbb events.

The validation cut is **BDT score ≥0.9922813**. On the independent test it
retains 6,002 direct Physics and 55 nonmatched Zbb candidates, each in a
different event. With the PI's factors 816,642 for unit signal efficiency
and 9×10¹¹ for unit Zbb candidate rate, this gives **245,013 expected
signal and 633,293 expected Zbb candidates** in 4.7–6.5 GeV, and
`S/sqrt(S+B)=261.4`. The two-sided 95% Poisson counting interval for the
Zbb expectation is **477,083–824,318**, below the requested one-million
ceiling at its upper edge. The diagnostic 5.4–5.9 GeV subset has only
17 test-background candidates, corresponding to 195,745 expected;
its shape remains limited by raw MC statistics. The held-out candidate
AUC is 0.99830.

For the requested single presentation canvas, the validation-fixed BDT
cut was also applied to **all** selected MC, including model-training
partitions. It leaves 29,274 direct Physics candidates and 257 nonmatched
Zbb candidates, scaling to **239,064 signal and 587,595 Zbb candidates**
in the full interval. In the diagnostic 5.4–5.9 GeV interval, 28,491
Physics and 99 Zbb MC candidates scale to 232,669 and 226,350.
The plot `full_sample_overlay_pi0_all1068/all_processed_expected_mass_and_angle.png`
shows both scaled mass shapes and the helicity-angle distribution on one
canvas, with raw MC counts and counting error bars. This all-sample view
is useful for presentation; the independent test above is the assessment
of the fixed cut.

A topology-only ten-input model on the same partitions gives held-out
AUC 0.99413 and a separately chosen validation score ≥0.9858741. Its
independent test gives 150,837 expected signal and 587,236 expected Zbb,
with `S/sqrt(S+B)=175.6` and a Zbb 95% interval of 437,236–772,107.
This cross-check also meets the requested numerical targets, but the high
separation of two differently produced MC samples still needs a transfer
study and the physical feed-down contribution is not included.

## Additional photon vetoes after the fixed BDT

The PI requested an eta-veto check on the **already scored** pi0-selected
sample. `evaluate_post_bdt_veto.py` uses the same full-feature model and
validation-fixed score ≥0.9922813; it does not retrain or optimize again.
The extra eta veto rejects a candidate if any saved raw type-22 photon pair
is within ±50 MeV of the eta mass. A candidate with no partner passes.
The distinct, stronger alternative requires every saved pair mass ≥1 GeV.

| Fixed BDT plus veto | All-MC direct signal / nonmatched Zbb | All-MC expected S / B | Test direct signal / nonmatched Zbb | Test expected S / B | Test S/√(S+B) |
|---|---:|---:|---:|---:|---:|
| Existing pi0 | 29,274 / 257 | 239,064 / 587,595 | 6,002 / 55 | 245,013 / 633,293 | 261.4 |
| pi0+eta | 24,033 / 193 | 196,264 / 441,268 | 4,898 / 43 | 199,946 / 495,120 | 239.8 |
| pi0 and every m(γγ)≥1 GeV | 8,838 / 28 | 72,175 / 64,018 | 1,805 / 6 | 73,684 / 69,087 | 195.0 |

Thus the eta veto keeps 82.1% of all-MC direct signal and 75.1% of
nonmatched Zbb **after the fixed BDT**. Its independent-test Zbb projection
is 495,120, with a two-sided 95% counting interval of 358,321–666,924.
The eta veto lowers the total background expectation but also lowers the
simple counting significance at this fixed score. The ≥1 GeV alternative
has only six test Zbb events, so its much smaller projected background is
more sensitive to sparse MC statistics. Both projections cover the full
4.7–6.5 GeV interval; 5.4–5.9 GeV is a diagnostic shape view.

Focused eta-veto linear/log plots and the three-scenario comparison plots
are in `offline_bdt_session_20261001/post_bdt_veto_fixed_model/`; exact
counts and denominators are in `post_bdt_veto_projection.json`. These plots
include all-MC and held-out-test variants. The focused all-MC overlay is
`post_bdt_eta_all_linear.png`.

## Proposed next review

### Truth audit of the final Zbb candidate table

**Question.** What generated particles make up the inclusive Zbb candidates
remaining after the fixed offline π⁰ selection and BDT? This audit is for
interpretation only; MC identity was attached after candidate building and
after the reconstructed selection.

**Exact sample and selection.** The 1,068 valid catalog chunks contain
393,638,637 processed Zbb events. The pre-BDT selection is Lambda mass
within 5 MeV, Lambda_b mass 4.7–6.5 GeV, and the saved all-raw-type-22
photon π⁰ veto. The model and validation-fixed score are those in
`bdt_full_pi0_all1068/` and `projection_full_pi0_all1068/`;
`bdt_score >= 0.9922813272476196`. The optional η veto is evaluated on
these same rows and does not retrain or move the score. The run manifest
records FCCAnalyses revision `0315db1e2941e2886813cb645193e348f3863d5d`
and repository revision `7efcf75030d9b7dabe4f6578fe9464cc2ab0135a`;
the scripts and exact rerun commands are in `OFFLINE_BDT_PIPELINE.md`.

**Candidate counts.** All 581 surviving candidates are in distinct Zbb
events: 324 full direct Lambda_b→Lambda gamma truth matches and 257
nonmatched combinations. The direct matches are kept separate from the
combinatorial Zbb background. With the optional η-window veto, 265 direct
matches and 193 nonmatched candidates remain. These are raw candidate
counts, not scaled FCC-ee yields.

**Nonmatched ancestry.** Of the 257, 175 proton-pion pairs are actually
K_S0→ππ assigned the pπ mass hypothesis, 79 are true Lambda→pπ pairs
paired with a photon that does not complete the direct decay, and 3 are
other/wrong or unmatched pairs. The candidate photon has a direct π⁰ mother
in 16 cases, direct η mother in 6, direct Lambda_b mother in 51, another
matched origin in 172, and no unique MC match in 12. These categories are
separate descriptions of the charged pair and photon, so their counts
should not be added across the two axes. Photon mother Lambda_b alone
does not imply a fully matched direct decay; that requires the Lambda and
photon to share the correct parent.

**Inspectability and limits.**
`post_bdt_zbb_truth/post_bdt_zbb_candidates_with_truth.parquet` and `.csv`
contain all 581 scored candidate rows with 74 columns, including the full
BDT feature record, event key, reconstructed daughter indices, and each
daughter's MC PDG, first mother PDG, and first grandmother PDG, with MC
indices for exact graph lookup. The one-to-one join was checked against
all saved scored survivors and the ROOT truth label. Uniquely unmatched
reconstructed particles use index `-1`/PDG `0`; a first-parent ancestry
summary cannot resolve every multi-parent graph. The plot
`post_bdt_zbb_truth/zbb_ancestry_detailed.png` compares the category
counts before and after the optional η veto. The saved photon-pair list in
these older Zbb ROOT files is all raw photons in both hemispheres, so the
same-Lambda-hemisphere η definition needs newly reconstructed stage-1
snapshots before a direct equivalent audit is possible.

**Proposed next review.** Inspect the exact daughter ancestry rows for
the K_S0 and true-Lambda subclasses, then decide which reconstructed
variables can reject them without using MC labels. The PI has not yet
selected a new reference veto from this audit.

## Exploratory post-BDT K_S0 alternative-mass veto

**Question and assumption.** The truth audit identified 175 K_S0→ππ pairs
among 257 nonmatched inclusive-Zbb candidates after the fixed BDT. Test
whether reassigning the proton track the pion mass separates these fakes
without excessive direct Λb→Λγ loss. This is a reconstructed-variable
study; truth labels only divide the reported categories.

**Exact comparison.** Keep the existing `lambda5_pi0` all-raw-photon
selection and validation-fixed BDT score `0.9922813272476196`. Use the
same 100,000 generated Physics events and 393,638,637 processed Zbb
events. The fitted proton and pion momenta in the scored tuples define
`m(ππ)` with both track masses set to 0.13957039 GeV. Veto candidates
with `|m(ππ)-0.497611 GeV| < w`, scanning `w = 5, 10, 15, 20, 30, 50`
MeV. The pπ candidate, photon, mass/angle analysis range, and BDT are
unchanged. The exact command, input paths, config, and output paths are in
`studies/reconstruction/OFFLINE_BDT_PIPELINE.md`; outputs are under
`offline_bdt_session_20261001/post_bdt_kshort_veto/`.

**Observed counts.** Before the K_S0 veto, all-MC counts are 29,274 true
Physics signal candidates, 141 wrong Physics combinations, 257 nonmatched
Zbb candidates, and 324 genuine direct Λb→Λγ candidates in inclusive Zbb.
At ±5 MeV the counts are 28,147, 137, 95, and 306, respectively. The
candidate-level conditional retention is 96.15% for true Physics signal,
36.96% for nonmatched Zbb, and 7.43% for the 175 truth-labelled K_S0 fakes.
At ±15 MeV the counts are 25,958 true Physics signal and 77 nonmatched Zbb,
giving 88.67% and 29.96% retention. All counted candidates are in distinct
events within each category at this fixed score.

**Independent test and projection.** The disjoint test partition has
20,005 generated Physics events and 78,162,817 processed Zbb events.
The fixed-score baseline is 6,002 true signal and 55 nonmatched Zbb
candidates; at ±5 MeV these become 5,765 and 27. With the supplied
branching-fraction normalization this corresponds to about 235,338 signal
and 310,890 background candidates in 4.7–6.5 GeV, compared with 245,013
and 633,293 before the veto. The central `S/sqrt(S+B)` rises from 261.4
to 318.4. The 27 surviving test-background candidates give a Poisson-only
95% projected interval of about 204,878–452,328. The ±5 MeV point has
the largest central value among this
exploratory scan, but choosing it on the test sample would bias a future
independent assessment; it is not yet a frozen reference selection.

**Checks and limits.** The tuple-only `m(ππ)` formula was compared to a
direct calculation using the saved fitted proton and pion three-vectors
on all 29,415 post-BDT Physics rows, including wrong combinations. The
maximum absolute difference was `5.83e-7 GeV`. The full and test mass/angle
plots show raw MC counts and scaled expectations; background bins remain
sparse after the veto. The study is conditional on the existing all-raw
π⁰ veto and does not solve the pending same-hemisphere η/1 GeV projection.
The PI should review the ±5 MeV proposal and its mass/angle shapes before
adopting any K_S0 veto as a reference cut.

## Earlier proposed next review

Inspect the all-sample scaled canvas and the independent-test mass and angle
plots with their raw MC bin counts. Measure a physical eta feed-down yield,
check generator/model transfer and BDT-induced mass/angle changes, then
decide whether the raw-photon pi0 veto and this BDT score become the
reference offline selection.

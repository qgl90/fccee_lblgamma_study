# Armenteros veto and next stage-1 activity scenario — PI review

## Question and inputs

Can a reconstructed Armenteros cut reject the K_S0→ππ pair contamination
seen after the fixed BDT, and what additional reconstructed quantities
should the next stage-1 Physics/Zbb production save?

The Armenteros study uses the existing `lambda5_pi0_all1068` selected
Parquets: fitted Λ mass within 5 MeV, Λγ mass 4.7–6.5 GeV, and the old
all-raw-type-22 π⁰ veto. It processes all 100,000 generated Physics
events and 393,638,637 processed Zbb events represented by 1,068 valid
chunks. It uses reconstructed momenta only for α and qT; `truth_matched`
and the already audited ancestry categories are report labels. The frozen
BDT score `0.9922813272476196` is used only for a residual-background
diagnostic. No BDT is trained, moved, or optimized here.

## Definitions and exact comparison

The helper `studies/reconstruction/armenteros.py` defines charge-signed
`α=(pL(positive)-pL(negative))/(pL(positive)+pL(negative))` and `qT` as
the daughter momentum transverse to the fitted pπ-pair direction. It can
use fitted daughter three-vectors directly or recover the same values from
the older selected tuples' momentum magnitudes and fitted pπ mass. On all
55,088 pre-BDT Physics selected candidates, those two methods agreed to
within `6.2e-7` in α and `1.85e-5 GeV` in qT.

The illustrative, **non-reference** veto in
`config/lb_armenteros_study.json` removes a candidate only when both
`0.70 ≤ |α| ≤ 0.75` and `0.09 ≤ qT ≤ 0.11 GeV`. Its boundaries were
informed by the already inspected post-BDT K_S0 cluster; its post-BDT
counts are therefore descriptive, not an unbiased cut optimization.

## Observed effect

| Category | Before box | After box | Retention |
|---|---:|---:|---:|
| Direct Physics, before BDT | 52,778 | 46,338 | 87.8% |
| Wrong Physics combinations, before BDT | 2,310 | 1,999 | 86.5% |
| Nonmatched Zbb, before BDT | 1,050,285 | 874,285 | 83.2% |
| Genuine direct Λb→Λγ in Zbb, before BDT | 622 | 528 | 84.9% |
| Direct Physics after fixed BDT | 29,274 | 26,033 | 88.9% |
| Truth-labelled K_S0 fakes after fixed BDT | 175 | 12 | 6.9% |
| Other nonmatched Zbb after fixed BDT | 82 | 75 | 91.5% |

Thus the fixed-score nonmatched Zbb count falls from 257 to 87, at an
11.1% direct-signal loss. The earlier ±5 MeV ππ-mass veto left 95
nonmatched Zbb while losing only 3.9% direct signal on the same fixed-score
sample. The box does not currently offer a better signal/background
tradeoff than that simpler alternative-mass veto. Its concentration of
post-BDT K_S0 fakes remains useful for diagnosis.

The full same-event pre-BDT plots and candidate tables are under
`outputs/analysis/studies/offline_bdt_session_20261001/armenteros_pre_bdt_all1068/`:
`armenteros_plane.png`, `armenteros_projections.png`, `armenteros_study.json`,
`physics_pre_bdt_armenteros.parquet`, `zbb_pre_bdt_armenteros.parquet`, and
`zbb_post_bdt_armenteros_truth_audit.parquet`. The plot's red dashed boxes
mark the actual two-dimensional veto region. Counts are candidate-based;
the JSON also records unique event counts. The pre-BDT background retention
is only 83.2%, so a large generic-Zbb suppression claim would be wrong.

## New reconstruction scenario and validation

The next full production is a separately named 3D/activity scenario:
`config/lb_reco_preselection_15mev_45_65_3d.json`. It changes the
upstream vertex choice from Rxy≥0.3 mm and Rxy significance≥2 to
Lxyz≥0.3 mm and a full-covariance 3D significance≥2. It leaves old
branches and the old config in place. New branches save Armenteros
variables; complete Λ-hemisphere selected and all-type-22 photon pair
lists; and candidate-removed same-Λ-hemisphere isolation sums of px, py,
pz, vector-sum momentum magnitude, energy, and multiplicity for all,
charged, and neutral objects in R=0.2, 0.3, and 0.5. Charged objects
with linked tracks also provide signed and absolute d0 minima/maxima to
the fitted PV. These use reconstructed quantities only.

One 100-input-event direct Physics trial produced 63 candidate-bearing
events and 71 candidates. On those same 100 input IDs, the old output had
the identical candidate keys, multiplicities, and masses. The new branch
decomposition, d0 sentinels, Armenteros vector values, and pair-list
nesting passed `validate_stage1_activity.py`. General flattening kept the
new branches; the offline preparation retained 74 optional scalar fields
on the 100-event trial. This does **not** establish full-sample efficiency
equivalence or performance under Condor; the PI will run those new
productions after reviewing the code.

The trial input was
`/eos/lhcb/lbdt3/user/rquaglia/fcc_ee/lblgamma/outputs/Lb2LambdaGammaPhysics_nev100000_IDEA_edm4hep.root`;
the output ROOT and validation JSON are preserved in
`outputs/analysis/studies/offline_bdt_session_20261001/stage1_3d_activity_trial_100/`.
The trial used `--nevents 100 --ncpus 1`. At review time the FCCAnalyses
checkout was `0315db1e2941e2886813cb645193e348f3863d5d`, the repository
HEAD was `7efcf75030d9b7dabe4f6578fe9464cc2ab0135a` with local edits,
and the new config SHA-256 was
`b872906ad0b25f94299c2ba627b0804d558c407134ca01f3e212c638e6cffa18`.
The edited C++ headers' SHA-256 values were
`710314e7da562dc5c833ec82c6a8cab35876bd44f605f5d6ad878222cbc4ae80`
for `lb_candidate_builder.h` and
`c1bbf8df01809ba65e32f2a0a42a38c08fc3c24971f8196af925eda1c61274f3`
for `lb_candidate_observables.h`. The trial ROOT SHA-256 was
`910e6c45d977caac29d971beeed73f62305dd81db9c50f093a5baf26f20a1d1e`.

## Proposed decision

Keep the Armenteros rectangle as an exploratory diagnostic and do not add
it to the reference selection. Review the 3D scenario and new branch
definitions, then reprocess Physics and Zbb under distinct output names.
Compare generated-event and candidate-level efficiencies to the old
Rxy scenario on matched inputs before declaring a new reference. Apply
π⁰, η, and diphoton-energy vetoes from the saved **same-Λ-hemisphere**
lists in that new production, with empty partner lists passing.

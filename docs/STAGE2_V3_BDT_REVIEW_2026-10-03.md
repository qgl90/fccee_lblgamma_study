# PI review: v3 Physics versus inclusive Zbb XGBoost

**Question.** After the unchanged v3 Stage 1 and the named offline
preselection, which score region is supported by the available inclusive
$Z\to b\bar b$ statistics, and what signal purity does it imply? This note
proposes a score for inspection. It does not change the reference selection.

## Frozen inputs and execution

- Physics signal: 100,000 generated Delphes input events, Stage 1 tuple
  `/eos/lhcb/lbdt3/user/rquaglia/fcc_ee/lblgamma/outputs/stage1_v3_my_run/signal_physics.root`.
  A separate full generator audit finds **100,002 direct decays** (49,998
  Λb and 50,004 anti-Λb), including two events with a second direct chain.
- Inclusive Zbb: [1,028-chunk frozen catalog](data/stage2_v3_bdt_1028/20261003_1028chunks.json)
  from 1,200 submitted native v3 jobs; 172 outputs were missing at the
  snapshot. All catalogued ROOT files pass the counter/schema checks and
  cover **376,723,929 processed input events**, distinct from 4,710,435
  candidate-bearing Stage 1 output events and 5,936,240 Stage 1 candidates.
- Reconstruction configuration:
  `config/lb_reco_preselection_15mev_45_65_3d.json`, SHA256
  `b872906ad0b25f94299c2ba627b0804d558c407134ca01f3e212c638e6cffa18`.
  FCCAnalyses revision recorded by the preparation:
  `0315db1e2941e2886813cb645193e348f3863d5d`.
- Offline scenario: `lambda12p5_lbE10p5_same_hemi_all` in
  `config/lb_offline_selections.json`, SHA256
  `c26d246adb0f4e2ddb3ecc4b41b1be10db38b687541989cdd7c7148bf20a1779`.
  It applies Λ⁰ ±12.5 MeV, Λb energy ≥10.5 GeV, and the existing
  same-thrust-hemisphere requirement, with no photon veto. The candidate
  mass interval for the projection is 4.7–6.5 GeV.
- Catalog SHA256:
  `69130166238a5c990a8e6ffe805c0405b3a2e2347cf3a99d44600e3cd885dcb0`.
  The [compressed complete preparation summary](data/stage2_v3_bdt_1028/prepared_summary.json.gz)
  and [training summary](data/stage2_v3_bdt_1028/training_summary.json)
  freeze all chunk records, commands, feature names, split counts and versions.
  The model is [also snapshotted here](data/stage2_v3_bdt_1028/bdt_model.json).

The 20 inputs are the named `v3_offline_no_veto_proposal` set in
`config/lb_bdt_features.json`: reconstructed kinematics, displaced-track and
Λ⁰ flight information, thrust, photon/Λ⁰ activity, Z balance, and photon
pair diagnostics. Candidate masses, cos θp, charge sign, truth/ancestry,
identity, and candidate multiplicity are excluded. Training uses every
available selected nonmatched Zbb candidate, not a training cap. Direct
signal is split by its candidate event key; whole Zbb chunks are assigned to
train/validation/test. The Physics tuple has 60,598 candidate rows with
56,871 unique `event_entry` keys and unique `(event_entry,candidate_slot)`
pairs, so candidates from a stored event stay in one split. A separate
[single-event audit](../howto/v3_candidate_event_display.md) found that one
Stage 1 `event_entry` does not point to the same *raw EDM4hep row*; this
does not merge candidates across the stored event-key split, but raw-event
joins require further validation.

## Cutflow and model check

The following are **candidate** counts. Signal means full direct truth match
used for evaluation; Zbb background means nonmatched candidate. Truth was
attached after candidate construction and was not used to build or select
observable candidates. Both charge conjugates are included.

| Stage | Direct signal | Conditional / cumulative from Stage 1 | Zbb other | Conditional / cumulative from Stage 1 |
|---|---:|---:|---:|---:|
| Stage 1 | 55,395 | 1 / 1 | 5,935,608 | 1 / 1 |
| Fit check | 55,395 | 1.000 / 1.000 | 4,843,426 | 0.816 / 0.816 |
| Λ⁰ check | 55,264 | 0.998 / 0.998 | 4,401,877 | 0.909 / 0.742 |
| Named offline selection | 54,872 | 0.993 / 0.991 | 1,060,544 | 0.241 / 0.179 |

The inclusive selected Zbb set also has 630 direct-in-Zbb candidates,
reported separately and excluded from the nonmatched background class.
Selected direct signal is 54,872 candidates from 100,000 generated events;
the 100,002 generated direct decays are a separate denominator.

XGBoost used 16 fitting threads and 8 independent Parquet readers on a
40-CPU-affinity host, with 698 best boosting rounds. The training/validation/
independent-test counts for `(Zbb other, direct signal)` are
`(741206, 38319)`, `(103501, 5494)`, `(215837, 11059)`.
ROC AUC is 0.99874 / 0.99864 / 0.99853 in those partitions. A high AUC
does not determine the rare-background rate in the tight score tail.
[Held-out score distributions](figures/stage2_v3_bdt_1028/test_response_three_categories.png),
[ROC](figures/stage2_v3_bdt_1028/test_roc.png), and
[feature importance](figures/stage2_v3_bdt_1028/feature_importance.png)
are frozen for inspection.

## Normalization and score scan

The code currently uses

\[
S = (6\times10^{12})(0.15)(2)(0.10)(7.1\times10^{-6})(0.639)
    \frac{N_{\mathrm{direct,pass}}}{N_{\mathrm{generated\ signal\ events}}},
\qquad
B = (6\times10^{12})(0.15)
    \frac{N_{\mathrm{Zbb\ other,pass}}}{N_{\mathrm{processed\ Zbb\ events}}}.
\]

The factors are 816,642 and $9\times10^{11}$, respectively. Expected yields
count candidates, while event counts are retained separately. The signal
formula assumes one forced decay per input event. The generated-chain audit
finds 100,002 direct decays in 100,000 events, so the event-denominator
normalization is high by about 0.002% relative to a per-generated-decay
normalization. The exact split allocation of the two extra decays is not
established because of the raw event-key discrepancy; this is immaterial at
the precision of the present sparse-tail projection and must be resolved for
a final physics normalization.

The 1,760-point validation scan includes a dense grid near one and exact
background-score order statistics. Its current *inspection proposal* maximizes
central $S/\sqrt{S+B}$ among points with at least 20 observed validation Zbb
candidates and a **95% Poisson upper projected Zbb yield ≤1,000,000** in the
full 4.7–6.5 GeV interval. No numeric purity floor was specified.

| Validation score ≥ | Direct MC | Zbb other MC | Expected S | Expected B | 95% upper B | Central purity | Purity using upper B |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 0.978706, constrained proposal | 2,877 | 28 | 235,089 | 683,408 | 987,715 | 25.6% | 19.2% |
| 0.990000, diagnostic | 1,911 | 11 | 156,154 | 268,482 | 480,388 | 36.8% | 24.5% |
| 0.992500, diagnostic | 1,582 | 6 | 129,270 | 146,445 | 318,748 | 46.9% | 28.9% |
| 0.995000, diagnostic | 1,086 | 3 | 88,741 | 73,222 | 213,987 | 54.8% | 29.3% |
| 0.999000, diagnostic | 105 | 0 | 8,580 | 0 observed | 90,036 | unresolved | 8.7% |

The [full scan](figures/stage2_v3_bdt_1028/working_point_scan.png),
[tight tail](figures/stage2_v3_bdt_1028/working_point_tail.png), and
[purity plot](figures/stage2_v3_bdt_1028/working_point_purity.png)
show why a more stringent apparent optimum would rely on only a few or zero
background MC candidates. Zero observed background is not a zero physical
rate. Every scan row, count, confidence interval, and normalization is in
the [frozen projection JSON](data/stage2_v3_bdt_1028/projection.json).

The score was fixed on validation and then evaluated once on the independent
test partition: **5,719 direct signal and 56 nonmatched Zbb candidates**
survive score ≥0.9787055, from 20,005 generated signal input events and
76,595,888 processed Zbb input events in that split. This projects to
233,460 signal and 657,999 Zbb candidates, central purity **26.2%** and
purity **21.5%** using the 95% upper Zbb count (854,466). The test Zbb
95% projected interval is 497,045–854,466. In the diagnostic 5.4–5.9 GeV
interval, 5,575 direct signal and 25 Zbb other candidates survive, giving
43.7% central purity; that interval is not an adopted fit window.

[Expected mass and angle](figures/stage2_v3_bdt_1028/expected_mass_and_angle.png),
[mass before/after](figures/stage2_v3_bdt_1028/mass_before_after_bdt.png),
and [angle before/after](figures/stage2_v3_bdt_1028/angle_before_after_bdt.png)
are PI diagnostics. The score changes the signal angular shape even though
cos θp is not an input. A later angular fit needs an efficiency-versus-angle
measurement. With only 56 test background survivors, the after-score mass
shape is statistically noisy; no smooth mass-background or sideband model is
claimed here.

## PI decision and limits

The 0.9787 point meets the specified background ceiling but does **not**
meet the stated qualitative aim of high purity. The tighter region cannot
yet support a precise purity estimate: validation has only 11, 6, 3, and 0
background candidates at the diagnostic scores above. The 172 missing Zbb
chunks should be catalogued and added as they finish, then the model and
validation scan repeated on a new frozen snapshot. With the current
minimum of 20 observed validation background candidates, the *largest*
purity on the scan is only 28.4% centrally and 20.4% using the 95% upper
background count (score 0.985313, exactly 20 survivors). A 90% purity
requirement has no statistically supported point in this snapshot. Zcc/Zss,
feed-down and other physical backgrounds are not included in this S/B estimate and require
their own Stage 1 processing and rate normalization before a mixed-sample
training. The PI can choose a purity requirement after viewing the plots;
only then should a score become the reference selection.

## Reproduce from the frozen outputs

The exact preparation, training and scan commands are recorded in the
compressed preparation manifest, training summary, and projection JSON. The
stage guide [howto/stage2.md](../howto/stage2.md) gives the step-by-step
commands and re-run rules. The EOS source paths for this snapshot are
`/eos/lhcb/lbdt3/user/rquaglia/fcc_ee/lblgamma/outputs/stage2_v3_incremental/prepared/`,
`models/20261003_1028chunks/`, `projections/20261003_1028chunks/`, and
`diagnostics/20261003_1028chunks/` below that same parent. The frozen
prepared summary has SHA256
`6b199bf1ad2f0e6be144c2e1c2cf2c2d81ec64ed7e486d9792ef48c711c100f5`;
the model JSON has `d6170270a4210b6a3b01d2e9522c00a3dab0896c87618ff364783045b1095706`;
the projection JSON has `2344b7d44db447173b322c02837aa0c2d284475f35bfe8a90a4ab925f32057eb`.

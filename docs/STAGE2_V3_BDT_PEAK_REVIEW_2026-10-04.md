# PI review: v3 XGBoost scan in the signal peak, 1,091 Zbb chunks

**Question.** With more of the submitted v3 inclusive Zbb jobs available,
which BDT score maximizes projected \(S/\sqrt{S+B}\) when **both** yields are
counted in the reconstructed signal peaking region? This is a proposed score
for PI inspection, not an adopted cut or a final purity estimate.

## Frozen inputs and definitions

- The [validated 1,091-chunk catalog](data/stage2_v3_bdt_1091_peak/20261003_1091chunks.json)
  covers 395,623,929 processed Zbb input events and 4,945,869 Stage 1
  candidate-bearing output events. All catalogued chunks pass ROOT counter
  and schema checks; 109 of 1,200 submitted chunk IDs still lack output.
  The Stage 1 v3 and Physics input scenario is the one in the
  [earlier 1,028-chunk review](STAGE2_V3_BDT_REVIEW_2026-10-03.md).
- The named offline scenario remains `lambda12p5_lbE10p5_same_hemi_all`:
  reconstructed Λ⁰ mass within 12.5 MeV, Λb energy at least 10.5 GeV, same
  hemisphere, and no photon veto. The [complete preparation summary](data/stage2_v3_bdt_1091_peak/prepared_summary.json.gz)
  records every shard and the original commands. The candidate mass range
  prepared is 4.7–6.5 GeV.
- The [training summary](data/stage2_v3_bdt_1091_peak/training_summary.json)
  and [frozen model](data/stage2_v3_bdt_1091_peak/bdt_model.json) use the
  same 20 reconstructed variables as the 1,028-chunk training. Zbb chunks
  and signal event keys are partitioned before scoring. Truth labels enter
  training and evaluation only, not candidate reconstruction or the score
  inputs. Training uses 8 Parquet readers and 16 XGBoost threads. ROC AUC
  is 0.998735 / 0.998617 / 0.998519 on train / validation / test.
- The **provisional** peak window is **5.4–5.9 GeV**, previously used as a
  diagnostic signal region. The PI should confirm the exact fit window before
  adopting a working point. The full [scan JSON](data/stage2_v3_bdt_1091_peak/projection.json)
  records the exact command, model and preparation hashes, 1,760 score
  points, expected-yield factors and all counting intervals.

The expected candidate yields follow the same normalization as the previous
review: \(S=816642\,N_{\rm direct,pass}/N_{\rm generated\ signal\ events}\)
and \(B=9\times10^{11}\,N_{\rm Zbb\ other,pass}/N_{\rm processed\ Zbb\ events}\).
For this scan, *pass* includes the 5.4–5.9 GeV reconstructed mass window.
The objective is projected \(S/\sqrt{S+B}\) on validation, subject to at
least 20 observed Zbb peak candidates and a projected 95% Poisson upper
background yield of at most one million. No purity floor was specified.
The score grid resolves the tight tail with actual observed background
score order statistics.

## Counts and independent check

Stage 1 has 6,232,490 Zbb candidate rows; 6,231,825 are nonmatched and
665 are direct-in-Zbb. The offline selection has 1,114,382 candidate rows:
1,113,719 nonmatched and 663 direct-in-Zbb. The 100k forced Physics sample
has 54,872 selected direct candidate rows. Candidate counts, candidate-bearing
events and input events remain separate in the preparation summary.

| Partition in 5.4–5.9 GeV | Fixed score ≥ | Direct signal MC | Nonmatched Zbb MC | Projected S | Projected B | Central purity | \(S/\sqrt{S+B}\) |
|---|---:|---:|---:|---:|---:|---:|---:|
| Validation selection | 0.95382696 | 3,648 | 21 | 298,090 | 492,521 | 37.7% | 335.2 |
| Independent test, same score | 0.95382696 | 7,355 | 56 | 300,245 | 628,461 | 32.3% | 311.6 |

The fixed test point has a 95% Poisson projected background interval of
474,733–816,109, giving 26.9% purity using its upper endpoint. In the
full 4.7–6.5 GeV interval, the same test score retains 7,529 direct and
120 nonmatched Zbb candidates; those counts are **diagnostics**, not the
optimization objective. The [working-point scan](figures/stage2_v3_bdt_1091_peak/working_point_scan.png),
[tight tail](figures/stage2_v3_bdt_1091_peak/working_point_tail.png), and
[purity plot](figures/stage2_v3_bdt_1091_peak/working_point_purity.png)
show the tradeoff and finite-background limit.

This refreshed test result is below a high-purity target. The projected
signal assumes one forced decay per generated Physics event; it omits Zcc,
Zss, feed-down and other physical backgrounds. The 56 observed test Zbb
peak candidates leave a sizable statistical interval and do not define a
smooth background mass model. Keep this working point as a named proposal.
Next, obtain the PI's peak-window and purity requirement, then compare
alternative scores and the post-BDT Armenteros proposal on newly completed
chunks. Any new score needs its own PHSP angular acceptance and migration
response before angular fitting.

## Results and figures

- [Validation score scan and expected yields](figures/stage2_v3_bdt_1091_peak/working_point_scan.png), [tight score tail](figures/stage2_v3_bdt_1091_peak/working_point_tail.png), and [projected purity](figures/stage2_v3_bdt_1091_peak/working_point_purity.png)
- [Independent-test score separation](figures/stage2_v3_bdt_1091_peak/signal_vs_background.png), [ROC](figures/stage2_v3_bdt_1091_peak/test_roc.png), and [feature importance](figures/stage2_v3_bdt_1091_peak/feature_importance.png)
- [Expected mass and angle](figures/stage2_v3_bdt_1091_peak/expected_mass_and_angle.png), [mass before and after](figures/stage2_v3_bdt_1091_peak/mass_before_after_bdt.png), and [angle before and after](figures/stage2_v3_bdt_1091_peak/angle_before_after_bdt.png)
- [Frozen scan counts and intervals](data/stage2_v3_bdt_1091_peak/projection.json), [training summary](data/stage2_v3_bdt_1091_peak/training_summary.json), and [input catalog](data/stage2_v3_bdt_1091_peak/20261003_1091chunks.json)

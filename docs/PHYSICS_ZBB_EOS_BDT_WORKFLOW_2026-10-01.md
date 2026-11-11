# Physics MC versus inclusive Zbb: direct EOS ROOT BDT workflow

## Input and selection

Use the existing flat physics-signal candidate file
`/eos/lhcb/lbdt3/user/rquaglia/fcc_ee/lblgamma/outputs/nominal_preselection_100k_signal_physics_candidates.root`
and the native inclusive-Zbb ROOT paths listed in
`outputs/analysis/studies/condor_zbb_chunk_catalog_plots_20261001.json`.
This catalog freezes the 679 chunks present at the 2026-10-01 scan; rerun the
catalog script with a new output name when more chunks arrive.

The offline diphoton rule **rejects a candidate if any** invariant mass below
1.0 GeV occurs among the candidate photon's pairs with all other raw type-22
photons. A candidate with an empty pair list passes the veto. The
flat signal branch is `Gamma_Combo_OtherGamma_M`; the native Zbb branch is
`gamma_combo_other_gamma_mass`. Empty lists fail. This is an event's
candidate-photon pairing list, so the cut denominator is candidate rows.
The script reports pre- and post-rule candidate counts and distinct signal
event counts. The baseline candidate builder and mass interval 4.5–6.5 GeV
are unchanged.

## Commands

Run the bounded cutflow check first. It reads 500 signal candidate rows and 50
ROOT event rows from each of ten Zbb chunks. The veto leaves too few Zbb
candidates in this pilot for BDT training, so the pilot writes
`cutflow_only.json`:

```bash
env -u PYTHONPATH -u PYTHONHOME myenv/bin/python \
  studies/reconstruction/train_eos_physics_zbb.py \
  --signal /eos/lhcb/lbdt3/user/rquaglia/fcc_ee/lblgamma/outputs/nominal_preselection_100k_signal_physics_candidates.root \
  --zbb-catalog outputs/analysis/studies/condor_zbb_chunk_catalog_plots_20261001.json \
  --output-dir outputs/analysis/studies/physics_zbb_bdt_veto_lowmass_pilot_20261001 \
  --max-signal-rows 500 --max-zbb-chunks 10 \
  --max-zbb-events-per-chunk 50 --cutflow-only
```

The full run on the frozen EOS inputs is:

```bash
env -u PYTHONPATH -u PYTHONHOME myenv/bin/python \
  studies/reconstruction/train_eos_physics_zbb.py \
  --signal /eos/lhcb/lbdt3/user/rquaglia/fcc_ee/lblgamma/outputs/nominal_preselection_100k_signal_physics_candidates.root \
  --zbb-catalog outputs/analysis/studies/condor_zbb_chunk_catalog_plots_20261001.json \
  --output-dir outputs/analysis/studies/physics_zbb_bdt_veto_lowmass_full_20261001 \
  --background-train-fraction 1
```

The fraction samples only training-chunk Zbb candidates after the diphoton
rule; validation and test chunks are read in full. Every available physics
signal candidate is read. The random seed and tree settings are fixed in the
script. The output `summary.json` records the cut, input paths, counts,
feature names, split sizes, independent-test AUC, validation-derived score
thresholds, and test candidate/event counts at each threshold. The fitted
model is `bdt_model.json`.

## Diagnostic outputs and interpretation

`training_kinematics.png` compares normalized training-candidate shapes of
`p`, `pT`, `eta`, and `E` for proton, pion, photon, fitted Λ, and Λb.
`training_other_variables.png` compares fitted Λ mass, displacement and
impact-parameter variables, vertex quality, isolation, recoil mass, the
diphoton-list minimum, and Λb mass. The diphoton minimum and Λb mass are
**plots only**. Neither Λb mass nor helicity angle enters the model. The
16 model inputs are proton and pion pT/η; photon E/η; fitted Λ and Λb pT/η;
proton, pion, and Λ d0 significance; Λ transverse flight distance; R=0.3
daughter-removed photon isolation; and opposite-side recoil mass `m_rec`.
Only one isolation radius and one recoil variable enter the model to avoid
repeated information.
`test_roc.png`, `test_scores.png`, and `mass_before_after_bdt.png` show
held-out performance and mass-shape changes at the validation-defined
`sig80` score threshold.

## Full frozen-catalog result for PI review

The direct ROOT run used the 679 valid chunks in the frozen catalog and read
3,337,613 Zbb ROOT event rows. The catalog records 267,510,122 processed
source events. The physics signal input had 60,593 candidate rows, of which
55,393 were truth-matched direct signal and 5,200 were wrong combinations.
The 1 GeV diphoton veto retained 13,830/55,393 direct-signal candidates
(25.0%), 491/5,200 signal wrong combinations (9.44%), and 8,239/4,204,734
nonmatched Zbb candidates (0.196%). Another 444 truth-matched candidates in
the inclusive sample were excluded from the Zbb negative class. The veto's
large signal loss deserves review before making it a reference selection.

Whole Zbb chunks contributed 5,801 train, 805 validation, and 1,633 test
post-veto background candidates. Signal events contributed 9,638 train,
1,392 validation, and 2,800 test direct candidates. The independent test AUC
was 0.9892. Validation-signal quantiles fixed these score points:

| Score point | Score | Test signal kept / 2,800 | Test Zbb kept / 1,633 | Test Zbb in 5.4–5.9 GeV |
|---|---:|---:|---:|---:|
| `sig90` | 0.8494 | 2,489 | 24 | 10 |
| `sig80` | 0.9435 | 2,247 | 17 | 8 |
| `sig70` | 0.9686 | 1,973 | 14 | 7 |
| `sig50` | 0.9859 | 1,426 | 10 | 5 |

`sig80` is a useful **comparison point**: it retains 80.3% of the signal
that passed the diphoton veto, hence about 20.0% of the post-preselection
truth-matched physics candidates, while retaining 1.04% of the post-veto
Zbb test candidates. Among these four points it gives the largest simple
signal-efficiency divided by square-root-background-efficiency proxy. The
test has only 17 background survivors, eight inside the diagnostic peak
interval; the background shape after the score cut is consequently too
sparse for a reliable fitted-background claim. The full fitted range remains
4.5–6.5 GeV. The mass before/after plot must be reviewed for sculpting.

The largest XGBoost split gains were Λ transverse flight distance, Λb pT,
Λ pT, photon E, and pion pT. Some kinematic differences between forced
physics signal and inclusive Zbb are very large. Both samples here are MC;
this is **not** a data/MC agreement check, and a model trained on these
differences needs a matched-production or data control validation before its
score can be trusted for a physical yield. The Λb candidate has no fitted
decay vertex in this reconstruction, so no Λb displacement input is invented.

Truth-matched physics MC provides the positive class; inclusive Zbb candidates
without a direct-signal truth match provide the negative class. Signal wrong
combinations are counted before and after the diphoton rule but do not train
the model. Whole Zbb chunks are assigned to train, validation, or test in a
fixed cycle; signal events are split by event ID. Validation-signal quantiles
fix `sig90`, `sig80`, `sig70`, and `sig50` thresholds, then the independent
test reports signal and Zbb retention. These score points are candidates for
PI review, not an adopted selection. The plots are normalized to each class,
and forced signal counts do not imply a physical signal yield. A physical
working point requires background normalization, mass-shape review, and an
independent physics-model/PHSP acceptance check.

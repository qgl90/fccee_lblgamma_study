# v5 flavour-tagging signal pilot — 5 October 2026

## Run and saved output

Ran the v5 stage-1 signal chain on the first 1,000 events of the 100k Physics
signal input, with `config/lb_reco_v5_training.json`. The run took 2:44,
processed 1,000 events, and returned 584 candidate-bearing events. The ROOT
output is
`outputs/analysis/studies/flavour_tagging_v5_trial/signal_1000_stage1_v5_training.root`.
Normal candidate flattening succeeded. The all-feature candidate table is
`outputs/analysis/studies/flavour_tagging_v5_trial/signal_1000_v5_candidates_all_ft.parquet`.

The saved ROOT tuple was flattened with:

```bash
env -u PYTHONPATH -u PYTHONHOME myenv/bin/python \
  studies/reconstruction/flatten_candidates.py \
  --input outputs/analysis/studies/flavour_tagging_v5_trial/signal_1000_stage1_v5_training.root \
  --output outputs/analysis/studies/flavour_tagging_v5_trial/signal_1000_v5_candidates_all_ft.parquet \
  --mode gamma
```

The flattened output has 627 candidate rows; 572 are truth matched. The
original training-focused table held six B/C/S associated-jet and other-jet
columns. After widening the preparation pass-through, the all-feature table
contains all ten B/C/S/Q/G associated-jet and other-jet columns. They have no
nulls in the shared training region. See
[`STAGE1_V5_FLAVTAG_VARIABLES.md`](STAGE1_V5_FLAVTAG_VARIABLES.md) for the
branch-by-branch definitions.

The exact Stage-1 command was:

```bash
LB_RECO_ANALYSIS=analysis/studies/lb2lambda_gamma_reco_v5.py \
  timeout 900 scripts/run_reco_preselection.sh signal_physics \
  /tmp/Lb2LambdaGammaPhysics_nev100000_IDEA_edm4hep_v5.root \
  outputs/analysis/studies/flavour_tagging_v5_trial/signal_1000_stage1_v5_training.root \
  1000 config/lb_reco_v5_training.json 1
```

The temporary input is a local copy of
`/eos/lhcb/lbdt3/user/rquaglia/fcc_ee/lblgamma/outputs/Lb2LambdaGammaPhysics_nev100000_IDEA_edm4hep.root`;
its SHA-256 is
`f483c59cc2fc1274d439c76a2232f272d1c6d54737ddeece6889fb4edb8740dc`.
The config SHA-256 is
`c35ba612be74c79e2f671fffaef3b3252650263107d7ac63ad9b7029500b08f1`.
The FCCAnalyses checkout was at `0315db1e2941e2886813cb645193e348f3863d5d`;
the repository base HEAD was `ca8c55e8a406889f6d45675dbcb860fe5ec8f232`
with v5 files present as working-tree changes. The model preprocessing JSON
and ONNX SHA-256 values are respectively
`0ef56a920d104d9f6f7c244eccd38bf3a1eb47efaf81dfdea4eaafb559320c6a` and
`faff362ebd94e0218e459d77243ad4a7260e6fc659e818eee1d4e0e0dd097dbf`.

## Signal-only diagnostic

Use the shared offline region `lb_energy >= 10.5 GeV` and
`abs(lambda_slot_mass - 1.115683 GeV) <= 12.5 MeV`. It contains 612 candidate
rows, 572 matched. For `lb_flavtag_v5_recojet_isB_flavtag_v5_otherjet_max`, the
matched-signal retention is:

| Score threshold | Matched candidates retained |
|---:|---:|
| 0.50 | 91.4% |
| 0.80 | 88.5% |
| 0.90 | 85.3% |
| 0.95 | 80.1% |
| 0.99 | 40.7% |

These are raw tagger-score efficiencies on signal only, before training a
combined BDT. They do not measure rejection of Z→ss, Z→cc, or Z→bb and are not
selection recommendations. The v5 tagger uses a reconstructed PV in place of
the pretrained model's MC-derived PV feature and includes the selected
candidate daughters in the event jets; both choices need study before using
the calibration for physics conclusions.

## Processing shortcut

The `E(Λb) >= 10.5 GeV` event gate is applied immediately after candidate
building, before truth annotation, offline observables, pointing, and tagger
inference. It reduces downstream work and written rows. Pair construction and
the two-track vertex fits still run before this gate. The candidate Λ⁰ mass
window and fitted displacement requirements are also applied by the builder
after vertex fitting. A raw pair-mass prefilter of ±0.15 GeV was tested on 200
events but retained only 73/129 (56.6%) of candidates in the shared offline
region, so it remains disabled.

## Next comparison

Produce corresponding v5 Zbb training data plus held-out Zss and Zcc data;
train using `v5_offline_plus_flavtag` in
`config/lb_bdt_features_v5_flavtag.json`. Measure the combined-model response
at fixed signal efficiency, retaining separate denominators for direct signal,
wrong signal combinations, and each inclusive background. No v5 Condor jobs
have been submitted as of this report.

## Condor wrapper check-only

The v5 wrapper default was corrected to load
`config/lb_reco_v5_training.json` before importing the shared dispatch code.
On 2026-10-05, `fccanalysis run analysis/studies/analysis_preselection_v5.py`
with `--check-only`, `--chunks 1200`, and `--ncpus 4` validated the standard
Winter2023 IDEA input globs: Zbb (4,398 files), Zcc (5,018), and Zss (5,015).
Each check printed the v5 training config and a distinct `stage1_v5_flavtag`
EOS destination and exited without submitting jobs. The preprocessing JSON
and ONNX file were readable on the submit host. This does not verify
worker-side model access or execute a Condor worker graph.

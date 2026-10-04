# Reproduce the v3 Λπ⁰ and Λη physics-model background chain

The [PI review](../docs/STAGE2_V3_PSEUDOSCALAR_BACKGROUNDS_2026-10-04.md)
links the stage counts, normalized results and figures. These forced-mode
samples are reconstructed as **one-photon Λb→Λγ** candidates under the same
v3 Stage 1 and offline configurations as signal. Truth ancestry is attached
only after reconstruction to identify genuine partial decays.

The frozen 100k EDM4hep inputs, Stage 1 v3 tuples, and complete Stage 2
`audit/`, `offline_selected/`, `bdt_selected/` tables and manifests are
archived under the three EOS directories named in the PI review. The
[study manifest](../docs/data/stage2_v3_pseudoscalar_100k_bdt1091peak/study_manifest.json)
records hashes, commands, seeds, stage counts and figure provenance.

## Stage 0: forced generation and checks

The complete configurations, distinct seeds and production recipe are in
[the Delphes guide](delphes_production.md). The two physics-model 100k files
come from ten independently seeded 10k chunks each, using the unchanged
`cards/card_IDEA.tcl` and `cards/edm4hep_IDEA.tcl`:

```bash
env -u PYTHONPATH -u PYTHONHOME XDG_CACHE_HOME=/tmp/rquaglia_smk_cache \
  myenv/bin/python -m snakemake --snakefile Snakefile --cores 10 \
  outputs/delphes/Lb2LambdaPi0Physics_nev100000_IDEA_edm4hep.root \
  outputs/delphes/Lb2LambdaEtaPhysics_nev100000_IDEA_edm4hep.root

env -u PYTHONPATH -u PYTHONHOME myenv/bin/python \
  studies/reconstruction/audit_generated_forced_chain.py \
  --input outputs/delphes/Lb2LambdaPi0Physics_nev100000_IDEA_edm4hep.root \
  --mode pi0 --expected-alpha -0.89 \
  --output /tmp/v3_pi0_physics_100k_generated_audit.json \
  --plot /tmp/v3_pi0_physics_100k_generated_angle.png

env -u PYTHONPATH -u PYTHONHOME myenv/bin/python \
  studies/reconstruction/audit_generated_forced_chain.py \
  --input outputs/delphes/Lb2LambdaEtaPhysics_nev100000_IDEA_edm4hep.root \
  --mode eta --expected-alpha 0.733 \
  --output /tmp/v3_eta_physics_100k_generated_audit.json \
  --plot /tmp/v3_eta_physics_100k_generated_angle.png
```

## Stage 1: common one-photon reconstruction

```bash
bash scripts/run_reco_preselection.sh lbgamma_pi0 \
  outputs/delphes/Lb2LambdaPi0Physics_nev100000_IDEA_edm4hep.root \
  /tmp/lbgamma_pi0_physics_100k_stage1_v3.root all \
  config/lb_reco_preselection_15mev_45_65_3d.json 8

bash scripts/run_reco_preselection.sh lbgamma_eta_physics \
  outputs/delphes/Lb2LambdaEtaPhysics_nev100000_IDEA_edm4hep.root \
  /tmp/lbgamma_eta_physics_100k_stage1_v3.root all \
  config/lb_reco_preselection_15mev_45_65_3d.json 8
```

`all` processes the full 100k events per input. The reconstruction applies
the same fitted-track and same-hemisphere Λγ candidate logic as signal;
it does not know whether the photon came from π⁰, η or a direct decay.
The complete Stage 2 preparation below checks the ROOT counters and flattens
all Stage 1 candidate rows, then joins them to the offline audit by
`source_id`, `event_entry` and `candidate_slot`. For an additional independent
ROOT vector audit, run `studies/reconstruction/verify_stage1_v3_outputs.py`
with `--input <stage1_v3.root> --output <validation.json>`. The optional
`--all-vectors` pass reads every candidate diagnostic branch and is
substantially slower for a full tuple.

## Stage 2 and fixed BDT

The BDT is the separate [1,091-chunk peak-window proposal](../docs/STAGE2_V3_BDT_PEAK_REVIEW_2026-10-04.md).
The score comes from its validation partition; no training or tuning occurs
on these forced backgrounds. Run once for each Stage 1 ROOT file:

```bash
RUN=/eos/lhcb/lbdt3/user/rquaglia/fcc_ee/lblgamma/outputs/stage2_v3_incremental
MODEL="$RUN/models/20261004_1091chunks"
PROJECTION="$RUN/projections/20261004_1091chunks_peak_5p4_5p9/projection.json"

env -u PYTHONPATH -u PYTHONHOME myenv/bin/python \
  studies/reconstruction/score_stage1_v3_dataset.py \
  --input /tmp/lbgamma_pi0_physics_100k_stage1_v3.root \
  --model-dir "$MODEL" --projection "$PROJECTION" \
  --output-dir /tmp/v3_pi0_physics_100k_stage2_bdt1091peak \
  --sample lb_lambdapi0_physics_v3 --source-id -4

env -u PYTHONPATH -u PYTHONHOME myenv/bin/python \
  studies/reconstruction/score_stage1_v3_dataset.py \
  --input /tmp/lbgamma_eta_physics_100k_stage1_v3.root \
  --model-dir "$MODEL" --projection "$PROJECTION" \
  --output-dir /tmp/v3_eta_physics_100k_stage2_bdt1091peak \
  --sample lb_lambdaeta_physics_v3 --source-id -5
```

The runner preserves every candidate in `audit/`, offline survivors in
`offline_selected/`, and BDT survivors in `bdt_selected/`. The manifest
checks the input and model scenario and stores the score, commands and
counts. The BDT itself does not use truth, parent identity, candidate mass
or helicity angle as inputs.

## Ancestry, mass shape and branching-fraction scenarios

Use [the explicit branching config](../config/v3_pseudoscalar_branching_scenarios.json)
to inspect or revise parent and daughter fractions. The η parent value is
the LHCb evidence central value; the π⁰ parent value is a theory benchmark,
not a measurement. The calculation keeps a yield per parent branching
fraction of 10⁻⁶ so the PI can insert an alternative without rerunning
Delphes or reconstruction.

```bash
env -u PYTHONPATH -u PYTHONHOME myenv/bin/python \
  studies/reconstruction/study_v3_pseudoscalar_backgrounds.py \
  --mode pi0_physics \
  --stage2-manifest /tmp/v3_pi0_physics_100k_stage2_bdt1091peak/manifest.json \
  --generated-audit /tmp/v3_pi0_physics_100k_generated_audit.json \
  --output-dir /tmp/v3_pi0_physics_100k_bdt1091peak_study

env -u PYTHONPATH -u PYTHONHOME myenv/bin/python \
  studies/reconstruction/study_v3_pseudoscalar_backgrounds.py \
  --mode eta_physics \
  --stage2-manifest /tmp/v3_eta_physics_100k_stage2_bdt1091peak/manifest.json \
  --generated-audit /tmp/v3_eta_physics_100k_generated_audit.json \
  --output-dir /tmp/v3_eta_physics_100k_bdt1091peak_study
```

The evaluator identifies direct partial candidates from reconstructed
daughter associations followed back to a common generated parent. It
reports wrong/unmatched candidates separately, but that truth label never
enters an observable cut. Its expected-yield formula counts candidate rows
in the named 5.4–5.9 GeV window and divides by the number of generated
forced-mode decays, rather than the number of Stage 1 output events.

For a mass-shape comparison with the same validation-fixed signal and
inclusive Zbb projection, keep forced-mode curves separate from Zbb because
the inclusive sample may already contain those rare decays:

```bash
env -u PYTHONPATH -u PYTHONHOME myenv/bin/python \
  studies/reconstruction/compare_v3_pseudoscalar_to_signal_zbb.py \
  --reference-projection "$PROJECTION" \
  --reference-candidates "$RUN/projections/20261004_1091chunks_peak_5p4_5p9/expected_test_candidates.parquet" \
  --eta-summary /tmp/v3_eta_physics_100k_bdt1091peak_study/summary.json \
  --eta-candidates /tmp/v3_eta_physics_100k_stage2_bdt1091peak/bdt_selected/lb_lambdaeta_physics_v3_-5.parquet \
  --pi0-summary /tmp/v3_pi0_physics_100k_bdt1091peak_study/summary.json \
  --pi0-candidates /tmp/v3_pi0_physics_100k_stage2_bdt1091peak/bdt_selected/lb_lambdapi0_physics_v3_-4.parquet \
  --output-dir /tmp/v3_pseudoscalar_100k_bdt1091peak_comparison
```

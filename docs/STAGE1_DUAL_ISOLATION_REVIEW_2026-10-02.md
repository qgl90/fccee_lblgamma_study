# Dual-center isolation Stage 1 trial — 2026-10-02

## Question and agreed definition

For each reconstructed Λb→Λ⁰γ candidate, measure same-hemisphere activity
in cones around both the candidate photon and the fitted Λ⁰ direction.
The PI specified that charged activity exclude the candidate Λ⁰ daughters,
neutral activity exclude the candidate photon, and all activity exclude all
three daughters. The PI chose ΔR=2.0 (`R20`) instead of the previous wide
ΔR=7.0 (`R70`) cone. The other radii are 0.2, 0.3, 0.5, 0.7 and 1.0.
All activity uses the fitted Λ⁰ side of the original full-event thrust axis,
with strict same-side and cone inequalities. These are **diagnostic fields**;
no candidate or offline selection changed in this trial.

## Provenance and exact comparison

- Input: `/eos/lhcb/lbdt3/user/rquaglia/fcc_ee/lblgamma/outputs/Lb2LambdaGammaPhysics_nev100000_IDEA_edm4hep.root`.
  Its SHA-256 in `config/lb_stage1_v2_samples.json` is
  `f483c59cc2fc1274d439c76a2232f272d1c6d54737ddeece6889fb4edb8740dc`.
  The detector card and Delphes response were unchanged.
- FCCAnalyses revision: `0315db1e2941e2886813cb645193e348f3863d5d`.
  Repository HEAD before local edits: `d112557c08b071cae72f630426fad9c6ffff4a03`.
- Reconstruction config SHA-256:
  `b872906ad0b25f94299c2ba627b0804d558c407134ca01f3e212c638e6cffa18`.
  New observables config SHA-256:
  `d0ebc4c1b8c3bfdc409515bf6e0c5fd8df5892b53fd7798ec8789484d5d9e3df`.
- New C++ observable header SHA-256:
  `1ae769648a193b1390fefb003f77cfaa10461e101efe1d8121f46d7a987205c3`.
- The baseline is the previous **100-input-event** ancestry trial on the
  same input entries:
  `outputs/analysis/studies/stage1_ancestry_trial_20261002/signal_physics_100.root`.

Trial command (100 input events, one CPU):

```bash
scripts/run_reco_preselection.sh signal_physics \
  /eos/lhcb/lbdt3/user/rquaglia/fcc_ee/lblgamma/outputs/Lb2LambdaGammaPhysics_nev100000_IDEA_edm4hep.root \
  outputs/analysis/studies/stage1_iso_dualcenter_trial_20261002/signal_physics_iso_100.root \
  100 config/lb_reco_preselection_15mev_45_65_3d.json 1
```

The same folder contains the flattened candidate Parquet and validation
JSON files. The independent raw-object check is reproducible with:

```bash
env -u PYTHONPATH -u PYTHONHOME myenv/bin/python \
  studies/reconstruction/validate_stage1_isolation.py \
  --raw /eos/lhcb/lbdt3/user/rquaglia/fcc_ee/lblgamma/outputs/Lb2LambdaGammaPhysics_nev100000_IDEA_edm4hep.root \
  --stage1 outputs/analysis/studies/stage1_iso_dualcenter_trial_20261002/signal_physics_iso_100.root \
  --event-limit 100 \
  --output outputs/analysis/studies/stage1_iso_dualcenter_trial_20261002/isolation_validation.json
```

## Observed effect and limits

The reconstruction processed 100 input events and wrote 63 candidate-bearing
events and 71 candidates, identical to the baseline. Candidate event IDs and
masses matched, and all 115 shared photon-centered activity branches at R02
through R10 matched **exactly**. New output contains 138 photon-centered and
138 Λ⁰-centered activity branches, including R20; it does not contain R70.
The flattened table and Stage 2 row producer both retained all 138 new Λ⁰
fields for all 71 candidates.

The independent checker recomputed photon/Λ⁰ geometry, fitted-Λ hemisphere,
charge classes, daughter exclusions, momentum sums, energy sums and counts
from the original `ReconstructedParticles` on those 100 events. All **15,336**
saved values agreed within float precision. The other Stage 1 validator
passed the activity decomposition, charged-d0 sentinels, candidate mass
comparison and unrelated observable consistency checks.

This validates computation and schema propagation on a bounded Physics MC
trial. It does not establish the discriminating power of any isolation field
or authorize an isolation cut. Zbb and the full forced samples need their
own reprocessing with a distinct campaign label before comparing new
activity distributions. Existing R70 tuples remain historical and cannot
be treated as if they had R20 or Λ⁰-centered values.

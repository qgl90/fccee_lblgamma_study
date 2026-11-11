# Stage 1 four-generation ancestry extension — 2026-10-02

## Question and definition

Can a final selected background candidate retain enough MC ancestry to
inspect its proton, pion, and photon chains through four generations?
The Stage 1 truth labeler now follows the first valid parent at each step:
particle ← parent ← grandparent ← great-grandparent ←
great-great-grandparent. These are signed PDG IDs plus indices in the event's
`Particle` collection. `reco_mc_n_parents` reports the matched particle's
number of valid parents. A chain starting from an absent or non-unique stable
reco↔MC association is missing; each missing index is `-1`, each missing PDG
ID is `0`. This is a **single first-parent path**, not a complete graph of
all possible parents. No MC field enters candidate building or selection.

## Code path and provenance

- C++ annotation: `analysis/studies/lb_candidate_truth.h`; output declaration:
  `analysis/studies/lb2lambda_gamma_baseline.py`. The direct
  `lb2lambda_gamma_reco.py` and native Condor
  `analysis_preselection_zbb.py` share this output method.
- Candidate flattening: `studies/reconstruction/flatten_candidates.py` joins
  each leg by `lb_{proton,pion,photon}_index`; the optional Stage 2 preparation
  copies these truth fields into its audit and selected rows. Existing
  snapshot branches and truth-matching rules remain unchanged.
- Repository HEAD before local edits:
  `d112557c08b071cae72f630426fad9c6ffff4a03`; local ancestry edits
  described in this note. FCCAnalyses revision:
  `0315db1e2941e2886813cb645193e348f3863d5d`.
- Input: `/eos/lhcb/lbdt3/user/rquaglia/fcc_ee/lblgamma/outputs/Lb2LambdaGammaPhysics_nev100000_IDEA_edm4hep.root`.
  The full-sample manifest `config/lb_stage1_v2_samples.json` records its
  SHA-256 as `f483c59cc2fc1274d439c76a2232f272d1c6d54737ddeece6889fb4edb8740dc`.
- Reconstruction config SHA-256:
  `b872906ad0b25f94299c2ba627b0804d558c407134ca01f3e212c638e6cffa18`.
  Observables config SHA-256:
  `75d849f40bd64164161b11b6652c1450a1cd173482c22cf1e3607bd12d632152`.
  The Delphes input and card are unchanged by this annotation extension.

## Bounded trial and observed effect

The exact 100-input-event command was:

```bash
scripts/run_reco_preselection.sh signal_physics \
  /eos/lhcb/lbdt3/user/rquaglia/fcc_ee/lblgamma/outputs/Lb2LambdaGammaPhysics_nev100000_IDEA_edm4hep.root \
  outputs/analysis/studies/stage1_ancestry_trial_20261002/signal_physics_100.root \
  100 config/lb_reco_preselection_15mev_45_65_3d.json 1
```

It processed 100 input events and wrote 63 candidate-bearing events and 71
candidates. Flattening those 63 events produced 71 one-candidate-per-row
records with all 12 new daughter columns (two generations × index and PDG ×
three legs). For all 71 rows, proton, pion, and photon values checked against
their reconstructed-particle indices in the Stage 1 ROOT vectors. The Stage 2
row producer retained the ancestry fields for all 71 candidate rows; a
simulated older schema filled missing deep generations with `-1`/`0`.
The existing baseline diagnostic ran successfully on the same trial and
wrote `truth_matched_components.csv`, summary, and plots under
`outputs/analysis/studies/stage1_ancestry_trial_20261002/plots/`.

This trial verifies schema propagation and indexing. It does not measure a
selection change or background composition. Existing full Stage 1 tuples
cannot acquire the added generations without reprocessing from Delphes.
The next full-run choice belongs to the PI; any new production should use a
distinct output name and the Stage 1 commands in `howto/stage1.md`.

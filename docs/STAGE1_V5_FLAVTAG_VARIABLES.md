# v5 flavour-tagging variables

This note describes the v5 outputs from
`analysis/studies/flavour_tagging_v5.py` as seen in the 1,000-event signal
pilot. The event-level columns contain one value per reconstructed jet (two
exclusive ee-kt jets by default); the candidate-aligned columns contain one
value per Λb candidate and become scalar columns after candidate flattening.

The pilot ROOT file contains all five model classes and all ten
candidate-aligned score branches. The BDT preparation pass-through now keeps
all ten. The proposed `v5_offline_plus_flavtag` model uses six of them: B, C,
and S for both the associated and other jet. G and Q remain available for
diagnostics and later feature studies.

## Saved event-level columns

| Variable(s) | Meaning |
|---|---|
| `flavtag_v5_pv_x`, `_y`, `_z` | Reconstructed primary-vertex position supplied to the tagger instead of the MC-derived vertex used by the upstream example. These are the coordinates from the existing `PrimaryVertexObject`. |
| `event_njet_flavtag_v5` | Number of jets returned by the exclusive-ee-kt clustering. The configured request is two jets. |
| `jet_p_flavtag_v5`, `jet_e_flavtag_v5`, `jet_mass_flavtag_v5` | Per-jet momentum magnitude, energy, and invariant mass (GeV). |
| `jet_phi_flavtag_v5`, `jet_theta_flavtag_v5` | Per-jet azimuth and polar angle (radians). The directions are also used to associate a candidate to a jet. |
| `jet_nconst_flavtag_v5` | Number of reconstructed particle constituents assigned to each jet. |
| `jet_nmu_flavtag_v5`, `jet_nel_flavtag_v5` | Per-jet muon and electron constituent counts. |
| `jet_nchad_flavtag_v5` | Per-jet charged-hadron constituent count. |
| `jet_ngamma_flavtag_v5`, `jet_nnhad_flavtag_v5` | Per-jet photon and neutral-hadron constituent counts. |
| `recojet_isB_flavtag_v5`, `recojet_isC_flavtag_v5`, `recojet_isS_flavtag_v5`, `recojet_isQ_flavtag_v5`, `recojet_isG_flavtag_v5` | Per-jet output scores for the pretrained model's b, c, s, light-quark (`Q`), and gluon (`G`) classes. These are classifier outputs, not calibrated probabilities for this reconstructed-PV setup. |

All per-jet vectors use the same jet ordering within an event. The tagger
clusters the full `ReconstructedParticles` collection; it does not remove the
candidate's proton, pion, or photon before clustering.

## Candidate-aligned columns

For each class `X` in `B`, `C`, `S`, `Q`, and `G`, the ROOT tuple stores:

| Pattern | Meaning |
|---|---|
| `lb_flavtag_v5_recojet_isX_flavtag_v5_associated` | Class-X score of the event jet whose direction is nearest the reconstructed Λb candidate direction. The association uses the 3D angle (maximum unit-vector dot product) between candidate momentum and jet direction. |
| `lb_flavtag_v5_recojet_isX_flavtag_v5_otherjet_max` | Maximum class-X score among all jets other than the associated jet. With the default two-jet clustering, this is the opposite jet's class-X score. |

These are candidate-aligned copies of the event-level scores, not separately
trained taggers. Their values are `-1` if no valid associated jet or score is
available. Candidate daughters are still present in both event jets, so the
associated score can be influenced by the candidate itself.

The ten exact column names are:

- `lb_flavtag_v5_recojet_isB_flavtag_v5_associated`
- `lb_flavtag_v5_recojet_isB_flavtag_v5_otherjet_max`
- `lb_flavtag_v5_recojet_isC_flavtag_v5_associated`
- `lb_flavtag_v5_recojet_isC_flavtag_v5_otherjet_max`
- `lb_flavtag_v5_recojet_isS_flavtag_v5_associated`
- `lb_flavtag_v5_recojet_isS_flavtag_v5_otherjet_max`
- `lb_flavtag_v5_recojet_isQ_flavtag_v5_associated`
- `lb_flavtag_v5_recojet_isQ_flavtag_v5_otherjet_max`
- `lb_flavtag_v5_recojet_isG_flavtag_v5_associated`
- `lb_flavtag_v5_recojet_isG_flavtag_v5_otherjet_max`

## Candidate-table BDT inputs

`config/lb_bdt_features_v5_flavtag.json` appends these six columns to the
current 20 offline features:

| Feature(s) | Intended information |
|---|---|
| `...isB..._associated`, `...isB..._otherjet_max` | How b-like the candidate-side and opposite event jets are. |
| `...isS..._associated`, `...isS..._otherjet_max` | How s-like the candidate-side and opposite event jets are; directly relevant to studying Z→ss. |
| `...isC..._associated`, `...isC..._otherjet_max` | How c-like the candidate-side and opposite event jets are; helps retain a distinct Z→cc control/background category. |

The Q and G columns are deliberately preserved but are not currently in this
named feature set. No combined v5 BDT has been trained yet.

## Event gate and inference inputs

`flavtag_v5_n_candidate_energy_pass` is the count of built candidates with
`E(Λb) >= LB_V5_MIN_LB_ENERGY_GEV` (10.5 GeV by default). Events with count
zero are filtered before truth annotation, offline observables, pointing, and
tagger inference. This is a selection/cutflow column, not a flavour-tagging
feature.

The helper also creates temporary particle-flow constituent inputs for the
Weaver inference. They are padded/truncated to 75 constituents per jet by the
model preprocessing and are not written as v5 tuple branches:

| Preprocessing group | Names in model JSON | Meaning |
|---|---|---|
| `pf_points` | `pfcand_thetarel`, `pfcand_phirel` | Constituent angular offsets from the jet axis. |
| `pf_features` | 34 particle-level inputs listed below | Relative energy, angular and track/covariance features, particle type flags, PID-related quantities, and impact-parameter/b-tag quantities supplied to Weaver. |
| `pf_vectors` | `pfcand_e`, `pfcand_p`, `pfcand_e`, `pfcand_e` | Vector-input channels as declared by this model's preprocessing JSON. Preserve the channel order; the repeated names are part of that file. |
| `pf_mask` | `pfcand_mask` | Marks real constituents versus padding. |

The 34 named
particle features are `pfcand_erel_log`, `pfcand_thetarel`,
`pfcand_phirel`, `pfcand_dptdpt`, `pfcand_detadeta`, `pfcand_dphidphi`,
`pfcand_dxydxy`, `pfcand_dzdz`, `pfcand_dxydz`, `pfcand_dphidxy`,
`pfcand_dlambdadz`, `pfcand_dxyc`, `pfcand_dxyctgtheta`, `pfcand_phic`,
`pfcand_phidz`, `pfcand_phictgtheta`, `pfcand_cdz`, `pfcand_cctgtheta`,
`pfcand_mtof`, `pfcand_dndx`, `pfcand_charge`, `pfcand_isMu`,
`pfcand_isEl`, `pfcand_isChargedHad`, `pfcand_isGamma`,
`pfcand_isNeutralHad`, `pfcand_dxy`, `pfcand_dz`, `pfcand_btagSip2dVal`,
`pfcand_btagSip2dSig`, `pfcand_btagSip3dVal`, `pfcand_btagSip3dSig`,
`pfcand_btagJetDistVal`, and `pfcand_btagJetDistSig`. These helper inputs are
used internally and are not written as v5 tuple branches. Their definitions
and normalization are controlled by the model's preprocessing JSON.

## Pilot check

After adding Q/G to the candidate-table pass-through, the existing pilot ROOT
file was flattened again to
`outputs/analysis/studies/flavour_tagging_v5_trial/signal_1000_v5_candidates_all_ft.parquet`.
It contains 627 candidates, including 572 truth-matched candidates. All ten
candidate-aligned FT columns are present and have zero nulls in the shared
training region (`E(Λb) >= 10.5 GeV`, fitted Λ⁰ mass within ±12.5 MeV), which
contains 612 candidates. The signal score-retention scan is reported in
[`STAGE1_V5_FLAVTAG_SIGNAL_PILOT_2026-10-05.md`](STAGE1_V5_FLAVTAG_SIGNAL_PILOT_2026-10-05.md).
No background rejection claim follows from that signal-only check.

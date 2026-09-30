# Candidate Parquet columns

This guide describes the one-row-per-candidate table written by
`studies/reconstruction/flatten_candidates.py`. It is written against the
current `--mode gamma` producer and the stage-1 reconstructed tree. The
flattening command for the 1,000-event raw-mass-prefilter test is:

```bash
env -u PYTHONPATH -u PYTHONHOME myenv/bin/python \
  studies/reconstruction/flatten_candidates.py \
  --input outputs/analysis/studies/LbGamma_prefilter50_signal_rawmass50_1000.root \
  --output outputs/analysis/studies/LbGamma_prefilter50_signal_rawmass50_1000_flatten.parquet \
  --mode gamma --source-id 0 --chunk-events 500
```

`--chunk-events` controls how many ROOT event entries are read and converted
per batch. The default is 500; lower it if a high-multiplicity input causes
memory pressure, or raise it if memory is available and I/O overhead dominates.

It also writes a sibling `.summary.json`. The Parquet schema preserves the
selected ROOT candidate branches and scalar event branches, then adds readable
LHCb-style aliases. Thus there are intentional aliases for some values; the
source names remain available for audit and compatibility with existing
analysis code.

## Row keys, event fields, and units

Each row represents one reconstructed `Lambda_b -> Lambda0 gamma` candidate
that survived the reconstruction configuration (including its Lambda mass,
Lambda_b mass, and hemisphere requirements). Multiple candidates from an
event create multiple rows. Events with no selected candidate have no row.

| Column | Meaning and use | Producer / definition |
|---|---|---|
| `source_id` | File or batch identifier. Use with the event and candidate keys when independently flattened files restart `event_entry` at zero. | `--source-id`; constant for this input file. |
| `event_entry` | Entry number in the input ROOT `events` tree. | Set by the reconstruction dataframe from `rdfentry_`. |
| `candidate_slot` | Candidate index within that event, starting at zero. | Flattening index into the event's `lb_mass` vector. |
| `candidates_in_event` | Number of selected candidates in that event. | The event's `n_lb`, copied to every candidate row. |
| `thrust_value`, `thrust_x/y/z` | Event thrust magnitude and axis used for the Lambda/photon hemisphere requirement. The axis sign is arbitrary. | FCCAnalyses thrust on all reconstructed particles in `lb2lambda_gamma_baseline.py`. |
| `pv_x/y/z` | Reconstructed primary-vertex coordinates in mm. | One beam-spot-constrained event PV fit; repeated on candidate rows. |
| `input_*`, `n_*`, `pv_valid`, `n_pv_tracks`, `lambda_*`, `lb_*` | Source scalar event counts, validity flags and counts for builder stages. See the tables below for candidate-vector columns. These scalar fields are copied onto every candidate row. | Existing scalar branches of the reconstructed ROOT tree. New scalar branches are preserved automatically by the flattener. |

Momentum, energy, and mass are in GeV; `Pt` and `P` are in GeV; PV/SV positions,
flight distances and impact parameters are in mm; angles are in radians;
significances, cosines, and isolation ratios are dimensionless. PDG IDs and
collection indices are integers. `-999` generally means undefined/unavailable;
truth indices use `-1` for no unique association. Check the particular field
before treating either value as a physical measurement.

For the raw-mass-prefilter run, the scalar counters
`n_opposite_charge_pairs`, `n_pairs_nonprimary`, `n_pairs_d0_pass`,
`n_pairs_raw_mass_pass`, and `n_vertex_fits` count the pair-processing stages
per event. The gate tests both raw-momentum pπ assignments within the configured
half-window. They are event-level counters copied to each candidate row, not
candidate weights.

## Candidate kinematics and reconstruction

The original names below are retained from the reconstructed ROOT branches.
Their corresponding `Lb_*`, `Lambda0_*`, daughter, or photon aliases are listed
in the following section.

| ROOT / Parquet column | Meaning and recommended use |
|---|---|
| `lb_mass`, `lb_energy`, `lb_px/py/pz`, `lb_pt` | Reconstructed Lambda_b candidate four-momentum/mass from the fitted Lambda daughter momenta and measured photon. Use `lb_mass` for the mass fit or mass-window studies. |
| `lb_sign` | `+1` for the Lambda_b / p+π− hypothesis, `−1` for anti-Lambda_b / pbar−π+; a charge-hypothesis label, not truth. |
| `lb_lambda_slot` | Index linking this Lambda_b candidate to the corresponding entry in the per-event Lambda candidate vectors. Used internally by flattening to copy Lambda-vertex quantities. |
| `lb_proton_index`, `lb_pion_index`, `lb_photon_index` | Indices in `ReconstructedParticles` for the selected proton-hypothesis daughter, pion-hypothesis daughter, and candidate photon. Preserve these for object-level joins and photon-veto studies. |
| `lb_photon2_index` | Second neutral index; `-1` for one-photon gamma mode. Eta mode uses a second photon. |
| `lb_lambda_mass` | Fitted-momentum pπ mass under the selected mass assignment. The candidate Lambda mass window is applied to this quantity in the current reconstruction. |
| `lb_lambda_px/py/pz` | Fitted Lambda momentum components used in the Lambda_b mass and observables. |
| `lb_proton_px/py/pz`, `lb_proton_energy`; `lb_pion_px/py/pz`, `lb_pion_energy` | Daughter four-momenta after the two-track vertex fit, with the selected mass assignment. |
| `lb_proton_d0`, `lb_pion_d0` | Signed transverse impact parameters at the fitted PV, in mm. Keep separate from their significances. |
| `lb_photon_px/py/pz`, `lb_photon_energy` | Selected reconstructed photon momentum and measured energy; no photon vertex fit is performed. |
| `lb_neutral_mass`, `lb_neutral_energy` | Neutral candidate mass and energy. Gamma mode uses the measured photon four-vector, so its reconstructed mass need not be exactly zero; eta mode uses the two-photon system. |
| `lb_same_hemisphere` | Whether fitted Lambda and candidate neutral have the same sign of projection on event thrust. This is the Boolean result of the configured hemisphere test. |
| `lb_lambda_thrust_cos`, `lb_neutral_thrust_cos` | Cosines of fitted Lambda and neutral momentum relative to event thrust. Useful for angular/hemisphere diagnostics. |
| `cos_theta_p` (`lb_cos_theta_p`) | Reconstructed helicity angle: proton or antiproton relative to minus the Lambda_b direction in the Lambda rest frame. It is reconstructed from the fitted candidate and is not a truth selection. |
| `lambda_mass`, `lambda_px/py/pz` | Selected fitted Lambda mass and momentum. The alias `Lambda0_E` is derived by the flattener from the fitted momentum and Lambda mass. |
| `lambda_vertex_primary` | Vertex fitter's primary/secondary classification code; the Λ⁰ pair is fitted as a secondary vertex. This is not a truth label. |
| `lambda_vertex_x/y/z`, `lambda_vertex_chi2` | Fitted Lambda0 secondary-vertex coordinates in mm and normalized fit χ². |
| `lambda_flight_rxy`, `lambda_flight_xyz` | Transverse and 3D distance from fitted PV to fitted Lambda0 vertex in mm. |
| `lambda_flight_rxy_sigma`, `lambda_flight_rxy_sig` | Projected transverse flight uncertainty in mm and flight-distance significance. The uncertainty combines PV and SV xy covariance along the flight direction. |
| `lambda_d0`, `lambda_d0_sigma`, `lambda_d0_sig` | Signed Lambda trajectory impact parameter relative to the PV, its projected uncertainty in mm, and signed significance. This is distinct from flight distance and from daughter-track d0. The uncertainty does not include Lambda-direction uncertainty. |
| `lambda_proton_d0sig`, `lambda_pion_d0sig` | Daughter-track absolute d0 significances relative to the fitted PV; used in the pre-fit track displacement requirement. |

`lambda_slot` is the flattened form of `lb_lambda_slot`. It gives the index in
the event's Lambda candidate vectors from which the per-Lambda fields above
were copied.

## Truth labels (evaluation only)

Truth columns are attached **after** the reconstructed candidate is built.
They are useful for efficiencies, fake/wrong-combination studies, and
resolution plots. Do not use them to define the reconstructed candidate
selection or as training inputs for a classifier intended to run on data.

For each leg (`proton`, `pion`, `photon`, and `photon2`), the following
columns are provided:

| Suffix | Meaning |
|---|---|
| `_reco_index` | Index in the reconstructed-particle collection. |
| `_mc_index` | Unique matched MC-particle index, or `-1` if absent, ambiguous, or not a stable final-state match. |
| `_mc_pdg` | Matched MC PDG ID; zero if no unique match. |
| `_mc_n_parents`, `_mc_parent_index`, `_mc_parent_pdg` | Number of MC parents and the first parent index/PDG ID when uniquely matched. |
| `_mc_grandparent_index`, `_mc_grandparent_pdg` | First grandparent index/PDG ID, if available. |
| `_reco_p`, `_reco_energy` | Reconstructed object's momentum magnitude and energy. |
| `_mc_p`, `_mc_energy`, `_mc_pt`, `_mc_eta`, `_mc_vertex_rxy` | Matched MC momentum, energy, transverse momentum, pseudorapidity, and production radius in mm. Missing values are `-999`. |
| `_mc_cos_opening` | Cosine between reconstructed and matched MC momentum directions. |

Additional candidate truth labels:

| Column | Meaning |
|---|---|
| `lambda_mass_hypothesis_correct`, `lb_mass_hypothesis_correct` | Whether the chosen daughter mass assignment agrees with the signed truth particle IDs. This tests identity only, not common ancestry. |
| `lambda_truth_matched` | Both daughters have unique matches with the correct signed p/pion IDs and share the same Lambda0 parent. |
| `lambda_truth_lambda_mc_index` | That common Lambda0 MC index, or `-1`. |
| `truth_matched` (`lb_truth_matched`) | Full candidate match: truth-matched Lambda0 and neutral share a correctly signed Lambda_b parent. |
| `lb_mc_index` (`lb_truth_lb_mc_index`) | Matched Lambda_b MC index, or `-1`. |
| `neutral_mc_index` (`lb_truth_neutral_mc_index`) | Matched neutral MC index for a fully truth-matched candidate, or `-1`. |
| `truth_cos_theta_p` (`lb_truth_cos_theta_p`) | Helicity angle calculated from true four-momenta for a fully matched candidate; otherwise `-999`. Compare with reconstructed `cos_theta_p` for angular response. |
| `n_truth_matched_lb` | Event scalar: number of fully truth-matched reconstructed Lambda_b candidates in the event. |

The association rule requires unique reconstructed↔MC links, a stable MC
particle, correct charge-sign assignment, and shared ancestry where stated.
For `--mode gamma`, all `photon2_*` truth values are sentinels because there is
no second photon.

## Isolation, photon pairing, recoil, and pointing observables

These columns are computed by `lb_candidate_observables.h` after candidate
construction. They are diagnostics; no isolation, pi0 veto, recoil, or
pointing-proxy cut is applied by this module. Isolation uses reconstructed
particles around the candidate photon. The selected photon itself is excluded.

| Column | Meaning and intended use |
|---|---|
| `iso_delphes`, `iso_delphes_available` | Delphes-provided isolation value and availability flag. In the current EDM4hep/IDEA output the source isolation branch is absent: value is `-999`, flag is `0`. Do not interpret this as zero isolation. |
| `iso_R02`, `iso_R03`, `iso_R05` | Sum of other reconstructed-object pT divided by candidate photon pT, for ΔR cones of 0.2, 0.3, and 0.5. |
| `iso_R02_E`, `iso_R03_E`, `iso_R05_E` | Same cone sums using object energy divided by candidate photon energy. |
| `iso_R03_noLambda`, `iso_R05_noLambda` | pT isolation ratios for ΔR 0.3/0.5 after removing the candidate proton and pion as well as the candidate photon. |
| `iso_R03_noLambda_E`, `iso_R05_noLambda_E` | Energy-based versions of the Lambda-daughter-removed isolation ratios. |
| `iso_charged`, `iso_neutral` | ΔR<0.3 pT sums of charged or neutral reconstructed objects, excluding the candidate daughters, divided by photon pT. |
| `iso_charged_E`, `iso_neutral_E` | Corresponding energy sums divided by photon energy. |
| `n_photons_DR03`, `n_photons_DR05` | Counts of other selected-container photons within ΔR<0.3/0.5 of the candidate photon. |
| `m_gg_best`, `dm_gg_pi0` | Mass of the selected other photon giving the closest same-event-thrust-hemisphere pair to the π0 mass, and its absolute mass difference from π0. `-999` means no eligible partner. |
| `E_gamma2`, `dr_gg`, `gamma2_index` | Energy, ΔR, and `ReconstructedParticles` index of that best selected-photon partner; sentinels when no partner exists. |
| `gamma_combo_other_gamma_mass`, `gamma_combo_other_gamma_index` | Per-candidate **list columns** containing masses and reconstructed indices for pairing the candidate photon with every other raw type-22 reconstructed photon. This is broader than the selected-photon π0-partner search and can support π0/η veto studies. |
| `m_LamGam` | Reconstructed Lambda+photon mass (same quantity as candidate `lb_mass`). |
| `m_rec`, `dm_rec` | Recoil mass from the initial-state four-vector minus the ROE in the hemisphere opposite the Lambda candidate, and its difference from the nominal Lambda_b mass. |
| `m_rec_all` | Recoil mass after subtracting all other reconstructed objects from the initial state, excluding candidate proton, pion, and photon. |
| `deltaE`, `px_bal`, `py_bal`, `pz_bal`, `deltaP` | Energy and three-momentum balance of reconstructed signal plus opposite-hemisphere ROE against the nominal 91.2 GeV initial state; `deltaP` is the magnitude of the balance vector. |
| `cos_rec_sig` | Cosine between the signal candidate momentum and the opposite-hemisphere recoil momentum. |
| `Estar_gamma`, `Estar_gamma_rec` | Candidate photon energy in the reconstructed signal rest frame and in the recoil-system rest frame, respectively. |
| `dEstar`, `dEstar_rec` | Those photon energies minus the expected two-body Lambda_b→Lambdaγ energy computed from configured nominal masses. |
| `E_same`, `m_same` | Energy and invariant mass of the ROE in the same thrust hemisphere as the Lambda candidate. |
| `roe_thrust_x/y/z`, `roe_n_same`, `roe_n_other` | Thrust axis and object multiplicities after removing the candidate proton, pion, and photon. |
| `lambda_pv_cos`, `lambda_pv_dca` | Cosine between fitted Lambda momentum and PV→SV flight vector; and the distance of the Lambda flight line from the PV. These describe Lambda pointing/displacement, not a separately fitted Lambda_b vertex. |
| `dca_Lam_gamma`, `Lxyz_implied`, `cos_dir_implied` | Approximate closest approach of the Lambda line from its SV and photon line from the PV, implied 3D distance, and implied Lambda_b direction cosine. The photon origin is assumed to be PV and this is a geometric proxy, not a vertex fit. |
| `pointing_derived_in_flattening` | `1` if `lambda_pv_cos` and `lambda_pv_dca` were derived by the Python flattener for an older ROOT snapshot; `0` if they were already present in the ROOT tree. |

Ratios and angular quantities may be `-999` when the denominator or geometry
is undefined. The cone sizes and nominal masses come from
`config/lb_observables.json`.

## LHCb-style aliases

The aliases are convenience names and are added without dropping the original
columns. `P`, `Pt`, `Eta`, and `Phi` are derived from the listed components;
`E` is copied from reconstructed energy where available.

| Alias | Source / meaning |
|---|---|
| `Lb_M`, `Lb_Px`, `Lb_Py`, `Lb_Pz`, `Lb_P`, `Lb_Pt`, `Lb_Eta`, `Lb_Phi`, `Lb_E` | Lambda_b candidate mass and reconstructed kinematics. |
| `Lb_ChargeSign` | `lb_sign`, ±1 candidate charge/hypothesis convention. |
| `Lambda0_M`, `Lambda0_Px/Py/Pz/P/Pt/Eta/Phi/E` | Fitted Lambda0 pπ mass and momentum. Its alias energy is derived from fitted momentum and selected Lambda mass. |
| `Lambda0_FlightRxy`, `Lambda0_Rxy` | Transverse PV-to-SV flight distance (same source value). |
| `Lambda0_FlightXYZ`, `Lambda0_FlightRxySigma`, `Lambda0_FlightRxySignificance` | 3D flight, transverse uncertainty, transverse significance. |
| `Lambda0_d0`, `Lambda0_d0Sigma`, `Lambda0_d0Significance` | Lambda trajectory d0 relative to PV, uncertainty, significance. |
| `Lambda0_PV_DCA`, `Lambda0_PV_Cos` | Lambda flight-line DCA to PV and pointing cosine. |
| `Lambda0_SV_X/Y/Z`, `Lambda0_VertexChi2` | Fitted Lambda secondary vertex and fit quality. |
| `PV_X/Y/Z` | Reconstructed primary vertex in mm. |
| `Proton_Px/Py/Pz/P/Pt/Eta/Phi/E`, `Proton_d0`, `Proton_d0Significance` | Selected proton-hypothesis daughter kinematics and impact parameter. |
| `Pion_Px/Py/Pz/P/Pt/Eta/Phi/E`, `Pion_d0`, `Pion_d0Significance` | Selected pion-hypothesis daughter kinematics and impact parameter. |
| `Gamma_Px/Py/Pz/P/Pt/Eta/Phi/E` | Measured candidate photon kinematics. `Gamma_RecoIndex` is its original reconstructed-particle index. |
| `Gamma_IsoR02/R03/R05`, `Gamma_IsoR03_NoLambda`, `Gamma_IsoR05_NoLambda` | Alias names for the photon isolation ratios defined above. |
| `Gamma_NPhotonsDR03/DR05` | Nearby selected-photon counts. |
| `GammaGamma_M_BestPi0`, `GammaGamma_DeltaM_Pi0`, `GammaGamma_PartnerEnergy`, `GammaGamma_DeltaR`, `GammaGamma_PartnerIndex` | Best selected photon-pair/pi0 diagnostic and its partner properties. |
| `Gamma_Combo_OtherGamma_M`, `Gamma_Combo_OtherGamma_Index` | List-column aliases for all-other-raw-photon pair masses and indices. |

## Flattening and analysis guidance

The candidate vectors in ROOT are flattened in lockstep using each candidate
slot. Lambda vertex variables are first indexed with `lb_lambda_slot`; leg
truth information is indexed using each candidate's reconstructed-object
index. The truth joins do not filter rows. Scalar ROOT branches are copied to
each row, so event-level quantities are intentionally duplicated when an
event has multiple candidates.

For signal/background studies, keep reconstructed observables and truth labels
separate. Use `truth_matched`, `lambda_truth_matched`, and the ancestry columns
to evaluate the sample, not as BDT features. Exclude identifiers such as
`source_id`, `event_entry`, candidate slots, object indices, and truth fields
from training. Split train/test by event (and preferably source file/seed) so
multiple candidates from one event cannot leak across samples. For an event
yield, count unique events or apply a documented candidate-weighting rule;
the table itself is candidate-based. Forced signal-sample row counts are not
physical Z→bb rates.

The ROOT reconstruction tree is the authoritative source for its stored
observables. `flatten_candidates.py` performs row alignment, preserves scalar
event fields, creates the aliases and, for older ROOT files missing the two
Lambda-PV pointing fields, derives them from the fitted Lambda momentum and
PV/SV positions. Metadata in the Parquet footer records the mode and input
source; the summary JSON records event/candidate totals and truth-matched
candidate totals.

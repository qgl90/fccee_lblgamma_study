# Post-preselection BDT inputs and their contracts

The binary BDT is trained after the existing stage-1 Λγ reconstruction and
an offline **fitted** Λ mass window `|m(pπ)−1.115683|<0.010 GeV`. The original
candidate window was `4.9≤m(Λγ)≤6.3 GeV`; the requested scenario uses
`4.5≤m(Λγ)≤6.5 GeV` and ±15 MeV in m(pπ). Both keep the vertex/displacement requirements,
and same-thrust-hemisphere requirement remain in force. All cuts use
reconstructed quantities. The target label uses truth only after candidates
are made: full direct Λb→Λ(pπ)γ matches are signal; Winter2023 inclusive
Z→bb combinations are background. Λb→Λη(γγ) feed-down and wrong
combinations in forced samples are scored but held out of binary training.

The trainer reads the `FEATURES` table from
`studies/reconstruction/prepare_training_inputs.py`, replaces missing
`−999` values with NaN for XGBoost, and replaces the two *signed* thrust
cosines by three axis-sign-invariant functions. The historical snapshot had 39
inputs; the current feature table has 41
reconstructed inputs. Units below follow the flattened Parquet columns.

| Inputs | Definition and reason to inspect |
|---|---|
| `lambda_mass` [GeV] | Fitted-momentum pπ mass under the selected proton/pion hypothesis. Variation **within** the ±10 MeV window still encodes Λ quality. Check mass sculpting. |
| `lb_pt` [GeV], `photon_reco_energy` [GeV] | Reconstructed Λγ transverse momentum and selected photon energy; constrain candidate kinematics without using its invariant mass. The IDEA photon container already has an energy threshold. |
| `lambda_vertex_chi2`, `lambda_flight_rxy` [mm], `lambda_flight_rxy_sig` | Two-track fitted SV quality and PV→SV transverse flight/significance. The baseline already requires χ²≤9, flight≥0.3 mm, significance≥2. |
| `proton_d0sig`, `pion_d0sig` | Absolute daughter-track transverse impact-parameter significance at the PV; each is already ≥3. Both charges are accepted. |
| `lambda_d0` [mm], `lambda_d0_sigma` [mm], `lambda_d0_sig` | Signed transverse impact parameter of the fitted Λ flight line relative to the PV, its uncertainty, and signed significance. The uncertainty projects fitted PV and SV xy covariances; Λ direction uncertainty is not included. `lambda_d0` and `lambda_d0_sig` enter the current feature table. |
| `lambda_pv_dca` [mm] | Distance of the **fitted Λ flight line** to the PV. This is a reco geometry diagnostic, not a requirement that a Λ from displaced Λb point to the PV. Validate its modeling before trusting a high-gain split. |
| `lambda_thrust_abs`, `neutral_thrust_abs`, `hemisphere_product` | `|cos(Λ,thrust)|`, `|cos(γ,thrust)|`, and their product. The full-event thrust axis has an arbitrary sign; these functions do not. The product is positive by stage-1 selection but its size measures alignment. |
| `iso_R02`, `iso_R03`, `iso_R05` | Sum of reconstructed-particle pT in ΔR<0.2/0.3/0.5 around the candidate photon, divided by photon pT; the candidate photon is excluded. These **raw** cones may contain the Λ daughters. |
| `iso_R03_noLambda`, `iso_R05_noLambda` | Same pT cones with the candidate proton and pion also removed. These are the preferred auxiliary photon-isolation measures. |
| `iso_R03_noLambda_E`, `iso_R05_noLambda_E` | Corresponding sum of reconstructed-particle energy divided by photon energy. |
| `iso_charged`, `iso_neutral` | R=0.3 no-Λ pT ratio split into charged and neutral reconstructed particles. Neutral means photons and neutral hadrons in the event collection. |
| `n_photons_DR03`, `n_photons_DR05` | Counts of other selected photons within ΔR<0.3/0.5; the candidate photon is excluded. |
| `dm_gg_pi0` [GeV], `E_gamma2` [GeV], `dr_gg` | For the other selected same-hemisphere photon whose pair mass is closest to mπ⁰: absolute mass difference, partner energy, and photon-pair ΔR. No partner is stored as missing, not as a passing veto. This is a resolved-partner diagnostic, not a π⁰ or η veto. |
| `m_rec` [GeV] | Mass of `pZ−p_other`, with `pZ=(91.2,0,0,0)` GeV. The other-side momentum is built after removing the candidate p, π, γ and reclustering ROE thrust. It is broad even for signal. |
| `m_rec_all` [GeV] | Mass of `pZ−Σp(ROE)` using all remaining reconstructed particles; diagnostic for visible-energy closure. |
| `deltaE` [GeV] | `E(Λγ)+E(other hemisphere)−91.2`; the signal median is not zero because of other signal-side fragments and missing particles. |
| `px_bal`, `py_bal`, `pz_bal`, `deltaP` [GeV] | Components and magnitude of `p(Λγ)+p(other hemisphere)−pZ`. Correlated closure observables; their redundancy is monitored through importance and held-out validation. |
| `cos_rec_sig` | Cosine between three-momenta of recoil candidate `pZ−p_other` and selected `pΛ+pγ`. |
| `Estar_gamma_rec` [GeV] | Candidate photon energy boosted into the recoil-system rest frame; broad because the recoil is not a kinematic fit. |
| `E_same` [GeV], `m_same` [GeV] | Energy and invariant mass of remaining ROE particles on the candidate Λ side, after removing p, π, γ. These measure same-b fragmentation and activity. |
| `roe_n_other`, `roe_n_same` | Reconstructed-particle multiplicity in opposite and same ROE hemispheres. |

The input schema deliberately excludes `lb_mass`/`m_LamGam`, reconstructed
and truth `cos_theta_p`, MC ancestry, the Λb charge sign, event/source IDs,
candidate multiplicity, and the photon-origin proxies that assume a ray
from the PV. Excluding the fit variables reduces direct sculpting, but does
**not** prove the BDT leaves their distributions unchanged: `lb_pt`, photon
energy, and event closure are correlated with mass and angle. Compare
held-out mass/angle shapes and efficiency versus generated cosθp at each
score cut.

Zbb is split by **source ROOT file**: files 0–6 for training, 7 for
validation, and 8–9 for test in the ten-file baseline. Forced PHSP signal
is split by event hash. Multiple candidates from an event stay in the same
split. The independent HELAMP sample and forced Λη sample are evaluation
samples. The 100k one-file `--pilot` mode uses only an event split and is
explicitly insufficient for a physics rejection claim.

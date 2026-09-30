# Delphes charged-particle and photon response

For the analysis-wide review gates and detector-scenario protocol, see
[`docs/ANALYSIS_WORKFLOW.md`](../../docs/ANALYSIS_WORKFLOW.md).

`resolutions.py` reads every event in the local Λb → Λγ EDM4hep file. It makes no Λb decay selection, so tracks and photons from the rest of each event are included.

## Run

From the repository root, in a fresh shell:

```bash
source external/FCCAnalyses/setup.sh
fccanalysis run analysis/studies/resolutions.py \
  --files-list outputs/delphes/Lb2LambdaGamma_nev500000_IDEA_edm4hep.root \
  --output Lb2LambdaGamma_resolutions.root --ncpus 4
```

The analysis script sets `outputDir = "outputs/analysis/studies"`, so `--output` is just a file name. The result is `outputs/analysis/studies/Lb2LambdaGamma_resolutions.root`. Add `--nevents 100` for a quick trial and use another output name. This requires the pinned local FCCAnalyses `pre-edm4hep1` build described in the root README.

## What is stored

The output has an `events` tree with one row per input event. `event_entry` identifies the input entry. The `track_*` and `gamma_*` branches are vectors, with one element per stable generated charged particle or photon, respectively. They include all generated candidates, even when no reconstruction match exists.

| Branches | Meaning |
| --- | --- |
| `track_truth_p`, `track_truth_pt`, `track_truth_eta`, `track_pdg`, `track_truth_charge`, `track_truth_rxy` | Generated charged-particle kinematics, identity, and production radius from detector origin in mm |
| `track_reco_p`, `track_reco_pt`, `track_reco_eta`, `track_reco_charge` | Matched charged reconstructed-particle kinematics |
| `track_dp_rel`, `track_dpt_rel` | `(p_reco − p_true)/p_true`, `(pT_reco − pT_true)/pT_true` |
| `track_dqoverpt` | `q_reco/pT_reco − q_true/pT_true`, in `1/GeV` |
| `gamma_truth_e`, `gamma_truth_pt`, `gamma_truth_eta`, `gamma_truth_phi` | Generated photon kinematics |
| `gamma_reco_e`, `gamma_reco_pt`, `gamma_reco_eta`, `gamma_reco_phi` | Matched reconstructed photon kinematics |
| `gamma_dE_rel` | `(E_reco − E_true)/E_true` |
| `gamma_signal` | Stable direct photon from a `|PDG|=5122` parent with a direct `|PDG|=3122` daughter; includes charge conjugates |
| `*_mc_index`, `*_reco_index`, `*_n_links`, `*_matched` | Truth/reco association diagnostics; a unique link sets `matched = 1` |
| `gamma_selected` | The matched photon is also in the card's `PhotonEfficiency/photons` collection |
| `n_reco_track_candidates`, `n_reco_photon_candidates`, `n_selected_photons` | Event-level reconstructed candidate counts |

Missing or ambiguous matches have `reco_index = -1`, `matched = 0`, and `-999` for reco/residual floats. Use `matched == 1` when plotting response. `n_links > 1` exposes ambiguous truth links rather than selecting one arbitrarily.

The ROOT residual branches are stored as dimensionless fractions. The standalone plotting scripts multiply relative residuals by 100 before fitting, and report their Gaussian widths in percent. `track_dqoverpt` remains in `1/GeV`.

The matching uses the EDM4hep `MCRecoAssociations` collection. A track candidate is a charged `ReconstructedParticle` with a track relation; a photon candidate is a neutral `ReconstructedParticle` with type 22. `Photon#0` points to the photons that passed the IDEA card's `PhotonEfficiency` module. The card sets charged tracking efficiency to zero for `pT < 0.1 GeV` or `|eta| > 2.56`, and photon selection to zero for `E < 2 GeV` or `|eta| > 3.0`. The selected-photon flag therefore has a different denominator from raw reconstructed photon matching.

For photons within `|eta| ≤ 3`, the card's ECAL energy-smearing term is `sqrt((0.005 E)^2 + (0.03 sqrt(E))^2 + 0.002^2)` with `E` in GeV. The actual `gamma_dE_rel` distribution can also reflect clustering and matching, so compare its width in truth-energy and `eta` bins rather than expecting this term alone to describe every candidate.

The ECAL reference in the plots is `100 * sigma_E / E` in percent. The barrel (`|eta| <= 0.88`) and endcap (`0.88 < |eta| <= 3`) use the same formula. The card cites [Lucchini et al., arXiv:2008.00338](https://arxiv.org/abs/2008.00338), Eq. 4.1. Charged momentum has no equivalent single formula in this card: `TrackCovariance TrackSmearing` uses its geometry, material, hit resolutions, a 2 T field, and a six-hit minimum. The card's 100% in-acceptance charged tracking efficiency is an input gate; observed MC-to-reco match fractions include propagation, finite geometry, and association.

This measures the final charged reconstructed-particle and photon response after the card's tracking and calorimeter chain. The EDM4hep file does not expose the raw Delphes `TrackSmearing/tracks` collection as a standalone `Track` collection, so the charged residual includes subsequent energy-flow handling. Bin the residuals against truth momentum and `eta` for the resolution study; keep efficiency and response comparisons separate.

The standalone uproot/awkward plotting code and its 200,000-pair workflow are in [studies/resolutions/README.md](../../studies/resolutions/README.md).

## Displaced V0 daughter study

`displaced_daughters.py` produces one vector entry for each stable direct proton or pion daughter of a generated Lambda0, or each stable direct pion daughter of a generated K0S. It records MC parent identity, true production vertex `(x, y, z, Rxy)` in millimetres, kinematics, the charged track match flag, and momentum residuals. Use `--nevents 10` for the native small run; see the [standalone plotting instructions](../../studies/resolutions/README.md#displaced-lambda0-and-k0s-daughters) for complete commands and output definitions.

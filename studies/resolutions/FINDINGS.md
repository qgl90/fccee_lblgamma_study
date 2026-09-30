# IDEA Delphes response: 500,000-event Gamma sample

The source is `outputs/delphes/Lb2LambdaGamma_nev500000_IDEA_edm4hep.root`
(500,000 events). Inclusive extraction read 12,000 events and retained 200,000
uniquely matched charged particles and 200,000 uniquely matched photons.
The displaced study read all 500,000 events. The Eta production contains a
separate 500,000 events and was not used for these response plots.

## Card input versus measured response

| Quantity | IDEA card input | What is measured here |
| --- | --- | --- |
| Charged tracking | Efficiency is 1 for input $p_T\geq0.1$ GeV and $|\eta|\leq2.56$, and 0 outside; `TrackCovariance` uses a 2 T field, layered geometry, material and hit resolutions, with at least 6 hits. There is no scalar $\sigma_p/p$ formula. | Gaussian core width of $(p_{\rm reco}-p_{\rm true})/p_{\rm true}$ and analogous $p_T$ residual, after the complete Delphes-to-EDM4hep chain. |
| ECAL photons | $\sigma_E=\sqrt{(0.005E)^2+(0.03\sqrt E)^2+0.002^2}$ GeV for $|\eta|\leq3$, with $E$ in GeV. Barrel and endcap coefficients are identical. `PhotonEfficiency` selects reconstructed photons with $E\geq2$ GeV and $|\eta|\leq3$ at 0.99 probability. | Gaussian core width of $(E_{\rm reco}-E_{\rm true})/E_{\rm true}$; the dashed curve is $100\sigma_E/E$ in percent. Selected and raw reconstructed photons are shown separately. |

The card attributes its ECAL crystal expression to [Lucchini et al.,
arXiv:2008.00338](https://arxiv.org/abs/2008.00338), Eq. 4.1. Its
absolute-energy terms are exactly the ones evaluated by the plotting code.
The measured photon points also include clustering and matching.
For example, the fitted photon core width in the bin centered at 0.995 GeV
is 3.048%, compared with 3.056% from the card term evaluated at the bin
center. The difference varies with energy and the truth-energy distribution
inside each bin, so the reference is a guide rather than a fit to the points.

## Direct signal photons

The full-event extraction tags a stable direct photon from a `|PDG|=5122`
parent only when that parent also has a direct `|PDG|=3122` daughter.
Across 500,000 events it finds 500,070 such photons; 59 events have more
than one and no event has zero. The raw unique match count is 496,244 and
the `PhotonEfficiency` selected count is 461,798. Within the generated
$E\geq2$ GeV, $|\eta|\leq3$ region, 466,837 photons are generated,
466,472 match uniquely (99.92%) and 461,490 are selected (98.85%).
These are truth-bin fractions; the card's 2 GeV and eta selection is
evaluated on reconstructed candidates. The signal-only energy and signed-eta
plots show these fractions, their generated and matched count distributions,
and the raw and selected resolution curves.

## Acceptance and matching

For generated charged particles with true $p_T\geq0.1$ GeV, the unique
MC-to-reco match fraction is 98.0% at $|\eta|<2$ (203,634/207,781), 92.2%
at $2\leq|\eta|<2.56$ (5,382/5,838), and zero outside $|\eta|=2.56$
(0/2,028). For generated photons with true $E\geq2$ GeV and $|\eta|<2$,
raw matching is 99.6% (29,552/29,660) and `PhotonEfficiency` selected
matching is 98.0% (29,067/29,660). These are checks in **truth** bins;
the card's photon selection operates on reconstructed energy and angle.
The signed-$\eta$ plots show both acceptance edges and the generated
distribution beneath each match-fraction curve.

"Matched" requires exactly one `MCRecoAssociations` link to a suitable
`ReconstructedParticle`. Charged candidates need nonzero charge and a track
relation. Photon candidates need type 22 and zero charge. Missing and
ambiguous links are excluded from resolution fits. Match fractions therefore
combine response, finite geometry, reconstruction and association; they are
not a direct readout of the card's nominal efficiency probability.

## Displaced daughters

| Stable direct daughter | Generated | Matched in card fiducial region | Fiducial generated | Fiducial match fraction |
| --- | ---: | ---: | ---: | ---: |
| $\Lambda^0\to p$ | 605,299 | 508,767 | 594,874 | 85.5% |
| $\Lambda^0\to\pi$ | 605,172 | 486,799 | 577,517 | 84.3% |
| $K^0_S\to\pi$ | 606,351 | 566,990 | 575,230 | 98.6% |

These populations include charge conjugates and $V^0$ particles from the
whole event. The comparison plot includes all charged particles and a
near-origin subset whose MC production radius is below 1 mm. That subset
is a truth-position category, not a reconstructed primary-vertex assignment.
The displaced match fraction is high at small production radii and falls
strongly as the production point approaches and passes the outer tracker.
In the shared radius comparison, the Lambda proton match fraction is 98.7%
for 209--520 mm, 93.2% for 520--1,296 mm, 45.2% for 1,296--3,226 mm,
and zero for 3,226--8,032 mm (all with at least 25,000 generated protons).
The inclusive tracks follow a similar radial trend. Counts in the inclusive
and displaced histograms come from 12,000 and 500,000 events respectively,
so their absolute heights should not be compared without normalization.
The momentum resolution also depends on $p_T$ and signed $\eta$; compare
groups in common truth-$p_T$ slices rather than interpreting the inclusive
width as an intrinsic species effect.

Plots, per-bin counts, Gaussian fit diagnostics and CSV tables are under
`outputs/plots/resolutions/`; the overview deck is `slides/resolution.tex`.

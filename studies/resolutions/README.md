# Standalone detector-resolution plotting workspace

This directory uses Python, uproot, awkward, NumPy, SciPy, Matplotlib, and mplhep with its LHCb2 style. It does not import ROOT or FCCAnalyses. Reusable methods live in `resolution_tools/`: `io.py` reads event-vector branches, `fitting.py` fits Gaussian cores and extracts binned widths, and `plotting.py` provides 1D, scatter, resolution, and efficiency plots and maps.

## Make a small FCCAnalyses input first

Run from the repository root. The local `pre-edm4hep1` build is required for this extraction step:

```bash
source external/FCCAnalyses/setup.sh
fccanalysis run analysis/studies/resolutions.py \
  --files-list outputs/delphes/Lb2LambdaGamma_nev500000_IDEA_edm4hep.root \
  --output Lb2LambdaGamma_resolutions_10events_from500k.root --nevents 10 --ncpus 1
```

In this FCCAnalyses version, `--nevents 10` applies `RDataFrame.Range(0, 10)`. Once that succeeds, use 12,000 input events:

```bash
fccanalysis run analysis/studies/resolutions.py \
  --files-list outputs/delphes/Lb2LambdaGamma_nev500000_IDEA_edm4hep.root \
  --output Lb2LambdaGamma_resolutions_12000events_from500k.root --nevents 12000 --ncpus 1
```

The 12,000-event file supplies the 200,000 matched tracks and photons used in the plotting cap. FCCAnalyses writes both files under `outputs/analysis/studies/` because `resolutions.py` sets that `outputDir`. Do not include the directory in the relative `--output` name.

## Run the Python plots

Use a separate shell without a sourced Key4hep environment. The existing `myenv` has the required Python packages:

```bash
env -u PYTHONPATH -u PYTHONHOME myenv/bin/python \
  studies/resolutions/run_study.py \
  --input outputs/analysis/studies/Lb2LambdaGamma_resolutions_10events_from500k.root \
  --output-dir outputs/plots/resolutions/smoke \
  --target-pairs 500 --min-fit-entries 20

env -u PYTHONPATH -u PYTHONHOME myenv/bin/python \
  studies/resolutions/run_study.py \
  --input outputs/analysis/studies/Lb2LambdaGamma_resolutions_12000events_from500k.root
```

For an independent environment, install this directory with `python -m pip install -e studies/resolutions`, then run `python studies/resolutions/run_study.py`. The default output is `outputs/plots/resolutions/Lb2LambdaGamma/`, and default cap is **200,000 matched tracks and 200,000 matched photons**. The reader processes events in file order until both categories reach the cap, then trims each matched array to exactly the cap. All generated-particle vectors from the events read are retained for match-fraction denominators.

The script writes PNG plots, CSV tables of binned Gaussian widths, and `summary.json`. Gaussian fits use a central window based on the median and median absolute deviation within each truth momentum or energy bin. Relative momentum and energy residuals are multiplied by 100 before fitting, so their plot axes and CSV values are in **percent**; the curvature residual stays in `1/GeV`. Resolution axes start at zero. Resolution points have horizontal errors spanning the full truth-variable bin and vertical fit errors; the grey histogram uses a twin y-axis to show residual entries per bin. Each resolution PNG has a companion `*_fit_distributions.png` showing the fit-window residual histogram and Gaussian curve in every bin, with the core count and chi2/ndf. Sparse or failed bins show their distribution without a fitted curve. This is a *core resolution* estimate; broad tails, unmatched objects, and reconstruction efficiency are separate quantities. The 1D plots combine all momenta or energies and show distributions without a single fitted width. The photon resolution plots overlay the ECAL energy term set in `cards/card_IDEA.tcl`. Their measured widths can also include clustering and matching effects.

The inclusive charged-track outputs include `track_resolution_vs_eta.png` for transverse momentum and `track_dp_resolution_vs_eta.png` for total momentum, alongside the pT scan. Signed eta scans show the full plotted range, including bins outside card acceptance. Photon resolution and match fractions also have signed eta scans. Match-fraction plots show generated and matched counts on a twin axis and horizontal bin errors. The ECAL reference is exactly `100*sqrt(E^2*0.005^2+E*0.03^2+0.002^2)/E` in percent for `|eta|<=3`, with the same coefficients in barrel and endcap. The card cites [Lucchini et al., arXiv:2008.00338](https://arxiv.org/abs/2008.00338), whose Eq. 4.1 has these terms.

`uproot.open(..., handler=uproot.source.file.MemmapSource)` is intentional: it reads the local ROOT file without relying on the default fsspec asynchronous source used in this CERN Python environment. Awkward arrays preserve the per-event particle vectors until the matched pairs are flattened for fitting.

## Direct signal photons

The event-wide study includes all stable generated photons. For the specific
`Lambda_b -> Lambda0 gamma` photon, extract all 500,000 events and then run
the signal-only plotting script:

```bash
source external/FCCAnalyses/setup.sh
fccanalysis run analysis/studies/resolutions.py \
  --files-list outputs/delphes/Lb2LambdaGamma_nev500000_IDEA_edm4hep.root \
  --output Lb2LambdaGamma_resolutions_500000events.root --ncpus 4
```

In a separate shell without Key4hep sourced:

```bash
env -u PYTHONPATH -u PYTHONHOME myenv/bin/python \
  studies/resolutions/run_signal_photons.py
```

`gamma_signal` requires a stable photon directly under a `|PDG|=5122`
parent that also has a direct `|PDG|=3122` daughter, following the EDM4hep
MC daughter indices. The script reads the entire output, not the 200,000-pair
inclusive plotting cap. It plots raw unique-match and `PhotonEfficiency`
selected fractions versus generated photon energy and signed eta, with the
generated and matched bin counts on a twin axis. The two fractions have the
same generated-photon denominator. It also plots raw and selected signal
photon energy resolution in percent, against the card's ECAL term. Results
are in `outputs/plots/resolutions/signal_photons/`.

## Displaced Lambda0 and K0S daughters

The separate FCCAnalyses script `analysis/studies/displaced_daughters.py` selects stable, direct `Lambda0 -> p pi` and `K0S -> pi pi` daughters using MC parent links. Both charge conjugates are included. It stores the true daughter production position in millimetres, truth kinematics, reco match flag, and matched track residuals. The sample includes V0s from the entire event, not just the signal Lambda0.

Run the 10-event check and then the full local sample from the repository root:

```bash
source external/FCCAnalyses/setup.sh
fccanalysis run analysis/studies/displaced_daughters.py \
  --files-list outputs/delphes/Lb2LambdaGamma_nev500000_IDEA_edm4hep.root \
  --output Lb2LambdaGamma_displaced_10events_from500k.root --nevents 10 --ncpus 1

fccanalysis run analysis/studies/displaced_daughters.py \
  --files-list outputs/delphes/Lb2LambdaGamma_nev500000_IDEA_edm4hep.root \
  --output Lb2LambdaGamma_displaced_500000events.root --ncpus 4
```

Use a separate shell for the standalone plots:

```bash
env -u PYTHONPATH -u PYTHONHOME myenv/bin/python \
  studies/resolutions/run_displaced_daughters.py \
  --input outputs/analysis/studies/Lb2LambdaGamma_displaced_500000events.root
```

The default output is `outputs/plots/resolutions/displaced_daughters/`, with separate `lambda_proton`, `lambda_pion`, and `kshort_pion` directories. Each contains match fraction and Gaussian core width versus truth pT, signed eta, production radius Rxy, and |z|, plus total-momentum width versus p **and signed eta**, curvature width versus pT, a production-position scatter, and a two-dimensional match-fraction map in Rxy and signed eta. Radius and |z| scans also have three truth-pT slices to reduce momentum-composition effects. Every resolution curve has a matching `*_fit_distributions.png` grid and CSV table; tables include bin counts and fit chi2/ndf, with empty fit fields indicating insufficient statistics or a failed fit. Relative widths in these plots and tables are in percent.

The match fraction counts an exactly-one-to-one MC association to a charged reconstructed particle with a track. It is a reconstruction-and-association measure, not an independently measured pattern-recognition efficiency. Vertex scans require truth pT >= 0.1 GeV and |eta| <= 2.56, the card's charged-hadron acceptance. The plotted production coordinates are absolute MC positions relative to the detector origin, not distances from a reconstructed primary vertex. The radial width of the detector and the kinematic mix both affect these curves, so use the pT-sliced scans and the two-dimensional map when interpreting a radius trend.

## Compare all tracks with displaced daughters

Run the standalone overlay study after the two analyses above:

```bash
env -u PYTHONPATH -u PYTHONHOME myenv/bin/python \
  studies/resolutions/run_comparison.py \
  --inclusive outputs/analysis/studies/Lb2LambdaGamma_resolutions_12000events_from500k.root \
  --displaced outputs/analysis/studies/Lb2LambdaGamma_displaced_500000events.root
```

It writes `outputs/plots/resolutions/comparison/`: overlays of all matched charged tracks, near-origin charged tracks (MC production `Rxy < 1 mm`), Lambda0 protons, Lambda0 pions, and K0S pions for relative pT resolution versus pT and signed eta, and total-momentum resolution versus signed eta. A 1--5 GeV pT slice of the latter helps separate angular behaviour from the changing momentum spectrum. Match-fraction comparisons versus pT, signed eta, and MC production `Rxy` use generated particles as denominators; the radius plot requires true pT >= 0.1 GeV and |eta| <= 2.56 for every group. Bins with fewer than 30 generated particles remain in the CSV but are not plotted. The twin count axis shows generated (solid) and matched (dashed) distributions for each group. Each comparison has a CSV with fitted percent widths or match fractions, bin counts and fit quality; resolution comparisons also have per-sample residual fit grids. The inclusive input uses 12,000 events and a 200,000-track cap; displaced inputs use the full 500,000-event sample. The plotted curves share the same truth-variable bin edges and fiducial selection, but they are not identical event sets. These overlays describe final reconstructed-particle response for each population, rather than an isolated detector-resolution term.

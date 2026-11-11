# Offline photon-pointing geometry: 200-event audit

Start from the [checkpoint and resume procedure](../docs/PHOTON_POINTING_CHECKPOINT_2026-10-05.md)
for the complete geometry, tuple-recovery and post-BDT application contract.

Run from the repository root using the existing Stage 0 Λη Physics chunk.
This reads 200 events and does not invoke Stage 1 or change a selection.

```bash
MPLCONFIGDIR=/tmp/lblgamma_mpl_pointing XDG_CACHE_HOME=/tmp/lblgamma_cache_pointing \
  myenv/bin/python studies/resolutions/audit_calorimeter_geometry.py \
  --input outputs/delphes/chunks/Lb2LambdaEtaPhysics_nev100000_chunk0_IDEA_edm4hep.root \
  --events 200 --card cards/card_IDEA.tcl \
  --output-json docs/data/v3_photon_pointing_geometry_200events/geometry_audit.json \
  --output-figure docs/figures/v3_photon_pointing_geometry_200events.png
```

The script caps inspection at 200 events, uses the shared v3 mplhep plotting
style, and uses synchronous `MemmapSource` reads for the local/mounted ROOT
file. It estimates the radius and endcap location from the most populated
10 mm-rounded position bins, then counts hits within 1 mm of either surface.
The JSON records the input and card SHA256 hashes. File hashing reads bytes
for provenance; only the first 200 events enter the geometry calculation.

Expected output: 4,472 hit records, all on the union of a 2,250 mm radius
barrel and endcaps at ±2,500 mm within 1 mm. There are 4,052 EFlow photons;
their position/direction-error fields and the hit energies are zero.

The [PI review and figure](../docs/STAGE2_V3_PHOTON_POINTING_INPUT_AUDIT_2026-10-05.md)
describe the limitations and the proposed conditional 1 mrad pointing study.
The geometry is a surface model for that approximation. True photon vectors
still need a validated join to existing Stage 0 records; Stage 1 will not be
rerun. Do not use the absence of a truth association to silently drop a
background candidate when estimating rejection.

## Pointing resolution pilot

The [four-parameter geometry config](../config/photon_pointing_idealized_v3.json)
includes an effective 249.554 mm endcap opening derived from |eta|<=3.
The [reusable module](../studies/resolutions/photon_pointing.py) projects
origin-based reconstructed rays, applies tangent-plane angular smearing and
computes 3D/transverse photon line impact parameters. It accepts arrays for
subsequent use on joined post-selection rows, including a fitted PV.

Run the analytic checks, then the 200-event object-response pilot:

```bash
myenv/bin/python studies/resolutions/test_photon_pointing.py
MPLCONFIGDIR=/tmp/lblgamma_mpl_pointing XDG_CACHE_HOME=/tmp/lblgamma_cache_pointing \
  myenv/bin/python studies/resolutions/run_photon_pointing_pilot.py \
  --input /eos/lhcb/lbdt3/user/rquaglia/fcc_ee/lblgamma/outputs/Lb2LambdaGammaPhysics_nev100000_IDEA_edm4hep.root \
  --config config/photon_pointing_idealized_v3.json \
  --events 200 --output-dir docs/data/v3_photon_pointing_200events
```

The seed and sigma convention are in the config. This pilot uses all uniquely
associated stable photons among reconstructed type-22 objects in the first
200 signal events, before Stage 1 selection, with PV fixed to (0,0,0).
Its photon categories are diagnostic truth labels. The saved Parquet retains
one row per matched photon, true/reconstructed vectors, production vertex,
predicted hit, aperture status, hypothetical momentum and both IP measures
under every resolution hypothesis. JSON accounts for the unmatched objects.

The [pilot review and figure](../docs/STAGE2_V3_PHOTON_POINTING_PILOT_2026-10-05.md)
show the substantial zero-smearing IP induced by the reconstructed-direction
hit proxy. This is not a post-BDT rejection estimate.

For the requested six-point scan over 0.5–1.5 mrad, run the same pilot with
the named scan config and a distinct output directory:

```bash
MPLCONFIGDIR=/tmp/lblgamma_mpl_pointing XDG_CACHE_HOME=/tmp/lblgamma_cache_pointing \
  myenv/bin/python studies/resolutions/run_photon_pointing_pilot.py \
  --input /eos/lhcb/lbdt3/user/rquaglia/fcc_ee/lblgamma/outputs/Lb2LambdaGammaPhysics_nev100000_IDEA_edm4hep.root \
  --config config/photon_pointing_scan_0p5_1p5_v3.json \
  --events 200 --output-dir docs/data/v3_photon_pointing_scan_0p5_1p5_200events
```

This produces IP-distribution overlays, a median/central-68%-interval plot
versus resolution, a CSV of quantiles and the per-photon Parquet. The six
values are 0.5, 0.7, 0.9, 1.1, 1.3 and 1.5 mrad per local angular component.
They share the same standard-normal draws, so each comparison is paired.

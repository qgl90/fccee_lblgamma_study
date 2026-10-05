# Offline photon-pointing geometry: 200-event audit

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

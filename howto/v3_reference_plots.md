# Inspect the Stage 1 v3 Physics and Zbb candidates

This is a small, frozen comparison of the Physics Λb→Λ⁰γ v3 tuple and the
Zbb v3 Condor chunks available on 2 October 2026. The input list and processed
event counters are in
[`zbb_catalog_snapshot.json`](../outputs/analysis/studies/v3_offline_inspection_20261002/zbb_catalog_snapshot.json).
It contains 191 completed chunks, not the full 1,200-job campaign. Later chunks
must be catalogued under a new study name before inclusion.

The prepared mass-window output is
[`reference_mass5`](../outputs/analysis/studies/v3_offline_inspection_20261002/reference_mass5):
one `signal_-1_selected.parquet` and one `zbb_<chunk>_selected.parquet` per
chunk. The matching `*_audit.parquet` files retain every Stage 1 candidate,
including those failing the mass window. `summary.json` records exact inputs,
config hashes, commands, processed-event denominators, and candidate/event
cutflow. `truth_matched` is an inspection label, never a filter in the offline
selection.
This frozen ±5 MeV comparison is the earlier no-veto reference. The current
default in [`lb_offline_selections.json`](../config/lb_offline_selections.json)
is ±12.5 MeV plus Λb energy ≥10.5 GeV, also with no photon veto.

The simpler same-hemisphere π⁰-veto reference lives in
[`reference_mass5_pi0`](../outputs/analysis/studies/v3_offline_inspection_20261002/reference_mass5_pi0).
Its `candidates/` directory contains the same columns, one row per passing
candidate. The veto rejects a candidate if **any other raw type-22 photon on
the Λ⁰ hemisphere** has `|m(γγ)−m(π⁰)|≤20 MeV`. A candidate with no eligible
partner passes. This is an optional named study selection, not a change to
the reference configuration.

## Reproduce the preparation and plots

From the repository root, with the LbConda environment available:

```bash
BASE=outputs/analysis/studies/v3_offline_inspection_20261002
SIGNAL=/eos/lhcb/lbdt3/user/rquaglia/fcc_ee/lblgamma/outputs/stage1_v3_my_run/signal_physics.root

env -u PYTHONPATH -u PYTHONHOME myenv/bin/python \
  studies/reconstruction/prepare_offline_bdt.py \
  --signal "$SIGNAL" --zbb-catalog "$BASE/zbb_catalog_snapshot.json" \
  --config config/lb_offline_selections.json \
  --stage1-config config/lb_reco_preselection_15mev_45_65_3d.json \
  --scenario lambda5_same_hemi_all --output-dir "$BASE/reference_mass5"

env -u PYTHONPATH -u PYTHONHOME myenv/bin/python \
  studies/reconstruction/plot_stage1_v3_reference.py \
  --prepared-dir "$BASE/reference_mass5" \
  --selection mass5_pi0 --output-dir "$BASE/reference_mass5_pi0"

env -u PYTHONPATH -u PYTHONHOME myenv/bin/python \
  studies/reconstruction/plot_stage1_v3_reference.py \
  --prepared-dir "$BASE/reference_mass5" --selection mass5 --no-copy \
  --output-dir "$BASE/reference_mass5_plots"
```

The second command writes normalized PNG comparisons under `plots/`, a
`manifest.json` with event and candidate counts, and an exploratory
`single_variable_cut_scan.csv`. Each CSV row gives the better one-sided bound
for its variable with at least 99% retention of truth-matched Physics
candidates **conditional on the offline selection**. Zbb retention uses
nonmatched Zbb candidates in these same 191 chunks. It is a discovery scan on
the plotted data, not a validated cut or a full-campaign physical projection.
Each plotted category is normalized separately: truth-matched Physics,
wrong Physics combinations, and nonmatched Zbb.
The diphoton-distance panels display only finite partner masses; an empty
partner list is stored as `+inf` and passes the veto. Inspect
`gamma_combo_same_hemi_all_mass` or count `min_pair == inf` to measure that
category explicitly.
Use `--selection mass5` to inspect the mass window before the photon veto;
change `--cones R03 R05 R07` to choose cone pages. Add, for example,
`--variables iso_R05_charged_energy z_full_deltaP proton_p` to make one custom
plot page. For a mass-window-only rerun, `--selection mass5 --no-copy` uses
the already prepared Parquets without duplicating them.

## Make a quick plot yourself

The named `lambda5_lbE9_same_hemi_all` comparison adds reconstructed
`lb_E ≥ 9 GeV` to the mass-window reference without a π⁰ or η veto. It
preserves all existing candidate columns and adds the new same-hemisphere
energy-isolation ratios. Reproduce it from the frozen mass-window tables:

```bash
BASE=outputs/analysis/studies/v3_offline_inspection_20261002
env -u PYTHONPATH -u PYTHONHOME myenv/bin/python \
  studies/reconstruction/study_v3_mass_energy_preselection.py \
  --parent-dir "$BASE/reference_mass5" --lb-energy-min 9 \
  --output-dir "$BASE/reference_mass5_lbE9"
```

The resulting `plots/diphoton_min_and_veto_windows.png` shows the
same-hemisphere minimum `m(γγ)`, distances to the π⁰/η masses, and the
no-partner fraction. No photon veto is applied. The corresponding
`manifest.json` gives candidate and event counts before and after the energy
cut. Use `$BASE/reference_mass5_lbE9/candidates` as the reference directory
for quick custom plots of this comparison.

For a joint mass and energy comparison retaining at least 99% of the
fit-range Stage 1 direct Physics candidates on the frozen inputs:

```bash
env -u PYTHONPATH -u PYTHONHOME myenv/bin/python \
  studies/reconstruction/study_v3_joint_mass_energy_scan.py \
  --prepared-dir "$BASE/reference_mass5" \
  --output-dir "$BASE/joint_mass_energy_scan"

env -u PYTHONPATH -u PYTHONHOME myenv/bin/python \
  studies/reconstruction/study_v3_mass_energy_preselection.py \
  --parent-dir "$BASE/reference_mass5" \
  --lambda-half-window-mev 12.5 --lb-energy-min 10.5 \
  --output-dir "$BASE/reference_mass12p5_lbE10p5"
```

The second command starts from the full candidate audits, so it can recover
candidates between ±5 and ±12.5 MeV. Its `candidates/` Parquets preserve all
Stage 1 and prepared columns, add 36 isolation-energy ratios, and retain one
row per selected candidate. The named JSON scenario is
`lambda12p5_lbE10p5_same_hemi_all`; the PI subsequently made it the offline
default. All v3 offline inspection plots use the
`mplhep` LHCb style. `d_pi0` and `d_eta` mean the **smallest absolute mass
distance** to π⁰ and η, respectively, across all eligible same-hemisphere
photon partners; they are not the lightest pair masses.

For a single fast plot from the energy-selected rows:

```bash
env -u PYTHONPATH -u PYTHONHOME myenv/bin/python \
  studies/reconstruction/quick_compare_v3_reference.py \
  --reference-dir "$BASE/reference_mass5_lbE9/candidates" \
  --variables lb_E iso_R03_all_energy_over_gamma_E z_partial_deltaE \
  --selection-label 'Λ ±5 MeV; Λb E ≥9 GeV; no photon veto' \
  --output-dir "$BASE/reference_mass5_lbE9/my_plot"
```

To repeat the energy-isolation ratio scan on this no-veto, energy-selected
sample, run `study_v3_isolation_ratios.py` with that `candidates/` directory
as `--reference-dir` and a new `--output-dir`.

To compare any saved numeric columns from the finished π⁰-veto reference,
without reading ROOT or copying all candidate columns again:

```bash
BASE=outputs/analysis/studies/v3_offline_inspection_20261002
env -u PYTHONPATH -u PYTHONHOME myenv/bin/python \
  studies/reconstruction/quick_compare_v3_reference.py \
  --reference-dir "$BASE/reference_mass5_pi0/candidates" \
  --variables iso_R05_charged_energy z_full_deltaP proton_p \
  --output-dir "$BASE/my_comparison"
```

The PNG and `comparison.json` appear in `my_comparison/`. Point
`--reference-dir` at `$BASE/reference_mass5` to inspect the same variables
before the π⁰ veto. This script reads only the requested columns.

To reproduce the same-hemisphere activity-energy/photon-energy ratio scan,
including all six cones, charged/neutral/all classes, both centers, and
99%/95% signal working points:

```bash
env -u PYTHONPATH -u PYTHONHOME myenv/bin/python \
  studies/reconstruction/study_v3_isolation_ratios.py \
  --reference-dir "$BASE/reference_mass5_pi0/candidates" \
  --output-dir "$BASE/isolation_ratio_study_pi0"
```

See the [isolation-ratio review note](../docs/STAGE1_V3_ISOLATION_RATIO_REVIEW_2026-10-02.md)
for the numerator definition and measured retention.

The `candidates/` directory is a Parquet dataset. For example:

```python
import pyarrow.dataset as ds
import matplotlib.pyplot as plt

path = "outputs/analysis/studies/v3_offline_inspection_20261002/reference_mass5_pi0/candidates"
columns = ["sample", "truth_matched", "iso_R05_charged_energy"]
df = ds.dataset(path, format="parquet").to_table(columns=columns).to_pandas()
signal = df[(df["sample"] == "signal") & (df["truth_matched"] == 1)]
zbb = df[(df["sample"] == "zbb") & (df["truth_matched"] != 1)]
plt.hist(signal["iso_R05_charged_energy"], bins=50, density=True,
         histtype="step", label="Physics direct")
plt.hist(zbb["iso_R05_charged_energy"], bins=50, density=True,
         histtype="step", label="Zbb")
plt.xlabel("Photon cone R05 charged energy [GeV]")
plt.legend()
plt.show()
```

The prepared ROOT-to-Parquet stage preserves charged, neutral, and all
activity for both photon- and Λ⁰-centered cones, including summed energy,
`px,py,pz`, vector-sum momentum magnitude, multiplicity, and charged-track
`d0` extrema. It also preserves thrust, recoil momentum/energy balance,
particle energies and momenta, pair mass lists, and truth ancestry. See
[`understand_isolation.md`](understand_isolation.md) for isolation definitions.
The [Z-balance definitions](understand_z_balance.md) give the exact
`z_partial_deltaE`, `z_partial_deltaP`, and full-event formulas.

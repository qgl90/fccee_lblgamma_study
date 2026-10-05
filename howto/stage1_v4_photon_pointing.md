# v4 tuples for offline calorimeter pointing studies

This is a tuple extension of the v3 reconstructed selection, requested on
2026-10-05. Smearing is performed offline. The new branches are attached after
candidate construction and do not enter the current BDT. Preserve the v3
production and use new v4 output directories and direct ROOT basenames.

## Geometry and saved information

`analysis/studies/photon_pointing_v4.h` defines an effective cylinder with
radius 2250 mm, half-length 2500 mm and annular endcaps with radii
249.55392417205682–2250 mm. The inner radius is 2500/sinh(3), inferred from
the card's acceptance; it is not a separately measured inner ECAL radius.
The [200-event geometry audit](../docs/data/v3_photon_pointing_geometry_200events/geometry_audit.json)
and [checkpoint](../docs/PHOTON_POINTING_CHECKPOINT_2026-10-05.md) explain the evidence.
This describes the effective fast-simulation surface, not a detailed detector.

Each candidate retains existing `lb_photon_px/py/pz/energy` (GeV), its
reconstructed photon index, and existing ancestry. New candidate vectors have
prefix `lb_photon_pointing_`:

| Suffix | Meaning |
|---|---|
| `mc_index`, `match_status` | Unique stable association: status 0 unresolved, 1 true photon, 2 matched nonphoton; absent MC index −1 |
| `truth_px/py/pz/energy` | Associated photon's generated four-momentum, GeV |
| `truth_vx/vy/vz` | Associated photon's production point, mm |
| `truth_hit_x/y/z/path/region` | First forward active surface crossing from the true production point along true momentum; path in mm |
| `reco_hit_x/y/z/path/region` | Surface crossing from origin along reconstructed momentum |
| `pv_x/y/z`, `pv_valid` | Reconstructed PV, repeated per candidate |
| `geometry_version`, `barrel_radius`, `endcap_abs_z`, `endcap_inner_radius`, `endcap_outer_radius` | Version 4 and exact effective dimensions in mm |

Hit region: 0 no valid crossing, 1 barrel, 2 either endcap (z gives its sign).
Invalid floating values are NaN. Matching uses the existing one-to-one stable
MC association, irrespective of full Λb truth matching: wrong combinations
and background photons receive the same diagnostics. A surface crossing is
geometric; photons produced outside the calorimeter are not a claim of detector
reconstructibility. Such cases can be identified from the saved truth vertex.
Both charge conjugates follow the existing builder. Photon truth is diagnostic
and may only define a synthetic detector response, not a truth-based event cut.

## Direct reconstruction

From the repository root, the wrapper selects the Python used to build
FCCAnalyses and sources its setup. Start with a bounded trial:

```bash
LB_RECO_ANALYSIS=analysis/studies/lb2lambda_gamma_reco_v4.py \
 scripts/run_reco_preselection.sh signal_physics \
 /eos/lhcb/lbdt3/user/rquaglia/fcc_ee/lblgamma/outputs/Lb2LambdaGammaPhysics_nev100000_IDEA_edm4hep.root \
 outputs/analysis/studies/my_pointing_trial_v4/signal_200_stage1_v4.root \
 200 config/lb_reco_preselection_15mev_45_65_3d.json 1
```

For the PI's production, use a fresh v4 output and `all` instead of `200`.
The final argument is CPUs; bounded runs use one CPU because ROOT Range and
implicit multithreading cannot be combined here. Parallelize independent full
input shards with an explicit CPU budget (e.g. eight jobs × four cores on a
32-core machine), and retain immutable source IDs and input lists.
Record input production IDs/card/decay/seeds, input-event count, both repository
revisions, selection/observable/header hashes, exact command, and output.
The underlying Delphes samples remain their original generator scenarios;
this extension changes the Stage 1 schema, not Delphes response.

For Zbb, Zcc and Zss use the native wrapper, on the Condor submission host:

```bash
source external/FCCAnalyses/setup.sh
unset LB_RECO_CONFIG
SAMPLE=Zss  # repeat with Zbb and Zcc
fccanalysis run analysis/studies/analysis_preselection_v4.py \
 --input-glob "/eos/experiment/fcc/ee/generation/DelphesEvents/winter2023/IDEA/p8_ee_${SAMPLE}_ecm91/events_*.root" \
 --chunks 1200 --comp-group group_u_FCC.local_gen \
 --queue workday --ncpus 4 \
 --output-eos "/eos/lhcb/lbdt3/user/rquaglia/fcc_ee/lblgamma/outputs/${SAMPLE}_pointing_stage1_v4" \
 --eos-type eoslhcb --check-only
```

The requested value is the Condor accounting group (`--comp-group`);
`--queue` remains the CERN job flavour (`workday`). The prepared campaign script
checks all three samples by default and submits only when explicitly invoked as
`scripts/submit_stage1_v4_zflavours.sh --submit`. Keep its default
`--check-only` for review. Inspect the sample, output destination and configs
before submission. Native FCCAnalyses creates `chunk_N.root` within the explicit
v4 campaign directory; retain this naming for its job/catalog consistency.
Catalog those outputs as in [stage1.md](stage1.md), with fresh v4 catalog names.
No inclusive production has been submitted as part of this development check.

## Validate and preserve through Stage 2

Run the baseline wrapper on the same first 200 events without
`LB_RECO_ANALYSIS`, using a distinct baseline output. Then:

```bash
env -u PYTHONPATH -u PYTHONHOME myenv/bin/python \
 studies/resolutions/validate_stage1_v4_pointing.py \
 --baseline outputs/analysis/studies/pointing_trial_v4/signal_200_baseline_v3.root \
 --v4 outputs/analysis/studies/pointing_trial_v4/signal_200_validated_stage1_v4.root \
 --output-dir outputs/analysis/studies/pointing_trial_v4/validation \
 --model-dir docs/data/stage2_v3_bdt_1091_peak
```

This compares every old branch, validates candidate lengths and geometric ray
closure, exercises the actual Stage 2 preparation, and checks reproducibility
under row reordering. `flatten_candidates.py` automatically copies new `lb_`
vector branches. `prepare_offline_bdt.py` explicitly preserves all pointing
fields and measured photon Cartesian components in audit and selected rows.
Keep `source_id`, `event_entry`, `candidate_slot`, `candidates_in_event`, and
`photon_reco_index` through BDT scoring. Use fresh preparation directories;
previous v3 Parquet tables cannot supply the new fields.

## Offline hypotheses after the BDT

```bash
env -u PYTHONPATH -u PYTHONHOME myenv/bin/python \
 studies/resolutions/smear_stage1_v4_pointing.py \
 --input path/to/scored_v4.parquet --output path/to/scored_pointing_v4.parquet \
 --namespace unique_frozen_sample_catalog_v4 --anchor truth
```

The six resolutions are 0.5, 0.7, 0.9, 1.1, 1.3 and 1.5 mrad, each the Gaussian
sigma per orthogonal tangent-plane angular component (radial RMS ≈ √2 sigma).
The true direction is smeared around the stored hit. The hypothetical momentum
is `E_reco * direction_smeared`; IDEA's existing energy response is retained.
The distance to the reconstructed PV is computed as
`IP3D = |(hit − PV) × direction|` and
`|d0| = |(hit_x−PV_x)n_y − (hit_y−PV_y)n_x| / sqrt(n_x²+n_y²)`.
No photon vertex fit or displacement significance is inferred.

`--anchor truth` assumes ideal hit position from the true displaced ray.
`--anchor reco` retains the position uncertainty inherited from the current
origin-based reconstructed direction. Compare these as two named detector
hypotheses. Angular smearing alone does not specify realistic hit-position
resolution/correlation. No extra position smearing is applied.

A SHA256-derived random seed uses the catalog namespace, source/event/photon
indices and seed. Candidates sharing a photon receive the same draw, independent
of shard order and batch size, and the six hypotheses share their Gaussian
variates. Use a distinct namespace for each sample/catalog. The script streams
50k rows per batch; independent Parquet shards can run in parallel.

Unresolved matches/hits/PVs retain their rows with `pointing_valid=false` and
NaN measurements. Report their fraction for each flavour; do not count them
as automatically rejected background. Apply the existing BDT/Armenteros/veto
selection first, then scan the synthetic displacement cut. Keep its conditional
and cumulative efficiency, MC uncertainty, mass and cos(theta_p) sculpting.
Use the existing flavour-specific expected-yield normalization. A predicted
improvement against Zss requires those full-sample studies; this pilot does
not establish it. Recomputing mass/angles with the hypothetical momentum is a
separate response scenario and requires a new acceptance evaluation.

Reproduce the published pilot figure from the frozen audit table:

```bash
MPLCONFIGDIR=/tmp/lblgamma-mplconfig XDG_CACHE_HOME=/tmp/lblgamma-cache \
 env -u PYTHONPATH -u PYTHONHOME myenv/bin/python \
 studies/resolutions/plot_stage1_v4_pointing.py \
 --input docs/data/stage1_v4_pointing_validation/signal_stage1_audit_v4.parquet \
 --output docs/figures/stage1_v4_pointing_validation.png

env -u PYTHONPATH -u PYTHONHOME myenv/bin/python \
 studies/resolutions/test_stage1_v4_pointing.py
```

Stage 2 also retains the fitted Lambda momentum and SV coordinates for future
photon–Lambda geometric studies. No new vertex fit is performed by this change.

## Prepared campaigns and the existing 100k forced modes

The v4 Z flavour campaign was checked against the live input directories:
4,398 Zbb, 5,018 Zcc, and 5,015 Zss EDM4hep files, configured as 1,200 chunks
per flavour with four CPUs per job. Check output and exact inputs in
[`docs/data/stage1_v4_pointing_jobs_20261005/condor_check_only.log`](../docs/data/stage1_v4_pointing_jobs_20261005/condor_check_only.log).
No jobs were submitted. To repeat the checks, or to submit after reviewing the
three destinations, use:

```bash
scripts/submit_stage1_v4_zflavours.sh --check-only
scripts/submit_stage1_v4_zflavours.sh --submit
```

The forced-sample runner defaults to inventory only. It found these five
merged 100k files: Lambda gamma PHSP, Lambda gamma HELAMP, Lambda eta PHSP,
Lambda eta HELAMP, and Lambda pi0 HELAMP. It did not find the Lambda pi0 PHSP
merged file at either the repository output or the expected EOS directory.
The full input/output inventory is in
[`forced_100k_inventory.log`](../docs/data/stage1_v4_pointing_jobs_20261005/forced_100k_inventory.log).
The configured pi0 PHSP mode uses seed base 72001 and ten 10k chunks. Generate
and merge it using the [production guide](delphes_production.md) if it is
needed; the v4 runner will then include it automatically.

Review the command list first, then run the existing merged modes with:

```bash
scripts/run_stage1_v4_forced_100k.sh --check-only
V4_DIRECT_CPUS=8 scripts/run_stage1_v4_forced_100k.sh --run
```

This writes fresh outputs below
`/eos/lhcb/lbdt3/user/rquaglia/fcc_ee/lblgamma/outputs/stage1_v4_pointing_forced_100k_20261005/`.
It processes up to four available samples concurrently, with eight ROOT workers each (32 CPU workers total by default), writing separate per-sample logs. Set `V4_DIRECT_JOBS` and `V4_DIRECT_CPUS` to change this bounded allocation. Each output is checked with `validate_stage1_v4_tuple.py` and gets a validation JSON before use.
Re-run the inventory after generation/merge to include the missing PHSP pi0.
Each output basename contains `_stage1_v4`; its matching validation JSON records candidate counts and valid hit/PV fractions. Review these before flattening. The pilot figure and counts are in
the [2026-10-05 review deck](../presentations/stage1_v4_pointing_20261005/stage1_v4_pointing_20261005.pdf).

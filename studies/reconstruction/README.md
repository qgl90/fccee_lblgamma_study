# Lambda_b to Lambda0 gamma reconstruction

Candidate-level isolation, π⁰ pairing, Z-recoil and pointing diagnostics are
documented in [STAGE1_OBSERVABLES.md](STAGE1_OBSERVABLES.md).
The flattened Parquet schema and every candidate/alias column are described in
[`readme_columns.md`](readme_columns.md).

## Nominal 1,000-event preselection and 100k signal production

The Snakemake target in `Snakefile` reconstructs four explicitly named
samples: `signal_phsp`, `signal_physics`, `lbgamma_eta`, and `zbb`. The local
test is capped at 1,000 events per input by `config/config.yaml`. It reuses
the local 500k PHSP and eta files, a local 10k HELAMP chunk, and the first
cached Winter2023 Zbb ROOT file. It applies the fitted-Λ ±15 MeV window
**after the broad pπ hypothesis choice but before Λ–photon combinations**,
then applies 4.5–6.5 GeV in m(Λγ), vertex/displacement cuts, and the existing
same-thrust-hemisphere condition. The builder uses reconstructed quantities;
truth only labels candidates afterward.

After candidate construction, the configured reconstruction now applies
`n_lb > 0`, so its ROOT output contains only events with at least one selected
Lambda_b candidate. This is an event-level output filter after the expensive
candidate builder: it reduces reconstruction-file size and downstream work,
but does not save vertex-fit or candidate-building CPU for rejected events.
Use the input event count or a separate cutflow when reporting event efficiency.

Inspect wrapper arguments first with:

```bash
scripts/run_reco_preselection.sh --help
scripts/run_preselection_pilot.sh --help
scripts/run_zbb_preselection_shard.sh --help
```

The exact local Snakemake commands are shown in the root README and are
reproduced in the [preselection review note](../../docs/PRESELECTION15_REVIEW_2026-09-30.md).
Outputs include ROOT reconstruction files, one-row-per-candidate Parquet
tables, rejected rows, cut summaries, and Snakemake logs under
`outputs/analysis/studies/nominal_preselection_1000/`.

The scenario stores fitted PV/SV positions, flight distance/significance,
proton and pion d0 significances, and signed Λ d0, its projected uncertainty,
and signed significance. The Λ d0 uncertainty uses the fitted PV and SV xy
covariances projected perpendicular to the fitted Λ transverse direction; it
does not include direction uncertainty. `lambda_pv_cos` and
`lambda_pv_dca` are also stored. None is a new pointing cut. The selected
photon keeps its original reconstructed-particle index and measured
`px,py,pz,E` (`photon_reco_index`, `photon_px`, `photon_py`, `photon_pz`,
`photon_reco_energy`), plus isolation and second-photon observables. Truth and
ancestry columns remain labels.

### Candidate table with LHCb-style names

The generated file `outputs/delphes/Lb2LambdaGamma_nev50000_IDEA_edm4hep.root`
is an EDM4hep input; run reconstruction before flattening. For example, to
reconstruct the full file with the current nominal preselection:

```bash
scripts/run_reco_preselection.sh signal_phsp \
  outputs/delphes/Lb2LambdaGamma_nev50000_IDEA_edm4hep.root \
  outputs/analysis/studies/Lb2LambdaGamma_nev50000_preselection15_reco.root \
  all config/lb_reco_preselection_15mev_45_65.json 4

env -u PYTHONPATH -u PYTHONHOME myenv/bin/python \
  studies/reconstruction/flatten_candidates.py \
  --input outputs/analysis/studies/Lb2LambdaGamma_nev50000_preselection15_reco.root \
  --output outputs/analysis/studies/Lb2LambdaGamma_nev50000_preselection15_candidates.parquet \
  --mode gamma
```

The script writes one Parquet candidate row per surviving combination, with
event keys, observables, truth labels, the original column names, and readable
`Lb_*`, `Lambda0_*`, `Proton_*`, `Pion_*`, and `Gamma_*` aliases. It
retains all scalar fields from the reconstructed ROOT tree in each candidate
row. If an event produces multiple candidates, its event-level values such as
PV position and input counts are repeated on each row. Events with no surviving
candidate have no row in this candidate table.

For a flat ROOT `events` TTree with the same candidate rows and columns, pass
`--root-output flat_candidates.root` alongside `--output candidates.parquet`.
Variable-length all-other-photon mass/index columns are stored as array
branches with count branches. The full 100k Snakemake
flatten target writes both formats for each named sample.

`Gamma_Combo_OtherGamma_M` is a list column: for each candidate photon it
contains the invariant masses against every other raw type-22 reconstructed
photon, with original indices in `Gamma_Combo_OtherGamma_Index`. This
all-photon diagnostic is separate from the selected-photon best-π0 variables.
Momentum/mass are in GeV and PV/SV positions and impact parameters in mm.
There is no independently fitted Λb decay vertex in this reconstruction, so
the output does not invent `Lb_X/Y/Z` or `Lb_Rxy`.

To generate three 100k forced samples with the Snakemake chunk and merge
rules, request these targets explicitly; this does not change the default
500k production target:

```bash
env -u PYTHONPATH -u PYTHONHOME XDG_CACHE_HOME="$PWD/.snakemake/cache" \
  myenv/bin/python -m snakemake --snakefile Snakefile --cores 20 --printshellcmds \
  outputs/delphes/Lb2LambdaGamma_nev100000_IDEA_edm4hep.root \
  outputs/delphes/Lb2LambdaGammaPhysics_nev100000_IDEA_edm4hep.root \
  outputs/delphes/Lb2LambdaEta_nev100000_IDEA_edm4hep.root
```

The original BDT chain is `scripts/run_bdt_study.sh`. For a later production
comparison, use a distinct `STUDY_TAG`, set
`LB_RECO_CONFIG=config/lb_reco_preselection_15mev_45_65.json`,
`LAMBDA_HALF_WINDOW_GEV=.015`, `LB_MASS_MIN_GEV=4.5`, and
`LB_MASS_MAX_GEV=6.5`, and
`ZBB_OUTPUT_TAG=Zbb_winter2023_preselection15_100k`, then run its stages in the order documented in
`docs/BDT_WORKFLOW.md`. Its defaults still describe the previously reviewed
±10 MeV, 4.9–6.3 GeV study. A 1,000-event Z→bb pilot is too small to
measure BDT rejection; train and test with independent source files after
reviewing the paired pilot. The trainer reads the interval from the dataset
manifest. Older yield projection scripts still display the reviewed
4.9–6.3 GeV interval and should not be used to present a new scenario.

The PI review history, stage boundaries, and extension contracts for Z-pole
event features, detector scenarios, and diphoton vetoes are in
[`docs/ANALYSIS_WORKFLOW.md`](../../docs/ANALYSIS_WORKFLOW.md). This README
documents the current executable reference reconstruction and measured
1,000-event checks.

The configured reconstruction builds every opposite-charge Lambda0 to p pi
hypothesis without MC identity, fits the two tracks with FCCAnalyses
`VertexFitterSimple`, uses the **fitted track momenta** for both proton/pion
mass assignments and the Lambda_b mass, and combines the chosen Lambda0 with
selected IDEA photons. MC associations label candidates after construction.
The local FCCAnalyses checkout is `pre-edm4hep1`, commit
`91c7d6c5a5c8ad5c3848d6d7cf8383e93c9b74e3`.

## Vertex and mass construction

The PV uses `get_PrimaryTracks(EFlowTrack_1, ...)` and the beam-spot-constrained
`VertexFitter_Tk(1, PrimaryTracks, ..., false)`, as in
`external/FCCAnalyses/examples/FCCee/tutorials/vertexing/analysis_primary_vertex.py`.
Opposite-charge tracks assigned to the PV are excluded. Each remaining pair is
fitted once with `VertexFitter_Tk(2, pair)`, as in the FCCAnalyses secondary-vertex
examples. Its `updated_track_momentum_at_vertex` has the same order as the two
input track states. The builder uses those two three-momenta to calculate both
p+ pi- and pbar- pi+ masses, tests the broad 0.7–1.3 GeV window, and picks the
surviving assignment with the smallest absolute distance to 1.115683 GeV.
The same fitted daughter momenta then enter `m(Lambda_b)`; the photon keeps its
measured reconstructed momentum and energy. The fit is independent of the
proton/pion mass hypothesis, so it is performed only once per pair.

This is equivalent to the momentum update performed by FCCAnalyses
`myUtils::get_RP_atVertex`, but it is applied to each candidate pair directly.
We do **not** use the examples' `RecoPartPIDAtVertex` chain: its upstream
`myUtils::PID` reads MC associations to assign particle identities and would
remove the fake combinations we need to study. The uncut baseline still uses
original reconstructed momenta because it has no vertex fit.

The input EDM4hep files have no fitted reconstructed-vertex collection. Their
`Particle.vertex` coordinates and Delphes `GenVertex` are truth information.
The local fitter writes vertex covariance `(xx,yx,yy,zx,zy,zz)`, so the
transverse significance projections use entries 0, 1, and 2.

## Selection

`config/lb_reco.json` defines the default selection:

- a finite fitted PV with at least two PV tracks, at least one selected
  `Photon#0.index` photon, and opposite-charge reconstructed tracks;
- both daughter transverse impact-parameter significances at the PV at least 3;
- secondary-vertex chi2 at most 9, transverse PV-to-SV flight at least
  0.3 mm, and flight significance at least 2;
- fitted-vertex Lambda0 mass 0.7–1.3 GeV, with the closer of the two
  proton/pion assignments retained;
- Lambda_b mass 4.9–6.3 GeV;
- photon and fitted Lambda0 in the **same event-thrust hemisphere**.

The event thrust axis comes from FCCAnalyses
`Algorithms::calculate_thrust` on all reconstructed-particle momenta, following
the local flavour-analysis examples. The hemisphere cut requires
`cos(Lambda0,thrust) * cos(photon,thrust) > 0`; the arbitrary sign of the thrust
axis cancels. It is configurable with `require_same_hemisphere`. The
`config/lb_reco_no_hemisphere.json` file changes only that flag for comparison.
For the two-photon Eta diagnostic, the summed photon-pair momentum defines the
neutral hemisphere. No isolation or best-candidate choice is applied.

## Run on the first 1,000 events

```bash
source external/FCCAnalyses/setup.sh
fccanalysis run analysis/studies/lb2lambda_gamma_reco.py \
  --files-list outputs/delphes/Lb2LambdaGamma_nev500000_IDEA_edm4hep.root \
  --output Lb2LambdaGamma_reco_1000events_vertexmom_hemi.root \
  --nevents 1000 --ncpus 1
fccanalysis run analysis/studies/lb2lambda_gamma_reco.py \
  --files-list outputs/delphes/Lb2LambdaEta_nev500000_IDEA_edm4hep.root \
  --output Lb2LambdaEta_as_gamma_1000events_vertexmom_hemi.root \
  --nevents 1000 --ncpus 1
fccanalysis run analysis/studies/lb2lambda_gamma_cutflow.py \
  --files-list outputs/delphes/Lb2LambdaGamma_nev500000_IDEA_edm4hep.root \
  --output Lb2LambdaGamma_cutflow_charge_chi2_1000events_vertexmom_hemi.root \
  --nevents 1000 --ncpus 1
```

The Eta-generated sample is reconstructed under the **same one-photon signal
hypothesis** to measure the partially reconstructed shape. A separate
`lb2lambda_eta_reco.py` two-photon diagnostic also uses the fitted-vertex
Lambda0. To compare without the hemisphere cut, prefix the run command with
`LB_RECO_CONFIG=config/lb_reco_no_hemisphere.json` and choose a distinct output
filename. This FCCAnalyses checkout runs single-threaded when `--nevents` is
specified; full-sample runs can omit it to use multiple cores.

Plotting and flattening use the separate `myenv` Python environment. For
example:

```bash
env -u PYTHONPATH -u PYTHONHOME myenv/bin/python \
  studies/reconstruction/flatten_candidates.py --mode gamma \
  --input outputs/analysis/studies/Lb2LambdaGamma_reco_1000events_vertexmom_hemi.root \
  --output outputs/analysis/studies/Lb2LambdaGamma_reco_1000events_vertexmom_hemi.parquet
env -u PYTHONPATH -u PYTHONHOME myenv/bin/python \
  studies/reconstruction/plot_thrust_hemisphere.py \
  --input outputs/analysis/studies/Lb2LambdaGamma_reco_1000events_vertexmom_nohemi.root \
  --output-dir outputs/plots/reconstruction/selected_vertexmom_hemi
env -u PYTHONPATH -u PYTHONHOME myenv/bin/python \
  studies/reconstruction/scan_lb_mass_windows.py \
  --signal outputs/analysis/studies/Lb2LambdaGamma_reco_1000events_vertexmom_hemi.parquet \
  --eta-as-gamma outputs/analysis/studies/Lb2LambdaEta_as_gamma_1000events_vertexmom_hemi.parquet \
  --output-dir outputs/plots/reconstruction/vertexmom_hemi
env -u PYTHONPATH -u PYTHONHOME myenv/bin/python \
  studies/reconstruction/audit_signal_losses.py \
  --mc outputs/delphes/Lb2LambdaGamma_nev500000_IDEA_edm4hep.root \
  --cutflow outputs/analysis/studies/Lb2LambdaGamma_cutflow_charge_chi2_1000events_vertexmom_hemi.root \
  --output-dir outputs/plots/reconstruction/selected_vertexmom_hemi
```

The Parquet table has one row per candidate, retaining event entry and
candidate multiplicity, truth ancestry for each daughter, vertex quantities,
`thrust_value`, thrust-axis components, and the Lambda0 and neutral cosines to
that axis. `lb_same_hemisphere` is stored in the ROOT output. The selected
plots and cutflow JSON are under
`outputs/plots/reconstruction/selected_vertexmom_hemi/`; the mass-window JSON
and signal/Eta overlay are under `outputs/plots/reconstruction/vertexmom_hemi/`.

## First 1,000-event results and charge audit

The first 1,000 input events contain **1,001** generated direct signal decays:
500 Lambda_b and 501 anti-Lambda_b. One event contains both. The builder and
truth labeler accept both p+ pi- and pbar- pi+ assignments. The final selected
truth counts are 262/500 = **52.4%** for Lambda_b and 273/501 = **54.5%** for
anti-Lambda_b. Their sum is **535/1,001 = 53.4% per generated decay**; there
are 535 events with at least one selected signal, or **53.5% per input event**.
There is no missing charge-conjugate chain.

`studies/reconstruction/audit_signal_losses.py` identifies generated truth
chains and their uniquely associated reconstructed daughters, then joins the
charge-specific FCCAnalyses cutflow. Here *reconstructible* means both charged
daughters have usable reconstructed tracks and at least one direct photon has
a unique type-22 reconstructed match. It includes detector acceptance and
reconstruction; it is not a generator-only geometric-acceptance measure.
The per-decay counts are:

| Cumulative stage | Decays retained | Loss at step |
|---|---:|---:|
| Generated Lambda_b/anti-Lambda_b to Lambda0(p pi) gamma | 1,001 | — |
| Both charged tracks reconstructed | 791 | 210 |
| Plus a reconstructed direct photon | 781 | 10 |
| Photon in IDEA selected container | 736 | 45 |
| Valid PV and event tracks | 724 | 12 |
| Both tracks outside PV set | 715 | 9 |
| Both daughter d0 significances at least 3 | 691 | 24 |
| Valid SV fit | 691 | 0 |
| SV chi2 at most 9 | 546 | 145 |
| SV flight distance and significance | 546 | 0 |
| Fitted Lambda0 mass 0.7–1.3 GeV | 544 | 2 |
| Closest mass hypothesis and Lambda_b fit interval | 544 | 0 |
| Same thrust hemisphere | 535 | 9 |

The two largest losses are **both charged tracks reconstructed** (210/1,001)
and **SV chi2 at most 9** (145/691 entering that cut). The photon selection
loses 45 of 781 reconstructible decays. The fitted-momentum Lambda0 mass
window loses only two. Marginally, 805/1,001 true protons or antiprotons,
795/1,001 true pions, and 988/1,001 direct photons have usable unique
reconstructed matches; these marginal counts overlap and must not be added.
The proton and pion have any reco association in 856 and 844 decays,
respectively; a usable charged track is present in 805 and 796. Requiring a
unique bidirectional association changes those usable-track counts to 805 and
795. Thus the charged-track loss is mostly missing or unusable track output,
not the strict one-to-one truth-match rule. A direct photon has a usable
reconstructed type-22 match in 990 decays and a unique one in 988.
The audit JSON and plot are
`outputs/plots/reconstruction/selected_vertexmom_hemi/signal_loss_audit.*`.
The event-level cutflow plot uses 1,000 input events as its denominator, so the
one double-signal event counts once there.

The true-pair SV chi2 distribution is saved as `true_vertex_chi2.png`. Of 691
valid true vertices entering the quality cut, 546 pass chi2 at most 9, 578
would pass 25, and 623 would pass 100. This distribution has a long high-chi2
tail (90th percentile about 93). Relaxing the threshold is a possible
efficiency study, but the corresponding combinatorial and inclusive Z→bb
background must be measured before changing the default selection.

The same-hemisphere photon cut retains 535/544 = **98.3%** of signal at that
step.

## Proton helicity angle for the mass–angle analysis

The candidate output now contains `lb_cos_theta_p` and `lb_truth_cos_theta_p`;
the flattened table calls them `cos_theta_p` and `truth_cos_theta_p`.
Following the [LHCb Λb→Λγ angular convention](https://arxiv.org/pdf/2111.10194),
θp is the angle between the proton momentum and **minus the Λb momentum in
the Λ rest frame**. For the conjugate chain, use the antiproton and minus the
anti-Λb momentum. Boost both four-vectors with the same Λ four-vector.
`lb_sign=+1` tags the p⁺π⁻/Λb **hypothesis** and `lb_sign=-1` the
p̄⁻π⁺/anti-Λb hypothesis; for fake candidates it is not a truth parent tag.
Keep the charge tag in the fit; do not fold charge samples without choosing and testing
the CP/angular sign convention. The reconstructed parent is fitted Λ⁰ plus
the selected photon; its proton momentum is the fitted-vertex momentum with
the chosen proton mass. The truth angle is stored only for a fully matched
candidate with the correct signed mass hypothesis. Undefined values are -999.

The current forced EvtGen Gamma and Eta files use `PHSP`; the Gamma file also
forces Λ⁰→pπ with `PHSP`. They provide the angular-acceptance denominator,
not a physics angular distribution. The generated denominator includes direct
decays with no reconstructed candidate. `study_cos_theta_p.py` independently
calculates each generated angle from MC four-vectors and checks it against
the C++ truth angle of every selected candidate. Its binned width is half the
central 68% residual interval in **absolute cos θp units**, since a relative
residual would be singular near zero. Underlying residual histograms are
saved for every bin.

```bash
source external/FCCAnalyses/setup.sh
fccanalysis run analysis/studies/lb2lambda_gamma_reco.py \
  --files-list outputs/delphes/Lb2LambdaGamma_nev500000_IDEA_edm4hep.root \
  --output Lb2LambdaGamma_angle_1000events.root --nevents 1000 --ncpus 1
fccanalysis run analysis/studies/lb2lambda_gamma_reco.py \
  --files-list outputs/delphes/Lb2LambdaEta_nev500000_IDEA_edm4hep.root \
  --output Lb2LambdaEta_as_gamma_angle_1000events.root --nevents 1000 --ncpus 1
env -u PYTHONPATH -u PYTHONHOME myenv/bin/python \
  studies/reconstruction/flatten_candidates.py --mode gamma \
  --input outputs/analysis/studies/Lb2LambdaGamma_angle_1000events.root \
  --output outputs/analysis/studies/Lb2LambdaGamma_angle_1000events.parquet
env -u PYTHONPATH -u PYTHONHOME myenv/bin/python \
  studies/reconstruction/flatten_candidates.py --mode gamma \
  --input outputs/analysis/studies/Lb2LambdaEta_as_gamma_angle_1000events.root \
  --output outputs/analysis/studies/Lb2LambdaEta_as_gamma_angle_1000events.parquet
env -u PYTHONPATH -u PYTHONHOME myenv/bin/python \
  studies/reconstruction/study_cos_theta_p.py \
  --mc outputs/delphes/Lb2LambdaGamma_nev500000_IDEA_edm4hep.root \
  --selected outputs/analysis/studies/Lb2LambdaGamma_angle_1000events.parquet \
  --eta-as-gamma outputs/analysis/studies/Lb2LambdaEta_as_gamma_angle_1000events.parquet \
  --cutflow outputs/analysis/studies/Lb2LambdaGamma_cutflow_charge_chi2_1000events_vertexmom_hemi.root \
  --events 1000 --output-dir outputs/plots/reconstruction/cos_theta_p_1000events
```

In the first 1,000 Gamma events there are 1,001 generated direct decays and
535 selected truth-matched candidates (262 Λb, 273 anti-Λb). In ten equal
generated-angle bins the observed final efficiency ranges from about 47% to
66%; this small diagnostic does not fix an acceptance model. The overall
central-68% residual half-width is about 0.0114 in cos θp. The eta sample,
processed with the same one-photon signal reconstruction, has 356 candidates:
249 have the true partial η ancestry and 107 are other combinations. Its
plotted angular shapes are unit normalized separately and carry no physical
yield normalization. The counts and bin values are in
`outputs/plots/reconstruction/cos_theta_p_1000events/cos_theta_p_summary.json`.

For the next stage, evaluate acceptance with more PHSP events and statistical
uncertainties, run the PI-supplied physics EvtGen model through the same
chain, and validate a two-dimensional mass–angle description for signal,
partial η, and inclusive Z→bb. Expected yields require physical branching
fractions, production fractions, and sample normalization; they cannot be
read from these forced samples.

## Post-reconstruction Lambda mass and diphoton veto pilots

`scan_lambda_mass_window.py` keeps the builder's broad 0.7–1.3 GeV Lambda
window and scans a tighter cut on the **fitted-vertex** pπ mass. On the first
1,000 forced Gamma events, a ±10 MeV window around 1.115683 GeV retains
524/535 truth-matched candidates. On one 100,000-event winter2023 IDEA
`p8_ee_Zbb_ecm91` file, it reduces the baseline from 5,582 candidates in
3,452 events to 814 candidates in 700 events. Of these, 433 have a true
Lambda daughter pair, so the Lambda mass cut cannot remove every Lambda plus
unrelated-photon combination. The scan and filtered candidate tables are in
`outputs/plots/reconstruction/zbb_lambda_mass_scan_100k/`.

`study_diphoton_veto.py` then pairs each selected candidate photon with every
**other selected photon in the same reconstructed thrust hemisphere**. It
uses the measured EDM4hep photon four-vectors, including measured energy, and
saves the nearest diphoton-mass distances from the π0 and η masses as
candidate-level Parquet columns. A candidate is vetoed when *any* such pair
falls in the specified mass interval. This does not use MC ancestry in the
decision. Photon truth labels are used only to report category retention.
The veto is evaluated after the ±10 MeV Lambda window and the existing
4.9–6.3 GeV Lambda_b fit interval, displacement, vertex-quality, and
same-hemisphere Lambda–photon cuts.

| Veto half-windows | True Gamma signal | True η-as-Gamma feed-down | Generic Zbb |
|---|---:|---:|---:|
| None | 524 | 246 | 814 |
| π0 ±20 MeV | 524 | 246 | 714 |
| η ±50 MeV | 522 | 189 | 769 |
| π0 ±20 and η ±50 MeV | 522 | 189 | 672 |
| π0 ±30 and η ±75 MeV | 522 | 167 | 636 |

The baseline signal uses 1,000 forced Gamma events, the η sample uses 1,000
forced Eta events, and Zbb uses the first 100,000 events of one file. The
combined ±20/±50 choice keeps 99.6% of the truth-matched Gamma candidates
that pass the Lambda mass cut, rejects 23.2% of the fully matched η feed-down,
and rejects 17.4% of generic Zbb candidates. Only 132/246 matched η
feed-down candidates have another selected photon in the same hemisphere,
so missing/inefficient companion photons limit this veto. Its absolute
signal yield is 522/1,000 generated events in this pilot.

The 40-thread Zbb snapshot has `event_entry` values that do not identify the
original EDM4hep entry reliably. The veto audit therefore recovers the source
entry with the candidate photon's original reconstructed-particle index and
exact persisted float32 energy; it fails if the match is absent or ambiguous.
The resulting `original_event_entry` is stored with the veto features. The
1000-event single-thread smoke was independently checked to have consistent
entry numbers. Future large reconstruction snapshots should write these
diphoton features in the same FCCAnalysis event to avoid this join.

```bash
env -u PYTHONPATH -u PYTHONHOME myenv/bin/python \
  studies/reconstruction/study_diphoton_veto.py \
  --signal-edm outputs/delphes/Lb2LambdaGamma_nev500000_IDEA_edm4hep.root \
  --signal outputs/analysis/studies/Lb2LambdaGamma_angle_1000events.parquet \
  --eta-edm outputs/delphes/Lb2LambdaEta_nev500000_IDEA_edm4hep.root \
  --eta outputs/analysis/studies/Lb2LambdaEta_as_gamma_angle_1000events.parquet \
  --zbb-edm /eos/experiment/fcc/ee/generation/DelphesEvents/winter2023/IDEA/p8_ee_Zbb_ecm91/events_000083138.root \
  --zbb outputs/analysis/studies/Zbb_winter2023_IDEA_firstfile_100k_mt48.parquet \
  --zbb-events 100000 --zbb-match-by-photon \
  --output-dir outputs/plots/reconstruction/diphoton_veto_100k
```

The output directory contains `veto_scan.json`, `veto_retention.png`, and
three candidate feature tables. Rerun window summaries without decoding the
original ROOT files using the same command with `--reuse-features`.

Using the same fitted-momentum reconstruction with the hemisphere cut disabled,
there are 913 candidates in the 4.9–6.3 GeV interval: 544 true signal and 369
other combinations. Enabling it leaves 639: **535 true signal and 104 other
combinations**. This removes 265/369 = **71.8%** of the other combinations
in the forced signal sample. For forced Eta decays reconstructed as one-photon
signal, the fit interval has 804 candidates without the hemisphere cut
(251 true partial Eta and 553 other), and 356 with it (249 true partial Eta
and 107 other). The direct-Gamma truth flag is zero for Eta-generated events.
The separate two-photon Eta diagnostic retains 384 candidates, including 344
full truth matches.

The truth-matched signal mass median in this 1,000-event diagnostic is
5.610 GeV. Illustrative windows around that sample median give:

| Lambda_b window | True signal | Other signal-sample combinations | True partial Eta | Other Eta-sample combinations | Signal efficiency |
|---|---:|---:|---:|---:|---:|
| 4.9–6.3 GeV | 535 | 104 | 249 | 107 | 53.5% |
| Median ±200 MeV | 510 | 29 | 63 | 31 | 51.0% |
| Median ±100 MeV | 400 | 13 | 39 | 14 | 40.0% |
| Median ±50 MeV | 265 | 7 | 17 | 7 | 26.5% |
| Median ±25 MeV | 128 | 2 | 11 | 4 | 12.8% |

Each generated sample has 1,000 input events, so the table compares shapes and
selection effects. Its background rows are **not** a physical S/B estimate:
the signal and Eta decays were generated as separate forced samples and their
production and decay rates have not been applied. The mass intervals are
illustrative and have not been optimized. For a signal branching ratio near
10 × 10^-6, a credible expected-background estimate requires inclusive Z→bb
samples, their generated-event counts and normalization, and the same complete
reconstruction. The verified winter2023 generic Zbb manifest below is the
input for that step.
If the generated signal forced both the Lambda_b and Lambda0 decays, an
expected yield has the form
`N(Lambda_b) × B(Lambda_b→Lambda0 gamma) × B(Lambda0→p pi) × efficiency`,
where the efficiency is measured for the chosen mass window. The inclusive
background yield must be counted from the central sample with its own event
weights and generated-event denominator. Candidate counts alone are not
independent events when multiple combinations share an event.

## Generic winter2023 IDEA Z→bb baseline

Use only the centrally produced **`p8_ee_Zbb_ecm91`** sample under
`/eos/experiment/fcc/ee/generation/DelphesEvents/winter2023/IDEA/` for
this compatible background baseline. The official dictionary
`/cvmfs/fcc.cern.ch/FCCDicts/FCCee_procDict_winter2023_IDEA.json` records
**438,738,637 generated events** and `sumOfWeights` equal to that count.
The EOS directory currently exposes **4,398 ROOT files**. A direct header
check of the first 100 files found 100,000 `events` entries in each; the
ten-file [manifest](../../outputs/analysis/studies/Zbb_winter2023_baseline_manifest.json)
therefore selects exactly **1,000,000 entries** and stores their path list.
The campaign total comes from the official dictionary; all 4,398 file
headers have not been independently summed.

The 100-event [smoke output](../../outputs/analysis/studies/Zbb_winter2023_IDEA_smoke_100events.root)
used the unchanged one-photon Λγ reconstruction. It processed 100 events,
retained 96 after event prerequisites, and built 13 candidates in four
events in the 4.9–6.3 GeV fit interval; none was direct-signal truth matched.
The [candidate Parquet](../../outputs/analysis/studies/Zbb_winter2023_IDEA_smoke_100events.parquet)
retains mass, cos θp, hypothesis sign, multiplicity, and truth ancestry.
These counts establish schema compatibility and execution, not a reliable
background rate.

A separate 1,000-event single-thread benchmark on the same first file took
167.8 s wall time (156 s in the FCCAnalyses event loop), with 908 events
passing event prerequisites and 56 candidates in 33 events. Its output is
`Zbb_winter2023_IDEA_benchmark_1000events.root`. The event-loop rate is
about 6.4 events/s on one thread. This is a timing diagnostic and still far
too small for a stable background rate or a mass–angle shape.

Regenerate the input manifest and run the full ten-file baseline with:

```bash
env -u PYTHONPATH -u PYTHONHOME myenv/bin/python \
  studies/reconstruction/catalog_zbb_winter2023.py \
  --output outputs/analysis/studies/Zbb_winter2023_baseline_manifest.json \
  --max-files 10 --target-events 1000000
bash scripts/run_zbb_baseline.sh
```

The wrapper uses all ten verified files and defaults to 40 threads, the
number currently visible to this process (`nproc`), even when 48 are
requested. It omits `--nevents` because this pinned FCCAnalyses checkout disables its
multithreaded path when an event limit is supplied. The million-event run
is prepared, with a distinct output name, but has not yet been executed.
For restartable file-level batch work, launch
`bash scripts/run_zbb_file_chunk.sh INDEX 4` with indices 0–9. Ten such jobs
at four threads each fit the 40 CPUs currently visible to this process.
Keep each output and its source-file index when flattening: `event_entry`
is local to the job and is not globally unique across these ten outputs.
Pass `--source-id INDEX` to `flatten_candidates.py`; together with
`event_entry` and `candidate_slot`, it gives each batch candidate a stable
join key.
For a full-campaign run, partition the file list into independent batch
outputs and verify event counts before merging or summing candidate tables.

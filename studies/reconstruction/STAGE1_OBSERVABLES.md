# Stage-1 isolation and Z-pole observables

The existing `lb2lambda_gamma_reco.py` stage still builds and selects the
same Λb→Λ⁰γ candidates. `observables_stage1.py` calls
`lb_candidate_observables.h` after candidate construction. Its vectors align
with `lb_mass`; no new selection or truth-dependent computation is applied.
Constants are in `config/lb_observables.json`: ECM 91.2 GeV, the Λb/Λ/π⁰
masses, and cone radii 0.2, 0.3, 0.5. The pinned FCCAnalyses checkout is
`pre-edm4hep1` at `91c7d6c5a5c8ad5c3848d6d7cf8383e93c9b74e3`.

## Definitions

- Cone isolation sums all `ReconstructedParticles` except the candidate γ.
  `_E` branches divide measured energy sums by Eγ; other branches divide pT
  sums by pTγ. `noLambda` removes the candidate p and π as well. Charged
  and neutral branches split the R=0.3 no-Λ sum by charge.
- `Photon#0` supplies the candidate and π⁰-partner photons. `m_gg_best`
  chooses the other selected photon in the candidate photon's **same thrust
  hemisphere** closest to mπ⁰. The partner may lie outside the isolation
  cones. Missing partners have `dm_gg_pi0=-999`, `gamma2_index=-1`.
- These EDM4hep files do not persist Delphes `IsolationVar`.
  `iso_delphes=-999`, `iso_delphes_available=0`; the analysis cone values
  are separate observables, not replacements for that card variable.
- ROE comprises all reconstructed particles except the candidate p, π, γ.
  The pinned FCCAnalyses thrust axis is computed on ROE **after those removals**. The fitted
  Λ⁰ momentum determines which side is `p_same`; the other side is
  `p_other`. The builder now stores fitted Λ⁰ momentum components so that
  `p_sig` and photon rest-frame energy use the same fit as its Λb mass.
  With `pZ=(ECM,0,0,0)`, `p_rec=pZ−p_other` and
  `m_rec_all=m(pZ−sum(ROE))`. Balances and same-side energy/mass are direct
  four-vector arithmetic. No kinematic fit is done.
- `Estar_gamma` and `Estar_gamma_rec` use the `p_sig` and `p_rec` rest
  frames. Their residuals subtract the configured two-body value,
  **2.699 GeV** for the specified Λb and Λ masses.
- `dca_Lam_gamma`, `Lxyz_implied`, and `cos_dir_implied` are **pointing
  proxies**. The Λ line runs through its fitted SV; the photon ray is
  projected from the PV. This IDEA output has no measured photon production
  vertex, so these are not a Λb vertex fit or measured photon DCA.
- `lambda_pv_cos` is the cosine between fitted Λ⁰ momentum and PV→SV;
  `lambda_pv_dca` is the fitted Λ⁰ trajectory's line distance to the PV.
  They describe geometry relative to the interaction point, **not a signal
  pointing requirement**: the Λ⁰ originates at the displaced Λb vertex and
  need not point back to the PV. Neither is cut in stage-1. Early MT snapshots can derive these
  exactly from their saved fitted Λ⁰ momentum and PV/SV coordinates during
  flattening; `pointing_derived_in_flattening` records that provenance.

## First comparison

The first 1,000 input events of each forced Gamma and Eta sample and the
first 1,000 events of one winter2023 IDEA `p8_ee_Zbb_ecm91` file give the
unchanged candidate counts: Gamma 639 total/535 truth matched, Eta-as-Gamma
356 total, generic Zbb 56 total. The flattened tables are in
`outputs/analysis/studies/Lb2Lambda{gamma,eta,zbb}_observables_1000events_final_pointing.parquet`.
All requested 1D overlays plus PV geometry diagnostics and five 2D comparisons are in
`outputs/plots/reconstruction/stage1_observables_1000events_final_pointing/`, with
`summary.json` and `scan_table.md`.

The signal median `iso_R05` is 0.44; excluding Λ daughters reduces it to
0.16. At about 80% relative true-signal retention,
`iso_R03_noLambda≤0.226` keeps 428/535 truth-matched signal and 4/56 Zbb
candidates. This is a **same-sample, 56-candidate pilot**, not a validated
background efficiency or a default isolation cut.

Recoil is not a Λb mass estimator by itself here: true signal has median
`m_rec=22.8 GeV`, `deltaE=-13.6 GeV`, `E_same=9.9 GeV`. Same-side fragments
and missing particles enter the recoil; a requirement of `m_rec≈mΛb` or
`deltaE≈0` would discard signal. The recoil photon-rest-frame energy is
also broad (true-signal median 5.00 GeV), while `Estar_gamma` from the
fitted candidate is narrow around 2.70 GeV. Generic Zbb differs strongly
in same-side activity and energy balance, but the forced-signal and generic
samples need a larger, independent validation before cut tuning.

`scan_table.md` tests both one-sided cut directions for every new scalar
at about 80% and 50% **relative retention of valid truth-matched signal
candidates**. The same events choose and evaluate each threshold, so this
is exploratory and does not measure joint-cut performance. `dm_gg_pi0`
requires a separate no-partner pass category; a generic one-sided scan
would give the wrong denominator. In this 1,000-event pilot a ±20 MeV π⁰
veto removes 0/535 true signal and 2/56 generic Zbb candidates before
the tighter Λ⁰ mass window. No dedicated Λπ⁰ sample is present.

## Reproduction

Run the current stage with `fccanalysis run` and `--nevents 1000 --ncpus 1`
on each of these three inputs:

1. `outputs/delphes/Lb2LambdaGamma_nev500000_IDEA_edm4hep.root`
2. `outputs/delphes/Lb2LambdaEta_nev500000_IDEA_edm4hep.root`
3. `/eos/experiment/fcc/ee/generation/DelphesEvents/winter2023/IDEA/p8_ee_Zbb_ecm91/events_000083138.root`

Use distinct output names `Lb2Lambdagamma_observables_1000events_final.root`,
`Lb2Lambdaeta_observables_1000events_final.root`, and
`Lb2Lambdazbb_observables_1000events_final.root`. Flatten each with
`studies/reconstruction/flatten_candidates.py --mode gamma`, then run:

```bash
env -u PYTHONPATH -u PYTHONHOME myenv/bin/python \
  studies/reconstruction/plot_stage1_observables.py \
  --signal outputs/analysis/studies/Lb2Lambdagamma_observables_1000events_final_pointing.parquet \
  --eta outputs/analysis/studies/Lb2Lambdaeta_observables_1000events_final_pointing.parquet \
  --zbb outputs/analysis/studies/Lb2Lambdazbb_observables_1000events_final_pointing.parquet \
  --output-dir outputs/plots/reconstruction/stage1_observables_1000events_final_pointing
```

## Proposed cut string for a later paired review

This **template is disabled**. Learn numerical bounds on independent signal
and inclusive Zbb samples. In particular, do not centre `m_rec` on mΛb.

```python
# (lambda_flight_rxy_sig >= 2) &  # already applied by baseline builder
# (MREC_MIN < m_rec) & (m_rec < MREC_MAX) &
# (deltaE > DELTAE_MIN) &
# (ESTAR_REC_MIN < Estar_gamma_rec) & (Estar_gamma_rec < ESTAR_REC_MAX) &
# ((dm_gg_pi0 < 0) | (dm_gg_pi0 > PI0_HALF_WINDOW_GEV))
# Optional auxiliary: (iso_R03_noLambda < ISO03_MAX)
```

The requested pointing study needs a defensible Λb origin or photon direction
measurement before a pointing cut is proposed. The current
`dca_Lam_gamma` assumes the photon's ray originates at the PV, so it remains
a diagnostic. No isolation, recoil, Λ⁰ PV-pointing, or π⁰ cut is enabled in
stage-1.

## Larger candidate comparison and review note

**Question.** Can isolation and Z-event observables distinguish true
Λb→Λγ from inclusive Z→bb combinations and Λb→Λη(→γγ) reconstructed as
Λγ, while leaving the baseline candidate selection intact?

**Inputs and assumption.** The pinned `pre-edm4hep1` FCCAnalyses revision
processed 10,000 events from each local forced-decay IDEA EDM4hep file
with `--nevents 10000 --ncpus 1`, and all 100,000 events of the first
winter2023 IDEA `p8_ee_Zbb_ecm91/events_000083138.root` file with
`--ncpus 32`. Both configs above were unchanged. The Zbb output was
produced before the two PV-geometry branches were compiled, so flattening
derived them from stored fitted Λ momentum and PV/SV coordinates;
`pointing_derived_in_flattening=1` records this. Forced-decay outputs store
them directly (`0`). A separate 10-event direct-versus-NumPy check agreed
within 2.7×10⁻⁸ in cosine and 1.1×10⁻⁵ mm in line DCA.

The reconstruction commands were:

```bash
source external/FCCAnalyses/setup.sh
fccanalysis run analysis/studies/lb2lambda_gamma_reco.py \
  --files-list outputs/delphes/Lb2LambdaGamma_nev500000_IDEA_edm4hep.root \
  --output Lb2Lambda_gamma10k_pointing_observables.root --nevents 10000 --ncpus 1
fccanalysis run analysis/studies/lb2lambda_gamma_reco.py \
  --files-list outputs/delphes/Lb2LambdaEta_nev500000_IDEA_edm4hep.root \
  --output Lb2Lambda_eta10k_pointing_observables.root --nevents 10000 --ncpus 1
fccanalysis run analysis/studies/lb2lambda_gamma_reco.py \
  --files-list /eos/experiment/fcc/ee/generation/DelphesEvents/winter2023/IDEA/p8_ee_Zbb_ecm91/events_000083138.root \
  --output Lb2Lambda_zbb100k_observables.root --ncpus 32
```

| Sample | Input events | Events after event filter | Selected Λγ combinations | Labelled target candidates |
|---|---:|---:|---:|---:|
| Forced Λb→Λγ | 10,000 | 9,676 | 6,460 | 5,637 truth matched |
| Forced Λb→Λη(→γγ), reconstructed as Λγ | 10,000 | 9,617 | 3,429 | 2,613 ancestry matched feed-down |
| Inclusive winter2023 Zbb | 100,000 | 90,295 | 5,582 | 0 true Λγ |

The 5,637 truth-matched signal candidates occur in 5,637 distinct events
and correspond to 56.37% of forced input events, assuming one generated
signal per event. Other counts are candidate counts; multiple candidates
per event are retained.

**Observed effect.** `outputs/plots/reconstruction/stage1_observables_10k_100k/`
contains all requested overlays and exploratory same-sample scans. The
separate audit and truth-free model tables are in
`outputs/analysis/studies/training_stage1_10k_100k/`. In
`holdout_features.md`, each one-sided threshold/direction is chosen on
training events and evaluated on disjoint test events. At thresholds aiming
for 80% **relative** signal retention on train events:

| Diagnostic | Test true signal kept | Test Zbb rejected | Test η feed-down kept |
|---|---:|---:|---:|
| `iso_R03_noLambda ≤ 0.2112` | 659/823 | 680/788 | 196/389 |
| `iso_R05_noLambda ≤ 0.4101` | 656/823 | 717/788 | 243/389 |
| `deltaE ≥ −24.90 GeV` | 652/823 | 776/788 | 311/389 |
| `E_same ≤ 19.35 GeV` | 645/823 | 776/788 | 304/389 |
| Fixed resolved π⁰ veto ±20 MeV; no partner passes | 823/823 | 93/788 | 389/389 |

The π⁰ veto is evaluated but **not applied**. It does not reject the η
feed-down here. `m_gg_best` chooses the partner closest to π⁰, so it cannot
serve as a reliable dedicated η veto when several partners exist.

**Limitations and next decision.** The holdout splits by output event,
not by production file or generator campaign; generic background uses one
central file. In multithreaded FCCAnalyses output, `event_entry` groups
output events but need not equal the source ROOT entry number. The sharp
`E_same` and `deltaE` separation may reflect both candidate topology and
differences between local forced production and the central campaign.
These results provide no joint-cut efficiency, branching-fraction
normalization, expected yield, NN performance, or sensitivity. The audit
table retains all candidate and truth columns; the model table omits truth,
Λb mass, `cos_theta_p`, unmeasured-photon-origin proxies, and Λ⁰ PV
alignment. Before selecting thresholds or training a reference classifier,
validate on unseen winter2023 files and check mass/angle sculpting and
feed-down retention.

To reproduce the downstream products from the three flattened Parquet files:

```bash
env -u PYTHONPATH -u PYTHONHOME myenv/bin/python \
  studies/reconstruction/prepare_training_inputs.py \
  --signal outputs/analysis/studies/Lb2Lambda_gamma10k_pointing_observables.parquet \
  --eta outputs/analysis/studies/Lb2Lambda_eta10k_pointing_observables.parquet \
  --zbb outputs/analysis/studies/Lb2Lambda_zbb100k_observables.parquet \
  --output-dir outputs/analysis/studies/training_stage1_10k_100k \
  --signal-input-events 10000 --eta-input-events 10000 --zbb-input-events 100000
env -u PYTHONPATH -u PYTHONHOME myenv/bin/python \
  studies/reconstruction/validate_training_features.py \
  --input outputs/analysis/studies/training_stage1_10k_100k/training_inputs.parquet \
  --output outputs/analysis/studies/training_stage1_10k_100k/holdout_features.json
```

## Pre-BDT plot and slide set

`plot_prebdt_separation.py` makes six four-panel figures from the audit
table: mass/kinematics, photon isolation, Z recoil, fitted Λ topology,
daughter displacement, and photon partners/geometry. It overlays full truth-matched signal, wrong
combinations in the signal sample, ancestry-matched η feed-down, and generic
Zbb combinations. Each histogram uses its full class candidate count as
denominator, including missing and out-of-range values; curve areas can be
less than one. No physical yield normalization or new cut is introduced.

The editable slide source is `slides/stage1_observables.tex`. Because TeX is
not installed in this workspace, `slides/build_stage1_observables_pdf.py`
also builds a viewable `slides/stage1_observables.pdf` using the same panels.
The slide summary distinguishes IDEA response gates from the current offline
candidate selection and explains how isolation, ROE recoil, SV displacement,
and photon-origin diagnostics are constructed. In particular, no Λ⁰
PV-pointing requirement is imposed.

```bash
env -u PYTHONPATH -u PYTHONHOME myenv/bin/python \
  studies/reconstruction/plot_prebdt_separation.py \
  --input outputs/analysis/studies/training_stage1_10k_100k/candidate_audit.parquet \
  --output-dir outputs/plots/reconstruction/prebdt_10k_100k
env -u PYTHONPATH -u PYTHONHOME myenv/bin/python \
  slides/build_stage1_observables_pdf.py
```

## Projected-yield reference for mass and cosθp

`plot_yield_projection.py` applies candidate weights to the audit table and
produces mass, reconstructed `cos_theta_p`, and two-dimensional mass–angle
plots at four cumulative stages. The first stage is the existing reconstruction
baseline. The later stages are **exploratory plotting-side cuts**:
`|m(pπ)-mΛ|<10 MeV`, `iso_R03_noLambda≤0.211`, then `E_same≤19.35 GeV`.
The FCCAnalyses snapshot is unchanged. The stage-1 mass window is
4.9–6.3 GeV at every stage. A 5.4–5.9 GeV interval is tabulated only as a
diagnostic; it is not an added candidate cut.

The config `config/yield_projection.json` contains all editable physics
factors and source URLs. It uses 5×10¹² Z decays, `B(Z→bb)=0.1512`, and the
Z-pole **all b-baryon** fraction 0.084. Its `lambda_b_share_of_b_baryons=1`
is explicitly an upper-envelope proxy, not a measured Λb-specific fraction.
It uses the PI benchmark `B(Λb→Λγ)=10⁻⁵`, `B(Λb→Λη)=9.3×10⁻⁶`, and the
physical Λ→pπ and η→γγ fractions needed because the EvtGen chains were
forced. One expected candidate receives a constant sample weight; both b
and anti-b hadrons are included. Multiple candidates per event remain.
Generic Zbb is scaled from all generated Zbb events, while only full
truth-matched forced chains represent signal or eta feed-down. No signal
wrong-combination component is separately added because inclusive Zbb
already represents generic combinations at physical rates.

```bash
env -u PYTHONPATH -u PYTHONHOME myenv/bin/python \
  studies/reconstruction/plot_yield_projection.py \
  --input outputs/analysis/studies/training_stage1_10k_100k/candidate_audit.parquet \
  --config config/yield_projection.json \
  --output-dir outputs/plots/reconstruction/yield_projection_10k_100k
env -u PYTHONPATH -u PYTHONHOME myenv/bin/python \
  slides/build_yield_projection_pdf.py
```

The output directory contains `summary.json`, `summary.md`, and three plots
per stage. `slides/yield_projection.tex` is the editable presentation source;
`slides/yield_projection.pdf` is the viewable version. Counts and plot errors
show MC counting statistics only. With this 100k Zbb file, the final
exploratory stage has **seven** background MC candidates in the whole fit
range and **one** in 5.4–5.9 GeV. Empty mass–angle cells therefore lack MC
support; the projected shapes cannot yet be used as a reliable toy template.
The forced signal uses PHSP, so its angular shape is not a polarization
prediction. Use independent central Zbb files, a Λb-specific production
fraction, and the physics decay model before sensitivity toys.

**PI review note (29 September 2026).** Question: what physically scaled
mass–angle candidate levels do the present samples imply before and after
simple offline cuts? The reference is stage-1; the changed scenarios are
the three cumulative plotting-side cuts above. Inputs are the 10k/10k/100k
Parquet paths in `training_stage1_10k_100k/manifest.json`, made from the
same IDEA response and the local FCCAnalyses `pre-edm4hep1` checkout at
`91c7d6c5a5c8ad5c3848d6d7cf8383e93c9b74e3`. That manifest records the
reconstruction/observable config hashes; this projection's assumptions are
the named JSON config. The signal sequence retains 5,637 → 5,552 → 4,445
→ 3,575 distinct matched events, corresponding to cumulative 56.37%,
55.52%, 44.45%, and 35.75% per 10,000 generated input events. Generic Zbb
candidate counts are 5,582 → 814 → 97 → 7; eta matched counts are 2,613
→ 2,568 → 1,234 → 920. The exact conditional retentions and MC counting
errors are in `summary.md`. The projected final generic rate is controlled
by seven candidates, so it is a diagnostic scale, not a reliable expected
background or angular toy template. PI decision sought: whether to pursue
these offline variables and which Λb production fraction/scenario to use;
the reference reconstruction selection has not changed.

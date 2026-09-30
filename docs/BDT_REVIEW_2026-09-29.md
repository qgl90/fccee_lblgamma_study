# PI review: post-Λ BDT baseline, 29 September 2026

## Question and unchanged reference

Does a BDT built from reconstructed photon isolation, event closure, and
Λ topology reduce Winter2023 IDEA inclusive Z→bb combinations while
retaining Λb→Λ(pπ)γ candidates for the 4.9–6.3 GeV mass and cosθp fit?
The reference is `analysis/studies/lb2lambda_gamma_reco.py` with
`config/lb_reco.json`. Its stage-1 selections were not changed. The only
additional candidate cut before BDT training is the offline fitted-momentum
`|m(pπ)−1.115683|<0.010 GeV` window. Truth is attached after reconstruction.

## Exact comparison and denominators

The run uses 10,000 local forced PHSP signal events, 10,000 forced Λη events,
10,000 independent forced HELAMP signal events, and ten distinct 100,000-event
Winter2023 IDEA `p8_ee_Zbb_ecm91` files. The generator/IDEA card and pinned
FCCAnalyses revision are hashed in
`outputs/analysis/studies/bdt_winter2023_v1/provenance.txt`.
The central file list is
`outputs/analysis/studies/Zbb_winter2023_baseline_manifest.files.txt`.
Each file is reconstructed and flattened separately, with source IDs 0–9.
The post-Λ table and every input hash are recorded in
`outputs/analysis/studies/bdt_winter2023_v1/manifest.json`.

The run is reproducible stage by stage with `scripts/run_bdt_study.sh` as
documented in `docs/BDT_WORKFLOW.md`. This particular run reused the
already reconstructed 10k PHSP and Λη candidate tables:

```bash
export SIGNAL_PARQUET=outputs/analysis/studies/Lb2Lambda_gamma10k_pointing_observables.parquet
export ETA_PARQUET=outputs/analysis/studies/Lb2Lambda_eta10k_pointing_observables.parquet
export PHYSICS_PARQUET=outputs/analysis/studies/Lb2LambdaGammaPhysics_10k_bdt.parquet
bash scripts/run_bdt_study.sh flatten
bash scripts/run_bdt_study.sh dataset
bash scripts/run_bdt_study.sh statistics
bash scripts/run_bdt_study.sh train
SIGNAL_EDM=outputs/delphes/Lb2LambdaGamma_nev500000_IDEA_edm4hep.root \
  PHYSICS_EDM=outputs/delphes/chunks/Lb2LambdaGammaPhysics_nev10000_chunk0_IDEA_edm4hep.root \
  bash scripts/run_bdt_study.sh angular
bash scripts/run_bdt_study.sh projection
bash scripts/run_bdt_study.sh slides
```

Stage-1 gives 5,637 true PHSP signal, 56,163 inclusive Zbb, and 2,613
true Λη feed-down **candidates**. The fitted-Λ window retains 5,552,
8,063, and 2,568, respectively; 619 other forced-sample combinations
also remain in the audit. The corresponding *distinct generated-event*
PHSP signal efficiencies are 56.37% and 55.52%.

The BDT trains only on true PHSP signal and generic Zbb. Zbb files 0–6
train, file 7 validates, and files 8–9 test; PHSP candidates are split by
event hash. Λη and wrong combinations are scored for diagnostics. All 39
model inputs and construction/units are in `docs/BDT_FEATURES.md`.
The Λγ mass, cosθp, truth, and event/source identifiers are excluded.

## Observed effect

The held-out test has 811 true PHSP and 1,655 generic Zbb candidates
after the fitted-Λ window. Its AUC is 0.99896. The validation `sig80`
threshold is score ≥0.99127. It keeps 621/811 test signal candidates
(76.6% conditional retention) and 0/1,655 test Zbb candidates. In the
**diagnostic** 5.4–5.9 GeV peak interval it keeps 605/793 test signal,
0/526 test Zbb, and 526/732 Λη candidates. The 621 selected test-signal
events out of 1,486 generated PHSP test decays correspond to 41.8%
acceptance × reconstruction × post-Λ/BDT efficiency. All counts are
candidate counts unless explicitly called events or decays.

The BDT gain plot is led by `E_same`, `deltaE`, hemisphere alignment,
candidate pT, and no-Λ isolation. Thus the learned separation strongly
uses same-side activity and event closure. The saved held-out mass/angle
shape plot and generated-angle acceptance plot must be inspected before a
mass–angular fit; excluding fit observables from inputs alone does not
prove an unsculpted selection.

The independent HELAMP sample has 5,503 matched post-Λ candidates from
10,000 generated events. At the same frozen `sig80` threshold, 4,380
survive (43.80% absolute forced-event efficiency). Generated cosθp is
strongly asymmetric, unlike PHSP; the selected/generated efficiency is
shown in ten angular bins with the generated counts behind it. The supplied
LHCb decay file gives HELAMP parameters, but its `PolarizedLambdab: yes`
metadata does not establish the FCC-ee Λb production spin-density model.

## Yield scenario and statistical limit

`config/yield_projection.json` assumes 5×10¹² Z, B(Z→bb)=0.1512,
f(b→all weakly decaying b baryons)=0.084, and a **Λb share of one** as an
upper-envelope proxy. B(Λb→Λγ)=10⁻⁵ is the PI benchmark. Under these
assumptions, one held-out Zbb test candidate represents 3.78 million
expected candidates. The observed zero survivors at `sig80` therefore
means an approximate 95% Poisson upper of three test candidates, or
11.34 million projected Zbb candidates in the peak diagnostic interval;
it does **not** mean zero expected background. At that score the signal
upper proxy is about 331,000 peak candidates and the Λη contribution
about 15,700. The `metrics.json` derived 2.84% “purity with Zbb upper”
is an illustrative ratio using *both* a Zbb count upper bound and a signal
production upper proxy, not a confidence bound on physical purity.

With zero test survivors, the current 200k independent Zbb test events
support a conditional post-Λ rejection lower bound of about 1,655/3≈552
at 95% confidence. The planning estimate in `statistics_needed.json`
requires about 3.49 million / 31.4 million / 282 million **total** Zbb
events, assuming a 20% independent test split, to bound the background
for 10% / 50% / 90% peak purity at 80% relative signal retention.
Those numbers are scenario planning estimates and omit uncertainty in
the Λb-specific fragmentation fraction and domain differences.

## Limitations and next decision

The HELAMP multithreaded reconstruction snapshot has processed
`event_entry` rows that do not preserve generator-file entry order after
part of the job. Its 5,503 selected decays were validated against the
generated sample by unique truth cosθp and charge content before drawing
the angular efficiency. Do not join this HELAMP table to generator rows by
`event_entry` until the snapshot mapping is repaired.

The high AUC may partly distinguish **local forced signal production**
from **central Winter2023 generic Zbb production**, especially through
`E_same` and `deltaE`. The file-held-out test checks within-campaign Zbb
generalization, but it cannot resolve that signal-domain issue. The PI
should review the gain and mass–angle plots, then obtain matched-campaign
signal and more independent Zbb events before freezing a BDT working point
or claiming peak purity. A Λb-specific Z-pole production fraction and a
validated angular physics generator are required before sensitivity toys.

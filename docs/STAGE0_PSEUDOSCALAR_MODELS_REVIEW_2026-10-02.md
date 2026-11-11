# Stage 0 η and π⁰ angular-model comparison for PI review

Author: Renato Quagliani (rquaglia@cern.ch)

## Question and choice to review

Provide both phase-space and physics-motivated HELAMP generator variants for
Λb→Λ(pπ)η(γγ) and Λb→Λ(pπ)π⁰(γγ), while keeping the older η PHSP and π⁰
HELAMP names stable. This is a generator-scenario comparison, not a change
to Stage 1 reconstruction or the offline reference selection.

## Model assumptions

The new η HELAMP uses the S1 η-mixing scheme in Table II of
[Rui, Li and Zhang, Phys. Rev. D 107, 093008 (2023)](https://arxiv.org/pdf/2302.13785).
Its complex S- and P-wave amplitudes give α(Λb→Λη) ≈ +0.733 after
conversion to two normalized EvtGen helicity amplitudes, including their
relative phase. The same paper reports model dependence, and a separate
theory estimate has an opposite sign. Thus “physics” here means a **named
PQCD benchmark**, not an experimentally established amplitude.

The π⁰ HELAMP remains the previously documented α = −0.89 theory benchmark
from [Mohanta, Giri and Khanna](https://arxiv.org/pdf/hep-ph/0006109); its
relative phase is set to zero because the cited asymmetry alone does not fix
it. Both HELAMP files use Λ→pπ amplitudes `.906, .423` as in the existing
Λγ physics sample. The PHSP files use phase space for both Λb and Λ decays.
All four force the meson to γγ with PHSP. Forced fractions do not represent
physical branching fractions.

## Provenance and commands

The 200-event pilots use the same Pythia8 Z→bb card, IDEA Delphes card,
EvtGen `DECAY.DEC` and `evt.pdl`, and 2023-04-08 generation stack described
in [the production howto](../howto/delphes_production.md). Repository HEAD
was `981266ad31ad0e39f5a7344c89fdc00c3d3f0603` with the changes in
this note uncommitted. Local FCCAnalyses revision was
`0315db1e2941e2886813cb645193e348f3863d5d`; FCCAnalyses is not part
of these Stage 0 pilot runs.

| Mode | Exact generation command | Decay-file SHA256 |
|---|---|---|
| η PHSP | `bash scripts/produce_chunk.sh Lb2LambdaEta 0 91701 200 200` | `9102fccd8553d0c2328aa7cb0aaa909c1664e5e6e982e3a7a0f74735db7a71c5` |
| η HELAMP | `bash scripts/produce_chunk.sh Lb2LambdaEtaPhysics 0 91901 200 200` | `8b79147f78c656a9b75cad399648cb4e027a44eee7b1311207cb2af6ebaf4b3b` |
| π⁰ PHSP | `bash scripts/produce_chunk.sh Lb2LambdaPi0 0 92001 200 200` | `9f144a02a6a7b0685097e8b975e63caaa95339a6aff9607cdc0b8fee5f2cd80d` |
| π⁰ HELAMP | `bash scripts/produce_chunk.sh Lb2LambdaPi0Physics 0 91801 200 200` | `ca8b154eb122ce01d540ca28cf8b5498a4fde504b61bdf034b4fa` |

Common SHA256 inputs: `config/config.yaml`
`02aadf6202c3fb32a80a3b2fd294ea799c13a9065f93e03251f7725cf17f9394`;
Pythia card `3fae9b7cd90c8ce5436ec6dd254f54d91fb0cb73f1ea7805c1551b3b359f8a09`;
IDEA card `11d81b4ee2bafa33e0715c4a390d235e38487521ce8e43bdb360890c9e8ec3d3`;
EDM4hep mapping `e834548595517fa2ea9fbc25dd96b9c408507c6cabc61da8feb1cbada8624982`;
`DECAY.DEC` `ac3161823b4e69a2d2629a7174484682083abe52c361558bcb07ef0a7ca0f799`;
`evt.pdl` `b337e3a332ed3d25d688f466cf3e57752d3609a1a3be41b1c6bb6cb283d5dd1a`.

The exact MC audit and plotting commands are in the howto. ROOT pilot
outputs and generator logs are under `outputs/delphes/chunks/` and
`outputs/logs/`. All JSON audits, per-decay angle CSVs, and plots are in
`outputs/analysis/studies/stage0_pseudoscalar_models_20261002/`.

## Observed pilot comparison

The denominator in each row is **200 output events**. A complete chain is a
direct generated Λb or anti-Λb→Λ(pπ) plus the named meson, with the meson
decaying to two photons. The helicity angle is between the (anti)proton and
the negative Λb momentum in the Λ rest frame. Its error is the standard error
of the generated-decay mean.

| Mode | Complete chains | Λb / anti-Λb | Mean cos θp | HELAMP expectation |
|---|---:|---:|---:|---:|
| η PHSP | 200 | 100 / 100 | +0.010 ± 0.041 | uniform, mean 0 |
| η HELAMP | 200 | 101 / 99 | +0.214 ± 0.039 | mean ≈ +0.157 |
| π⁰ PHSP | 200 | 102 / 98 | −0.033 ± 0.040 | uniform, mean 0 |
| π⁰ HELAMP | 200 | 86 / 114 | −0.215 ± 0.038 | mean ≈ −0.190 |

All four chains contain both charge signs. The η HELAMP pilot mean is about
1.5 standard errors above its model expectation; the π⁰ HELAMP mean is
consistent within one standard error. At 200 events these are useful sign
and syntax checks, not precision model tests. The comparison plot uses
normalized generated counts, independent pilot seeds, and the expected
curves; no detector or Stage 1 selection has been applied.

## Limitations and next step

The 100k jobs have not been run. The Snakemake dry run resolves twenty
generation chunks and two merges for the two added modes; their Stage 1
dry run adds the same reconstruction rule for each. The generated Condor
queue has 60 jobs across all six forced modes. The next physics comparison
is to run the same one-photon Stage 1 reconstruction and offline veto study
on η/π⁰ PHSP and HELAMP samples, with true ancestry and candidate counts
reported separately. The PI should choose which η theory scenario, if any,
becomes the reference feed-down model before projecting a physical yield.

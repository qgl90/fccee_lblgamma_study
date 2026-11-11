# Stage 0 π⁰ generation pilot for PI review

Author: Renato Quagliani (rquaglia@cern.ch)

## Question and scenario

Can the existing Pythia8/EvtGen/Delphes production path create a forced
Λb→Λ(pπ)π⁰(γγ) physics benchmark, including its charge conjugate, for a
one-photon Stage 1 background study? This is a new named forced-decay
scenario. It does not replace the γ or η baseline.

## Assumptions and provenance

- The HELAMP magnitude ratio encodes α(Λb→Λπ⁰) = −0.89 predicted in
  [Mohanta, Giri and Khanna, Table 4](https://arxiv.org/pdf/hep-ph/0006109).
  The relative phase is set to zero because that prediction does not fix it.
  The Λ→pπ amplitudes `.906, .423` are copied from
  `evtgen/Lb2LambdaGamma_trpol.dec`. The forced decay probabilities are not
  branching fractions and no Λb production polarization is specified.
- Pilot command: `bash scripts/produce_chunk.sh Lb2LambdaPi0Physics 0 91801 200 200`.
  This uses the `2023-04-08` Key4hep generation stack configured in
  `config/config.yaml`; Pythia8 Z→bb at 91.188 GeV and the IDEA Delphes card.
- Repository HEAD at validation: `981266ad31ad0e39f5a7344c89fdc00c3d3f0603`,
  with the changes described here uncommitted. Local FCCAnalyses revision:
  `0315db1e2941e2886813cb645193e348f3863d5d` (not used by Stage 0).
- SHA256: `config/config.yaml` `192fd3e0f615f32b844798b66002cbb683889f7b0bfa9806942f9893c61b7dc1`;
  `cards/p8_ee_Zbb_ecm91_EVTGEN.cmd` `3fae9b7cd90c8ce5436ec6dd254f54d91fb0cb73f1ea7805c1551b3b359f8a09`;
  `cards/card_IDEA.tcl` `11d81b4ee2bafa33e0715c4a390d235e38487521ce8e43bdb360890c9e8ec3d3`;
  `cards/edm4hep_IDEA.tcl` `e834548595517fa2ea9fbc25dd96b9c408507c6cabc61da8feb1cbada8624982`;
  `evtgen/DECAY.DEC` `ac3161823b4e69a2d2629a7174484682083abe52c361558bcb07ef0a7ca0f799`;
  `evtgen/evt.pdl` `b337e3a332ed3d25d688f466cf3e57752d3609a1a3be41b1c6bb6cb283d5dd1a`;
  `evtgen/Lb2LambdaPi0.dec` `ca8b154eb122ce01d540ca28cf8b5498a4fde504b61bdf034b4fa`.

## Exact validation and observed effect

The output is
`outputs/delphes/chunks/Lb2LambdaPi0Physics_nev200_chunk0_IDEA_edm4hep.root`;
its production log is in `outputs/logs/`. `check_root_entries.py` confirmed
200 `events` entries. The generated-chain audit, JSON, and angular plot are
under `outputs/analysis/studies/stage0_pi0_20261002/`.

| Quantity | Pilot count or value |
|---|---:|
| Input / processed events | 200 / 200 |
| Complete Λb→Λ(pπ)π⁰(γγ) chains | 200 |
| Λb / anti-Λb complete chains | 86 / 114 |
| Events with ≥1 / >1 complete chain | 200 / 0 |
| All Λb parents in output | 204 |
| Mean generated cos θp | −0.215 ± 0.038 |

The cascade expectation from the selected HELAMP magnitudes is approximately
αb αΛ / 3 = −0.190 for the mean cos θp. The pilot mean agrees within its
statistical precision. The Snakemake dry run resolves ten 10k-event π⁰ chunks
and a merge; the Condor queue writer resolves 40 jobs across the four 100k
modes. The Snakemake dry run for the π⁰ Stage 1 ROOT target resolves those
generation jobs plus the shared reconstruction rule. Shell syntax and Python
compilation checks passed.

## Limitations and proposed next step

The 200-event output tests the file syntax, complete ancestry, charge
conjugation, and the sign/scale of the angular response. It does not validate
the Λb→Λπ⁰ asymmetry prediction, a relative phase, a physical π⁰ branching
fraction, or detector selection efficiency. The forced π⁰ sample must not be
scaled as an inclusive Zbb yield. Before designating it a reference
background, compare its one-photon Stage 1 reconstructed mass, candidate
counts, and same-hemisphere second-photon behavior with the unchanged η and
γ scenarios, then review the model choice with the PI. The 100k production
and full Stage 1 processing have **not** been run here.

# Stage 0: generate and simulate the Stage 1 inputs

Author: Renato Quagliani (rquaglia@cern.ch)

Run commands from the repository root in a fresh shell. This stage produces
EDM4hep `events` trees. Stage 1 then reconstructs Λb→Λ(pπ)γ candidates from
these files; generation truth is used only to label and validate candidates.
See [Stage 1](stage1.md) for reconstruction and
[the analysis workflow](../docs/ANALYSIS_WORKFLOW.md) for review gates.

## What runs

`scripts/produce_chunk.sh` prepares a Pythia8 card with the requested seed and
event count, sources the generation Key4hep stack, and invokes
`DelphesPythia8EvtGen_EDM4HEP_k4Interface`. Its inputs are:

| Role | File |
|---|---|
| Z→bb generation at 91.188 GeV | `cards/p8_ee_Zbb_ecm91_EVTGEN.cmd` |
| IDEA detector and EDM4hep mapping | `cards/card_IDEA.tcl`, `cards/edm4hep_IDEA.tcl` |
| EvtGen particle and inclusive decays | `evtgen/evt.pdl`, `evtgen/DECAY.DEC` |
| Forced Λb decay | The mode-specific `.dec` file below |

Pythia8 creates the event and the interface uses EvtGen for the selected
Λb decay and its conjugate. The forced fractions in `.dec` files are not
physical branching fractions. This interface writes events containing the
requested forced decay: the 200-event π⁰ pilot had 200 complete chains, one
per event. Still record generated decays and `events` entries separately;
multiple Λb parents can occur in one event, and another production setup
need not have the same one-chain-per-event relation.

| Sample name | Forced chain | Decay file | 100k seed base |
|---|---|---|---:|
| `Lb2LambdaGamma` | Λb→Λγ, phase space | `evtgen/Lb2LambdaGamma.dec` | 71501 |
| `Lb2LambdaGammaPhysics` | Λb→Λγ, LHCb HELAMP scenario | `evtgen/Lb2LambdaGamma_trpol.dec` | 71601 |
| `Lb2LambdaEta` | Λb→Λη, η→γγ, PHSP | `evtgen/Lb2LambdaEta.dec` | 71701 |
| `Lb2LambdaPi0Physics` | Λb→Λπ⁰, π⁰→γγ, HELAMP benchmark | `evtgen/Lb2LambdaPi0.dec` | 71801 |
| `Lb2LambdaEtaPhysics` | Λb→Λη, η→γγ, HELAMP benchmark | `evtgen/Lb2LambdaEtaPhysics.dec` | 71901 |
| `Lb2LambdaPi0` | Λb→Λπ⁰, π⁰→γγ, PHSP | `evtgen/Lb2LambdaPi0PHSP.dec` | 72001 |

The π⁰ HELAMP benchmark takes α(Λb→Λπ⁰) = −0.89 from Table 4 of
[Mohanta, Giri and Khanna](https://arxiv.org/pdf/hep-ph/0006109), with
`H+ = sqrt((1+α)/2) = 0.23452079` and
`H− = sqrt((1−α)/2) = 0.97211110`. The source predicts an asymmetry;
it does not determine the relative helicity phase. The zero phase here is
an explicit assumption, and no Λb production polarization is supplied by
this file. Λ→pπ uses the HELAMP daughter amplitudes of the existing
Λb→Λγ physics scenario. This is a **theory benchmark**, subject to PI
review of the amplitude model and a generated-angle validation. The π⁰
decays to two photons through `PHSP`.

The η HELAMP benchmark uses the S1 mixing scheme complex S- and P-wave
amplitudes in Table II of [the PQCD calculation by Zhou et al.](https://arxiv.org/pdf/2302.13785):
`M_S = −1.9 − 11.2i` and `M_P = −8.9 + 32.1i` in common units. Taking
`r = m(Λ)/m(Λb)`, its two helicity amplitudes are proportional to
`(1+r)M_S ∓ (1−r)M_P`. The resulting normalized HELAMP parameters are
`H+ = 0.93082244` at phase zero and `H− = 0.36547173` at relative phase
`−2.61205672` radians, giving α ≈ +0.733. This is **one theoretical
scenario**: the same paper reports other predictions, including a model
with opposite asymmetry sign. The PHSP files have no parent or Λ daughter
spin correlations. In all four η/π⁰ modes the meson decay to γγ is PHSP.

## Environment and provenance

The generation stack is set in `config/config.yaml` and can be overridden with
`GEN_SETUP`. It differs from the FCCAnalyses reconstruction environment.
Do not source a Key4hep stack before running the helper; each chunk sources
the generation stack itself. In a clean shell:

```bash
cd /afs/cern.ch/work/r/rquaglia/fcc_ee/fccee_lblgamma_study
bash scripts/check_environment.sh
git rev-parse HEAD
git -C external/FCCAnalyses rev-parse HEAD
sha256sum config/config.yaml cards/p8_ee_Zbb_ecm91_EVTGEN.cmd \
  cards/card_IDEA.tcl cards/edm4hep_IDEA.tcl \
  evtgen/DECAY.DEC evtgen/evt.pdl \
  evtgen/Lb2LambdaEta.dec evtgen/Lb2LambdaEtaPhysics.dec \
  evtgen/Lb2LambdaPi0PHSP.dec evtgen/Lb2LambdaPi0.dec
```

Keep the command, hashes, seed, event count, output, and generator log in the
campaign record. Existing output files are reused after an entry-count check,
so use a new campaign name/seed when changing a card or decay file. The helper
does **not** compare those input hashes when deciding to reuse a file.

## Bounded pilot before production

This is a 200-event π⁰ syntax and output check with a seed distinct from the
100k production range. It writes a uniquely named trial chunk:

```bash
bash scripts/produce_chunk.sh Lb2LambdaPi0Physics 0 91801 200 200
tail -n 40 outputs/logs/Lb2LambdaPi0Physics_nev200_chunk0.production.log
env -u PYTHONPATH -u PYTHONHOME \
  XDG_CACHE_HOME="$PWD/outputs/analysis/studies/stage0_pi0_20261002/cache" \
  MPLCONFIGDIR="$PWD/outputs/analysis/studies/stage0_pi0_20261002/mplcache" \
  myenv/bin/python \
  studies/reconstruction/audit_generated_forced_chain.py \
  --input outputs/delphes/chunks/Lb2LambdaPi0Physics_nev200_chunk0_IDEA_edm4hep.root \
  --mode pi0 --max-events 200 --expected-alpha -0.89 \
  --output outputs/analysis/studies/stage0_pi0_20261002/generated_chain_audit.json \
  --plot outputs/analysis/studies/stage0_pi0_20261002/generated_cos_theta_p.png
```

The output is
`outputs/delphes/chunks/Lb2LambdaPi0Physics_nev200_chunk0_IDEA_edm4hep.root`.
The helper checks that its `events` tree has exactly 200 entries. Inspect the
MC truth audit to confirm both Λb charges and the Λ(pπ)π⁰(γγ) chain before
using the sample for a physics comparison. The pilot is a technical
validation, not an efficiency measurement. The current pilot audit finds
86 Λb and 114 anti-Λb complete chains in 200 events.
The generated mean cos θp is −0.215 ± 0.038, consistent at this pilot size
with the nominal cascade expectation −0.190 from αb = −0.89 and the Λ
daughter amplitudes. This checks the sign and approximate size of the
implemented angular response; it does not establish a measured physical model.

To check the two newly added modes in the same bounded way, use separate
200-event pilot names and seeds:

```bash
bash scripts/produce_chunk.sh Lb2LambdaEtaPhysics 0 91901 200 200
bash scripts/produce_chunk.sh Lb2LambdaPi0 0 92001 200 200

env -u PYTHONPATH -u PYTHONHOME myenv/bin/python \
  studies/reconstruction/audit_generated_forced_chain.py \
  --input outputs/delphes/chunks/Lb2LambdaEtaPhysics_nev200_chunk0_IDEA_edm4hep.root \
  --mode eta --max-events 200 --expected-alpha 0.733 \
  --output outputs/analysis/studies/stage0_pseudoscalar_models_20261002/eta_physics_audit.json \
  --plot outputs/analysis/studies/stage0_pseudoscalar_models_20261002/eta_physics_cos_theta_p.png \
  --angles-output outputs/analysis/studies/stage0_pseudoscalar_models_20261002/eta_physics_angles.csv

env -u PYTHONPATH -u PYTHONHOME myenv/bin/python \
  studies/reconstruction/audit_generated_forced_chain.py \
  --input outputs/delphes/chunks/Lb2LambdaPi0_nev200_chunk0_IDEA_edm4hep.root \
  --mode pi0 --max-events 200 \
  --output outputs/analysis/studies/stage0_pseudoscalar_models_20261002/pi0_phsp_audit.json \
  --plot outputs/analysis/studies/stage0_pseudoscalar_models_20261002/pi0_phsp_cos_theta_p.png \
  --angles-output outputs/analysis/studies/stage0_pseudoscalar_models_20261002/pi0_phsp_angles.csv
```

For the four-way generated-angle comparison, also produce the η PHSP pilot
and audit both previously available variants into the same folder:

```bash
bash scripts/produce_chunk.sh Lb2LambdaEta 0 91701 200 200

env -u PYTHONPATH -u PYTHONHOME myenv/bin/python \
  studies/reconstruction/audit_generated_forced_chain.py \
  --input outputs/delphes/chunks/Lb2LambdaEta_nev200_chunk0_IDEA_edm4hep.root \
  --mode eta --max-events 200 \
  --output outputs/analysis/studies/stage0_pseudoscalar_models_20261002/eta_phsp_audit.json \
  --angles-output outputs/analysis/studies/stage0_pseudoscalar_models_20261002/eta_phsp_angles.csv

env -u PYTHONPATH -u PYTHONHOME myenv/bin/python \
  studies/reconstruction/audit_generated_forced_chain.py \
  --input outputs/delphes/chunks/Lb2LambdaPi0Physics_nev200_chunk0_IDEA_edm4hep.root \
  --mode pi0 --max-events 200 --expected-alpha -0.89 \
  --output outputs/analysis/studies/stage0_pseudoscalar_models_20261002/pi0_physics_audit.json \
  --angles-output outputs/analysis/studies/stage0_pseudoscalar_models_20261002/pi0_physics_angles.csv
```

Then run:

```bash
env -u PYTHONPATH -u PYTHONHOME myenv/bin/python \
  studies/reconstruction/plot_pseudoscalar_model_comparison.py \
  --eta-phsp outputs/analysis/studies/stage0_pseudoscalar_models_20261002/eta_phsp_angles.csv \
  --eta-physics outputs/analysis/studies/stage0_pseudoscalar_models_20261002/eta_physics_angles.csv \
  --pi0-phsp outputs/analysis/studies/stage0_pseudoscalar_models_20261002/pi0_phsp_angles.csv \
  --pi0-physics outputs/analysis/studies/stage0_pseudoscalar_models_20261002/pi0_physics_angles.csv \
  --output outputs/analysis/studies/stage0_pseudoscalar_models_20261002/model_comparison_cos_theta_p.png
```

The exact pilot commands, counts, and model assumptions are recorded in
[the η/π⁰ review note](../docs/STAGE0_PSEUDOSCALAR_MODELS_REVIEW_2026-10-02.md).

## 100k production: local Snakemake or Condor

`config/config.yaml` sets ten independent 10k-event chunks per sample.
Chunk `i` uses `seed base + i`. Snakemake and Condor call the same
`scripts/produce_chunk.sh`; both write
`outputs/delphes/chunks/SAMPLE_nev100000_chunkI_IDEA_edm4hep.root`.
On a local machine, preview the π⁰ target, then run it:

```bash
env -u PYTHONPATH -u PYTHONHOME XDG_CACHE_HOME="$PWD/.snakemake/cache" \
  myenv/bin/python -m snakemake --snakefile Snakefile --cores 1 \
  outputs/delphes/Lb2LambdaPi0Physics_nev100000_IDEA_edm4hep.root \
  --dry-run --printshellcmds

env -u PYTHONPATH -u PYTHONHOME XDG_CACHE_HOME="$PWD/.snakemake/cache" \
  myenv/bin/python -m snakemake --snakefile Snakefile --cores 10 \
  outputs/delphes/Lb2LambdaPi0Physics_nev100000_IDEA_edm4hep.root
```

For Condor, edit `REPO_DIR` in
`scripts/condor_forced_samples_100k.sub` to the checkout visible on workers.
The generated queue now contains all six configured samples, 60 chunks in
total. Inspect it before submitting; the submit wrapper submits **all six**
samples, including any completed chunks, which are checked and reused.

```bash
scripts/submit_forced_samples_100k_condor.sh --dry-run
scripts/submit_forced_samples_100k_condor.sh
```

After all chunks for a sample finish, merge and validate. For π⁰:

```bash
bash scripts/merge_chunks.sh Lb2LambdaPi0Physics 100000 10
```

Use the same command with any of the six sample names above to merge those
modes. The final files are under
`outputs/delphes/SAMPLE_nev100000_IDEA_edm4hep.root`; logs are under
`outputs/logs/`. Copy only checked final files to the EOS location intended
for Stage 1, recording source and destination checksums. For the centrally
produced inclusive Zbb input, use `config/zbb_winter2023_full_file_list.txt`
or the Stage 1 `--input-glob` instructions; this forced-sample generator does
not create an inclusive Zbb normalization sample.

## Handoff to Stage 1

Reconstruct each η and π⁰ sample with the **same one-photon** Λb→Λγ code and
config used for γ. This deliberately creates the possible partially
reconstructed Λb→Λη or Λb→Λπ⁰ background when one meson photon is selected.
The legacy `lbgamma_eta` label means η PHSP, and `lbgamma_pi0` means π⁰
HELAMP; the additional labels name their model explicitly:

```bash
scripts/run_reco_preselection.sh lbgamma_pi0 \
  outputs/delphes/Lb2LambdaPi0Physics_nev100000_IDEA_edm4hep.root \
  outputs/analysis/studies/stage1_pi0_20261002/lbgamma_pi0.root \
  all config/lb_reco_preselection_15mev_45_65_3d.json 4

scripts/run_reco_preselection.sh lbgamma_eta_physics \
  outputs/delphes/Lb2LambdaEtaPhysics_nev100000_IDEA_edm4hep.root \
  outputs/analysis/studies/stage1_eta_physics_20261002/lbgamma_eta_physics.root \
  all config/lb_reco_preselection_15mev_45_65_3d.json 4

scripts/run_reco_preselection.sh lbgamma_pi0_phsp \
  outputs/delphes/Lb2LambdaPi0_nev100000_IDEA_edm4hep.root \
  outputs/analysis/studies/stage1_pi0_phsp_20261002/lbgamma_pi0_phsp.root \
  all config/lb_reco_preselection_15mev_45_65_3d.json 4

scripts/run_reco_preselection.sh lbgamma_eta \
  outputs/delphes/Lb2LambdaEta_nev100000_IDEA_edm4hep.root \
  outputs/analysis/studies/stage1_eta_phsp_20261002/lbgamma_eta.root \
  all config/lb_reco_preselection_15mev_45_65_3d.json 4
```

For a development check, use the distinct pilot input, output path, and an
event limit of at most 1,000. Compare true π⁰ ancestry, selected candidate
counts, and same-hemisphere partner-photon variables with the unchanged γ
and η baselines before deciding whether π⁰ enters an offline reference cut.
Forced π⁰ and η samples provide shapes and conditional efficiencies; their
raw counts must not be scaled as inclusive Zbb background yields.

# 1M-event Λb→Λ⁰γ Physics campaign: ten selected chunks

This campaign is separate from the existing 100k/500k generation targets.
It uses the existing HELAMP Physics decay file
`evtgen/Lb2LambdaGamma_trpol.dec` with the `Lb2LambdaGammaPhysics` generator
mode, IDEA Delphes card and EDM4hep mapping. It defines ten independent
100,000-event chunks (1,000,000 events in total), with seeds 72601–72610.
Forced-decay counts remain conditional samples, not physical Z→bb yields.

The campaign configuration is `config/lbgamma_physics_1m_campaign.yaml`.
Its prepared provenance record, including card, decay and Stage 1 config
hashes, is `docs/data/lbgamma_physics_1m_20261006/study_manifest.json`.
Stage 0 chunks default to
`/eos/lhcb/lbdt3/user/rquaglia/fcc_ee/lblgamma/outputs/stage0_lbgamma_physics_1m_20261006/`;
override this with `LB_DELPHES_OUTPUT_DIR`. Outputs use the standard chunk
names and include their count in the basename.

## Generate selected Stage 0 chunks

Preview the campaign and select any chunk IDs from 0 through 9:

```bash
scripts/run_lbgamma_physics_1m.sh stage0 --check --chunks 0,1
```

Run only those chunks locally:

```bash
scripts/run_lbgamma_physics_1m.sh stage0 --run --chunks 0,1
```

To submit only those selected generation chunks to Condor, use
`scripts/run_lbgamma_physics_1m.sh stage0 --run --executor condor --chunks 0,1`.
The wrapper writes a queue containing only those requested chunk IDs.

Each chunk runs through `scripts/produce_chunk.sh`, which checks for an
existing output and verifies its event count and provenance before reusing it.
This setup step has not generated or submitted any chunks.

## Reconstruct selected chunks through FCCAnalyses

Check that selected Stage 0 files exist:

```bash
scripts/run_lbgamma_physics_1m.sh stage1 --check --chunks 0,1
```

Run those files locally through the v5 `RDFanalysis` and the
`processList`-style Stage 1 entry point:

```bash
scripts/run_lbgamma_physics_1m.sh stage1 --run --executor local --chunks 0,1
```

Use FCCAnalyses `runBatch` to submit one Condor job per selected chunk:

```bash
scripts/run_lbgamma_physics_1m.sh stage1 --run --executor condor --chunks 0,1
```

The Stage 1 output goes to
`/eos/lhcb/lbdt3/user/rquaglia/fcc_ee/lblgamma/outputs/stage1_v5_lbgamma_physics_1m_20261006/`;
local-mode output defaults to `/tmp/rquaglia/fccee_lblgamma_study/stage1_v5_lbgamma_physics_1m_20261006/`. Each
chunk is reconstructed independently, so a partial campaign has an explicit
set of generated and reconstructed chunk IDs. The candidate builder still
uses reconstructed objects only and attaches truth labels after building.

## Before production

Run the existing 200-event HELAMP audit with a separate pilot seed/output if
the EvtGen decay file, generator card, or Delphes card has changed. For this
named scenario, retain the 10 chunk logs, exact card and decay hashes, output
ROOT entry checks, both charge-sign counts, direct-chain audit, v5
reconstruction config hash, FCCAnalyses revision, and per-chunk Stage 1
candidate counts. Validate each Stage 0 chunk before reconstructing it; do not
infer a million-event efficiency from only the selected chunk IDs.

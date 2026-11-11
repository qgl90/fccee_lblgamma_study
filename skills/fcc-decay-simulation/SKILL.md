---
name: fcc-decay-simulation
description: Define and validate a named EvtGen decay and Delphes EDM4hep input for this FCC-ee Lambda-b study, including a new PHSP or amplitude scenario. Use for Stage 0 generation work, not for offline selection or a detector response reinterpretation.
---

# Stage 0 decay simulation

Read `docs/agents/DECAY_STUDY_WORKFLOW.md`, `howto/delphes_production.md`,
`README_GEN.md`, and the relevant Stage 0 review before changing a card or
decay file. Work from the repository root.

1. Name the decay and model scenario. Keep PHSP, a theory amplitude model, and
   a detector-card variant separate. Record the source and assumptions for
   HELAMP magnitudes, phases, charge conjugation, and any forced probabilities.
2. Create the `.dec` file and register its sample name in the actual generator
   entry points (`scripts/produce_chunk.sh`, `config/config.yaml`, and the
   Snakemake/Condor queue only if that production path is requested). Use a new
   seed range and output name so existing files cannot be silently reused.
3. Run a distinct bounded pilot. Verify the log and exact ROOT `events` count;
   use `audit_generated_forced_chain.py` to count complete direct chains and
   both signs. For a spin model, compare generated `cos θp` with its stated
   prediction and show the raw counts. Record card/decay hashes and the
   generation stack. A valid pilot does not prove the physics model.
4. Run the requested production count only after the pilot passes. Keep chunk
   seeds, merge checks, and final input paths in the scenario manifest. Hand
   the frozen EDM4hep files to Stage 1 without using forced counts as an
   inclusive Z→bb normalization.

Changing the Delphes card creates a new detector scenario and requires a new
response and reconstruction comparison. Do not represent a post-hoc weight as
regenerated detector output when the changed parameter enters reconstruction.

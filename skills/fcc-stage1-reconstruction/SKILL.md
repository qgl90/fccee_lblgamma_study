---
name: fcc-stage1-reconstruction
description: Run and validate the Lambda-b to Lambda gamma Stage 1 v3 candidate builder on a new forced decay or inclusive Z-flavour sample in this repository. Use when producing ROOT candidate tuples and their provenance, not for Delphes generation or BDT cuts.
---

# Stage 1 v3 reconstruction

Read `docs/agents/DECAY_STUDY_WORKFLOW.md`, `howto/stage1.md`, and
`studies/reconstruction/README.md`. Confirm the Stage 0 input and its card,
decay, seeds, event count, and validation before a new full run.

Use the current one-photon builder and the named v3 selection and observable
configs for a baseline comparison. Eta and pi0 feed-down inputs use the same
one-photon reconstruction as gamma. Keep a distinct trial path for at most
1,000 input events; a full run uses the PI-requested size. New Stage 1 run
directories and ROOT basenames both include `v3`. Record the exact command,
input and output, repository and FCCAnalyses revisions, config hashes, event
limit, and any local edits.

Validate ROOT counters and candidate-vector lengths with
`verify_stage1_v3_outputs.py`, then flatten to one row
per candidate with `source_id`, `event_entry`, `candidate_slot`, and
`candidates_in_event`. Count input events, candidate-bearing output events,
candidate rows, direct truth matches, and wrong combinations separately.
Truth and ancestry are evaluation labels attached after reco candidate
building. For Condor, catalog all present chunks, reject invalid or changed
records, and freeze a new catalog for each downstream comparison. A partial
catalog contributes only its own processed-event denominator.

Compare a changed Stage 1 scenario to the unchanged baseline on the same
input events and present the difference to the PI before promoting it.

## v4 photon-pointing extension

For the PI-requested v4 reprocessing, use the opt-in v4 entry points and
`howto/stage1_v4_photon_pointing.md`. This is a tuple-schema extension of the
v3 selection. Keep v3 outputs and use distinct v4 campaigns. Attach true
photon momentum/vertex and geometric projections after candidate building;
keep stochastic detector hypotheses offline. Validate unchanged common
branches on the same bounded input and retain the fields through Stage 2
and frozen BDT scoring. Do not infer Zss rejection from the signal pilot.

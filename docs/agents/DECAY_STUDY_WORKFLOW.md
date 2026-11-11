# Agent workflow for a decay study

The PI states the physics question and decides whether a decay model, detector
scenario, or selection becomes a reference. An agent carries out the smallest
reproducible comparison and records the evidence at each gate. Read
`docs/ANALYSIS_WORKFLOW.md`, `howto/delphes_production.md`, `howto/stage1.md`,
and `howto/stage2.md` for the commands used by the current implementation.

## Start a named study

Create a distinct study tag and an output directory before running jobs. State
the requested decay, charge conjugate, physics model (PHSP or named HELAMP
scenario), detector card, reconstruction version, unchanged comparison sample,
and the question for the PI. Record repository and FCCAnalyses revisions plus
local edits. A `study_manifest.json` beside the outputs should contain the
exact input paths, their hashes or central production IDs, card/config and
decay-file hashes, seeds, commands, event limits, software revisions, outputs,
and validation files. Keep one manifest for each named scenario; append a new
snapshot record instead of changing the meaning of an old output.

## Stage 0 — EvtGen and Delphes

Use `skills/fcc-decay-simulation/SKILL.md`. Keep the decay file, generator
card, Delphes card, and EDM4hep mapping as separate provenance fields. Create
or modify a `.dec` file under a new scenario name. Record the source of any
amplitude, phase, or branching assumption. Check EvtGen syntax and produce a
bounded pilot with a distinct seed and output name. Validate the ROOT entry
count, direct ancestry chain, both charge signs, and generated-angle behavior
where a spin model is used. Keep PHSP and theory-model samples distinct.
Only then run the requested production count and freeze its input and logs.

**Handoff:** immutable EDM4hep paths, generator scenario, seed list, processed
events, complete direct decay counts by charge, card/decay hashes, and pilot
validation JSON. Forced-decay counts are conditional samples, not physical
Z→bb yields.

## Stage 1 v3 — candidate reconstruction

Use `skills/fcc-stage1-reconstruction/SKILL.md` and the current v3 config
`config/lb_reco_preselection_15mev_45_65_3d.json` with
`config/lb_observables.json`. Run the same one-photon builder on γ, η, and π⁰
samples when studying partial reconstruction. Candidate building uses reco
objects only; truth and ancestry are attached afterward. For a development
trial use at most 1,000 input events and a distinct name. A full run requires
the PI's requested event count and a frozen Stage 0 input.

**Handoff:** full paths and names containing `stage1_v3`, exact input and
config/revision, command and event limit, ROOT counters, branch/schema check,
candidate-bearing output events, candidate rows, direct matches and wrong
combinations, and one-row-per-candidate table with source/event/slot keys.
`event_entry` alone is local to its output and is not a cross-production ID.
For native Condor output, freeze a catalog of valid chunks and use its summed
processed-event count as the denominator. Do not call a partial catalog a
complete 1,200-job campaign.
Use FCCAnalyses/RDataFrame for ROOT reconstruction, with an explicit per-job
CPU count. Keep each Condor chunk independent so a failed job can be retried
without changing earlier outputs.

## Stage 2 — offline comparison and model

Start from a frozen Stage 1 v3 catalog and the unchanged reference selection.
Preserve all candidate rows in the audit; the selected table may be smaller.
Prepare independent Parquet shards by chunk with bounded parallel workers,
then verify their preparation identities and rebuild a combined cutflow.
Compare direct signal, signal wrong combinations, forced η/π⁰ feed-down, and
nonmatched inclusive Z→bb separately. Give input-event, candidate-bearing
event, and candidate denominators. For a BDT, split by generated event for
forced samples and by whole chunk for inclusive Z→bb; keep mass, helicity
angle, truth and ancestry out of training features. Freeze the model and score
choice before evaluating a held-out test partition. Record MC intervals in
sparse tails and inspect mass/angle sculpting.

**PI gate:** write a short review note with the question, exact paired
comparison, counts and conditional/cumulative efficiencies, observed effect,
limitations, and proposed next step. The PI decides whether the named
scenario becomes a reference. Preserve the prior baseline and output files.
When a command, scenario, or result changes, update its copyable `howto/`
section and study index in the same repository change. For a PI discussion,
use the [presentation workflow](PRESENTATION_WORKFLOW.md) to assemble a
Beamer deck from the frozen plots and review note.

## Operational rules

- Resume only after checking scenario identity and that every earlier catalog
  record is unchanged. Put every catalog and model snapshot under a distinct
  name. Rebuild summaries from candidate tables after interrupted work.
- Label v3 at both the run directory and new Stage 1 ROOT basename. Existing
  `stage1_v3_my_run/*.root` basenames without `_v3` remain historical paths;
  their full path and manifest define the scenario. Do not rename inputs used
  by a prepared Stage 2 identity.
- Archive a run only after its manifest, logs, validation JSON, and PI note
  point to durable outputs. Identify obsolete code by checking entry points,
  references, and artifacts before proposing removal.
- Reuse the current v3 `v3_plot_style.py` for new reconstruction/BDT plots and
  existing shared plotting and sample I/O helpers where their contracts fit.
  Factor repeated loaders or histogram definitions into a shared helper only
  after two studies demonstrate the same semantics and units; record a paired
  output comparison before replacing an established plot.

# Analysis agent working agreement

The PI steers the physics questions. Make each study step reproducible and easy
to inspect before drawing a physics conclusion. Read
`docs/ANALYSIS_WORKFLOW.md` and the relevant stage README before changing a
selection, detector card, or interpretation.

## Working rules

- Keep generation, detector response, reconstruction, truth labelling, and
  offline plots as separate stages. Record the exact input, card/config,
  FCCAnalyses revision, command, event limit, and output for each comparison.
- Use at most 1,000 events for development and validation runs unless the PI
  explicitly requests a larger run. Give trial outputs distinct names.
- Build reconstructed candidates without MC identity. Attach truth and ancestry
  only after candidate building; never use truth fields as an input selection
  when estimating observable signal efficiency or background.
- Include both charge conjugates. Count generated decays, input events, and
  candidates separately. State the denominator of every efficiency and show
  conditional as well as cumulative losses where a cutflow is relevant.
- Compare any new selection to the unchanged baseline on the same events.
  Report true signal, wrong combinations, and the relevant background sample
  separately. Forced signal/eta sample counts are not a physical Z→bb yield.
- Keep one candidate per row in downstream tables, with `event_entry`,
  `candidate_slot`, and `candidates_in_event`; preserve unselected candidates
  in diagnostic outputs when measuring a new cut.
- Treat card changes, PV/SV-resolution assumptions, and photon vetoes as named
  scenarios. Record provenance and rerun the same response and reconstruction
  checks. Do not present a reweighted plot as if it were a regenerated Delphes
  sample when the changed quantity enters reconstruction upstream.
- Write a short review note for the PI at each physics decision: question,
  assumption, exact comparison, event counts, observed effect, limitation, and
  proposed next step. The PI decides whether a change becomes the reference
  selection or detector scenario.

The stage gates, current choices, historical questions, and extension contracts
are detailed in `docs/ANALYSIS_WORKFLOW.md`.

For a request to study a new decay, follow
`docs/agents/DECAY_STUDY_WORKFLOW.md` from the named generator scenario through
the Stage 1 and offline handoffs. Use the repository skills
`skills/fcc-decay-simulation/SKILL.md` for EvtGen/Delphes work and
`skills/fcc-stage1-reconstruction/SKILL.md` for a new Stage 1 sample. Current
v3 and historical study artifacts are indexed in `docs/agents/STUDY_INDEX.md`.
The current BDT and future background-mixture gates are in
`docs/agents/BDT_ITERATIONS.md`.
For PI review decks, use `skills/fcc-study-presentation/SKILL.md` and
`docs/agents/PRESENTATION_WORKFLOW.md`; figures and numerical statements must
resolve to frozen study outputs and the matching `howto/` command.
Do not relabel an older tuple as v3; record the actual reconstruction scenario
in each run manifest. A v3 output path and future basename must both identify
v3, while a Stage 0 EDM4hep input is labelled by its generator scenario.

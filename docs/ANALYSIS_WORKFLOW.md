# PI-reviewed Λb→Λ⁰γ analysis workflow

This is the working map for an agent-assisted FCC-ee Z-pole analysis. The PI
sets the physics objective and reviews the evidence at each decision. An agent
implements and tests the smallest useful step, records its inputs and outputs,
and proposes the next comparison. A review note should make it possible to
accept, reject, or revise a choice without rerunning unrelated stages.

## How the study reached the current reconstruction

| PI question or correction | Why it mattered | Current answer and evidence |
|---|---|---|
| Which FCCAnalyses branch, environment, and generator cards are used? | An EDM4hep or vertexing API mismatch invalidates a run; an unrecorded card changes detector response. | `pre-edm4hep1` at `91c7d6c5a5c8ad5c3848d6d7cf8383e93c9b74e3`; generator and analysis use distinct Key4hep stacks. See the root README, `README_GEN.md`, and `outputs/build/fccanalyses_revision.txt` when present. |
| Can generation be run through Snakemake and plain Bash? | Production must be inspectable and reproducible without a workflow engine. | `Snakefile` and `scripts/produce_*.sh` make separate Λb→Λ⁰γ and Λb→Λ⁰η samples with forced EvtGen decays. Sample normalization is not a branching-ratio prediction. |
| What response does the IDEA card give charged tracks, displaced daughters, and photons? | Acceptance and momentum/energy response set the ceiling for reconstruction. | `analysis/studies/resolutions.py` and `displaced_daughters.py` write generated and matched objects; `studies/resolutions/` uses uproot/awkward. Residuals are `(reco−true)/true`; percent plots multiply by 100. Use signed η and production Rxy, and show the underlying distributions. |
| Where does the ECAL curve come from; why is there a photon threshold? | A reference curve and an efficiency gate describe different parts of the response. | The active `cards/card_IDEA.tcl` ECAL term is `sqrt((0.005 E)^2+(0.03 sqrt(E))^2+0.002^2)` for `|η|≤3`. `PhotonEfficiency` sets its own selected-container threshold. See `analysis/studies/README.md`; inspect the exact card version before comparing variants. |
| Can the first candidate builder be unselected, then use a tunable Λ⁰ window and both pπ hypotheses? | A raw mass peak tests object assembly; the mass hypothesis changes the Λb tail. | The baseline keeps all type-22 photons. The configured builder fits each opposite-charge pair once, tests both fitted-momentum mass hypotheses in 0.7–1.3 GeV, and retains the one closest **in absolute mass difference** to 1.115683 GeV. |
| Is the vertex built like FCCAnalyses examples, and are fitted momenta used? | A truth vertex or prefit momenta would misstate mass and displacement performance. | The PV uses `get_PrimaryTracks` and `VertexFitter_Tk(1,...)`; the Λ⁰ pair uses `VertexFitter_Tk(2,...)`. The builder uses `updated_track_momentum_at_vertex`; truth is joined later. See `studies/reconstruction/README.md`. |
| What happens with Λb→Λ⁰η(γγ) under the **one-photon** signal reconstruction? | A missing photon makes a partially reconstructed background shape. | Run the same `lb2lambda_gamma_reco.py` on the eta sample. The separate two-photon eta builder is only a diagnostic. Forced-sample counts cannot determine physical S/B. |
| Does the thrust hemisphere help, and is the 4.9–6.3 GeV interval enforced? | The signal Λ⁰ and γ should usually share a hemisphere; combinatorics can be reduced. | The selected builder requires positive product of their thrust-axis cosines and retains candidates only in the configured Λb mass interval. A no-hemisphere config is kept for a paired comparison. |
| Why is efficiency near 53%, rather than roughly twice that? | A missing charge-conjugate chain or a harsh selection would change the physics interpretation. | Both Λb and anti-Λb are included: 262/500 and 273/501 selected direct decays. The dominant losses are usable charged tracks (210/1,001) and true-pair SV χ²≤9 (145/691 entering). See `signal_loss_audit.json` and the reconstruction README. |
| What is cos θp, and does reconstruction or selection distort it? | This is the angular fit observable alongside Λb mass; its acceptance must be measured on generated phase space and charge conjugates retained. | The builder and truth labeler now store the helicity angle, `lb_sign`, and a 1,000-event PHSP acceptance/resolution diagnostic. See the reconstruction README and `study_cos_theta_p.py`. |

These entries describe what has been checked, not a claim that the current cuts
are optimal. In particular, the 1,000-event signal and eta studies are shape
and efficiency diagnostics, not an inclusive Z→bb background measurement.

## Stage boundaries and review gates

| Stage | Inputs and code | Review evidence before changing the reference |
|---|---|---|
| 0. Provenance | `config/config.yaml`, `cards/`, `evtgen/`, local FCCAnalyses revision | Card and decay-file checksums or immutable copies, environment/revision record, event count, seed list. |
| 1. Generation | `Snakefile` or `scripts/produce_*.sh` | Event count, direct decay-chain content, both charge signs, independent seeds. Do not infer physical rates from forced decays. |
| 2. Detector response | `analysis/studies/resolutions.py`, `displaced_daughters.py`; `studies/resolutions/` | Generated denominator; match and selected-container efficiencies versus truth pT, signed η and production Rxy; residual distributions and fitted widths with units. |
| 3. Candidate reconstruction | `lb_candidate_builder.h`, `lb_event_selection.h`, `lb2lambda_gamma_reco.py`, `config/lb_reco.json` | Same 1,000 events under baseline and variant; Λ⁰ and Λb masses, vertex and thrust diagnostics, candidate multiplicity, charge-separated cutflow. No MC inputs to the builder. |
| 4. Truth annotation and tables | `lb_candidate_truth.h`, `flatten_candidates.py` | Unique association rule, signed parent/grandparent PDGs, wrong-hypothesis and fake categories, one row per candidate plus event identity. Truth fields are labels, not cuts. |
| 5. Background and inference | same reconstruction on eta and eventually inclusive central Z→bb files | Per-event and per-candidate counts, sample normalization, branching fractions, mass-window definition, selection-efficiency uncertainty, and validation/control distributions. |

Keep a named baseline and a changed scenario side by side. At each gate give
the PI the exact command, config/card diff, input list, number of events,
plots/tables, signal retained, background retained, and an interpretation with
its limits. A proposed cut becomes a reference choice only after that review.

### Current inclusive Zbb Stage 1 input check

The v3 native Condor campaign is a separate reconstruction scenario from the
older `native_batch` Zbb outputs. The latest frozen 2026-10-03 catalog of
`native_batch_3d_activity_v3` checks 1,028 of 1,200 submitted chunks: all 1,028
pass ROOT counter and branch/type checks and share one schema. They cover
376,723,929 processed input events and contain 4,710,435 candidate-bearing
output events. The earlier 629-chunk snapshot is documented in
[the Stage 1 Zbb review](STAGE1_ZBB_CATALOG_REVIEW_2026-10-03.md); 172 jobs
still have no ROOT output in the current snapshot. Its frozen path is in
[the study index](agents/STUDY_INDEX.md). These are input-event and
candidate-bearing-event counts, not candidate counts or a final inclusive
background yield. Refresh and freeze a new catalog before each downstream
comparison; the reproducible check is in [howto/stage1.md](../howto/stage1.md).

The fixed 1,028-chunk v3 BDT scan is reviewed in
[the Stage 2 note](STAGE2_V3_BDT_REVIEW_2026-10-03.md). A separate
[post-BDT Armenteros review](STAGE2_V3_ARMENTEROS_REVIEW_2026-10-03.md)
uses truth ancestry to diagnose K⁰S pair contamination and evaluates a
reconstructed-only veto after the same fixed score. Both cuts remain
proposals for PI review.

## Current data and code contracts

- Generator truth and `MCRecoAssociations` are used to evaluate acceptance,
  efficiency, and ancestry. Reconstructed candidate construction uses only
  reconstructed particles, tracks, fitted PV/SV, selected photons, and thrust.
- The configured C++ builder fits an opposite-sign track pair once, considers
  p⁺π⁻ and p̄⁻π⁺, and records PV/SV positions and significances in mm. It
  chooses the valid mass hypothesis with the smallest absolute distance to the
  Λ⁰ mass. It then combines that Λ⁰ with each selected photon. The truth
  module records whether that assignment and full decay ancestry are correct.
- The current `reconstructible` audit means unique MC↔reco links to both usable
  charged tracks and one type-22 photon. It includes detector acceptance and
  reconstruction. It is **not** a pure generated-geometry acceptance. The
  cumulative cutflow follows the implemented order: object availability,
  selected photon, PV and Λ⁰ builder, then Λb mass and hemisphere. Conditional
  loss at each step has the preceding step as its denominator.
- The configured photon collection is `Photon#0.index`. A type-22 reconstructed
  photon that fails this collection is a distinct loss from having no type-22
  match. The eta-as-gamma study deliberately uses this same collection.
- The ROOT `events` tree stores vector candidate branches. The flattened
  Parquet table stores `event_entry`, `candidate_slot`, and
  `candidates_in_event`; these distinguish candidate and event denominators.
  An event with two direct decays or multiple reconstructed combinations must
  not silently become two independent events in a yield calculation.
- The mass–angle fit variables are `lb_mass`, `lb_cos_theta_p`, and `lb_sign`
  (`+1` for the Λb hypothesis, `-1` for the anti-Λb hypothesis). The truth angle uses generated Λb, Λ⁰,
  and (anti)proton four-vectors only after full ancestry matching. The angle
  follows the [LHCb Λb→Λγ definition](https://arxiv.org/pdf/2111.10194):
  (anti)proton versus negative parent momentum in the Λ rest frame. The PHSP
  sample supplies an acceptance denominator, not the later physics model.
- Stage-1 now stores candidate-level isolation, π⁰-partner, daughter-removed
  ROE thrust/recoil, and PV/SV pointing diagnostics. No isolation, recoil,
  pointing, or π⁰/η veto cut is enabled. Full global-event models,
  alternative detector scenarios, and a statistically supported inclusive
  Z→bb yield remain future stages. A first physically scaled but MC-limited
  mass–angle projection at four plotting-side stages is described in
  `studies/reconstruction/STAGE1_OBSERVABLES.md`.

## Extension contracts

### Mass–angle acceptance and expected yields

Keep PHSP and the later PI-supplied physics decay file as separate named
generator scenarios with their EvtGen text and seeds recorded. Measure
generated and selected cos θp by Λb charge, compare reconstructed and true
angles, and build a migration matrix if bin crossing matters. Model signal
acceptance versus generated angle from PHSP, then validate the product of
physics shape and acceptance against the physics MC. The η→γγ sample must be
reconstructed as one-photon signal for the partial-background mass–angle
shape; its true partial ancestry and unrelated combinations should be shown
separately. Inclusive Z→bb supplies combinatorial background. Only after
sample counts, production fractions, branching fractions, and efficiencies
are established can the forced samples be turned into expected yields. Keep
charge-conjugate angular conventions explicit in any combined fit.

### Z-pole event information

Add an event-feature producer that reads the full reconstructed event and
returns a compact record before candidate flattening. Keep candidate building
independent of it initially. Candidate rows can receive copied event features
using `event_entry`, while an event table preserves one row per collision.
Candidate-bearing hemisphere, opposite-hemisphere flavour/tag activity,
visible energy, missing momentum, thrust, and charged/neutral multiplicities
are useful *study candidates*. Their definitions, treatment of the signal
daughters, and effect on signal and inclusive Z→bb must be reviewed before
using them as selection or BDT features. Split train/test by event and, where
needed, by production file or seed so candidates from one event cannot leak
across partitions.

### Alternative calorimeter and vertex assumptions

Make a named detector-scenario manifest with a parent card, exact parameter
changes, source/rationale, output card path, checksum, generation seed, and
EDM4hep output. Start with one isolated change per scenario, for example an
ECAL energy term, photon efficiency, tracker response, or PV/SV assumption.
Inspect proposed FCC-ee calorimeter options and their authoritative parameter
sources before encoding values. Preserve the original `card_IDEA.tcl` and
regenerate the detector output for changes upstream of reconstruction.

The current PV/SV positions and covariances come from FCCAnalyses fits to
Delphes tracks. A vertex-resolution variant needs an explicit model of which
track parameters, beam spot, covariance, and correlations change. A post-hoc
shift of a plotted vertex significance is not equivalent to refitting tracks.
For each scenario rerun the same response audit and reconstruction, and report
the baseline-versus-variant change in acceptance, mass/vertex response,
signal efficiency, and background retention. Keep the card and analysis
selection config as separate provenance fields.

### π⁰ and η veto for the selected photon

For each selected Λb→Λ⁰γ candidate, combine **its photon** with every other
eligible reconstructed photon in the event, excluding the same object index.
Store the minimum `|m(γγ)−m(π⁰)|` and `|m(γγ)−m(η)|`, the partner indices and
energies, and counts inside configurable mass windows. Store these variables
before cutting, including an explicit no-partner state. Test all-photon and
selected-container partner definitions separately: the latter may hide a
low-energy second photon. Then scan veto windows on direct signal, forced
Λb→Λ⁰η reconstructed as one photon, and inclusive Z→bb. A veto is useful
only after its signal loss and background rejection are measured on the same
events. Keep MC ancestry as an evaluation label, never a veto input.

## Review note template

1. **Question and decision sought:** one physics choice, with reference and
   changed scenario named.
2. **Provenance:** FCCAnalyses commit/local edits, generator and analysis
   environments, card/config checksums, input files/seeds, exact commands.
3. **Definitions:** generated decay, reconstructible object, candidate, event,
   matching rule, denominator, units, truth-only diagnostics.
4. **Evidence:** staged counts and conditional efficiencies, distributions
   beneath resolution fits, signal/background comparison, statistical limits.
5. **Recommendation for PI review:** keep, reject, or test further; record the
   PI's decision and the next named scenario without overwriting the baseline.

### v4 photon-pointing tuple extension

The PI requested a new Stage 1 campaign carrying the inputs for offline
pointing hypotheses. This preserves the v3 candidate selection and attaches
truth/geometry diagnostics afterward. Follow
[the v4 handoff](../howto/stage1_v4_photon_pointing.md) and
[paired validation](STAGE1_V4_POINTING_REVIEW_2026-10-05.md).
Detector-hypothesis scans remain a separate offline stage; adopting a cut
requires signal acceptance and separately normalized Zbb/Zcc/Zss studies.

### v5 event-jet flavour-tagging extension

The v5 Stage 1 study starts from the v4 candidate selection and adds Weaver
scores for two exclusive event jets. It applies the existing training energy
gate before truth annotation and tagger inference. The first iteration uses a
reconstructed PV for tagger impact-parameter features, stores per-jet outputs
and candidate-aligned nearest-jet/other-jet scores, and does not apply a tag
cut. The pretrained model's PV input differs from its published training
setup, so its score calibration must be validated. Candidate daughters are not
yet removed before clustering. See
[the v5 handoff](../howto/stage1_v5_flavour_tagging.md); only a paired,
normalized signal/Zbb/Zcc/Zss study can motivate a later rejection scenario.
The 1,000-event signal pilot and Condor check-only inventory are recorded in
the [v5 pilot review](STAGE1_V5_FLAVTAG_SIGNAL_PILOT_2026-10-05.md); exact
saved FT branch names and meanings are in the
[v5 variable dictionary](STAGE1_V5_FLAVTAG_VARIABLES.md).
The six-file Zbb/Zcc/Zss opposite-jet pilot is documented in
[the v5 Z-flavour review](STAGE1_V5_ZFLAVOUR_PILOT_2026-10-06.md); it observed
zero of 36 selected Zss events passing a trial B-score threshold, which is too
small a denominator to establish the inclusive rejection.

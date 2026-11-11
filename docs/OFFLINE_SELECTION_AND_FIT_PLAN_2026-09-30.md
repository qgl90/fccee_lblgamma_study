# Offline selection and mass-fit preparation plan (30 September 2026)

## Question and current reference

Can reconstructed diphoton, photon-isolation, and Lambda-displacement
observables improve the nominal Lambda_b -> Lambda0 gamma selection without
unacceptable loss of true signal or distortion of the mass and helicity-angle
distributions? The reference is the existing `config/lb_reco_preselection_15mev_45_65.json`
reconstruction on the **same input events**. It applies the fitted Lambda0
mass window of +/-15 MeV, 4.5-6.5 GeV Lambda-gamma mass, existing vertex and
displacement cuts, and same-thrust-hemisphere requirement. No additional
offline veto or isolation cut is reference-approved.

The pinned FCCAnalyses revision recorded by the 100k run is
`91c7d6c5a5c8ad5c3848d6d7cf8383e93c9b74e3` (`pre-edm4hep1`). Before
comparing new outputs, verify the exact runtime code and config against the
100k run manifest: the current checkout has uncommitted reconstruction and
Condor changes. Preserve these existing changes and use new output names.

## Inputs already available

The EOS output root is
`/eos/lhcb/lbdt3/user/rquaglia/fcc_ee/lblgamma/outputs`. Its
`nominal_preselection_100k_run_manifest.json` gives input hashes, commands,
and the candidate-table hashes. These are forced-decay samples with 100,000
input events **each**, reconstructed with the one-photon Gamma builder:

| Mode | Candidate rows | Reference truth category | Category rows |
|---|---:|---|---:|
| `signal_phsp` | 60,424 | Direct fully matched Lambda_b -> Lambda0 gamma | 55,293 |
| `signal_physics` | 60,593 | Direct fully matched Lambda_b -> Lambda0 gamma | 55,393 |
| `lbgamma_eta` | 44,930 | Matched Lambda_b -> Lambda0 eta, eta -> gamma gamma, reconstructed with one gamma | 39,772 |

The remaining rows in each forced sample are wrong or unmatched combinations.
Keep them as a separate category. The candidate table stores `source_id`,
`event_entry`, `candidate_slot`, and `candidates_in_event`. Count distinct
events separately from candidate rows. Check the direct generated-decay and
charge-sign counts from generator truth before quoting decay efficiency;
100,000 input events must not silently become a 100,000-decay denominator.

The EOS directory has native FCCAnalyses Z->bb ROOT chunks under
`zbb_full_condor/native_batch/p8_ee_Zbb_ecm91/`. The submission covers 4,398 central Winter2023 IDEA
input files in 1,200 chunks. This is an **incomplete snapshot**, not a
complete background denominator. The historical first-file 100k scan has
982 candidates in 816 events after an older **4.9-6.3 GeV** Lambda-gamma
reconstruction and offline +/-15 MeV Lambda window; it is superseded for active background
comparisons by the Condor chunks. Before
using native chunks, establish each chunk's exact source-file list, processed
input-event count, successful completion, schema, and uniqueness; flatten with
stable source and event identifiers. Do not extrapolate from the number of
candidate-bearing output entries.
The generated native job scripts under
`external/FCCAnalyses/BatchOutputs/2026-09-30_18-23-32/p8_ee_Zbb_ecm91/`
record the input paths for each `chunk_N.root`. For example, chunk 112 lists
four distinct central files; its ROOT `eventsProcessed` parameter is 400,000,
whereas its filtered `events` tree contains 4,954 candidate-bearing events.
Use the chunk number as the first stable output grouping key until a checked
per-source-entry mapping exists. Split ML by whole chunks or larger source
groups, never by candidate rows from one chunk.
The first schema-checked catalogue snapshot on 1 October 2026 found 284
valid ROOT chunks with 113,274,120 processed central events and 1,413,475
candidate-bearing output events; 916 jobs were still absent. All 284 shared
one ROOT branch/type signature. The snapshot is saved as
`outputs/analysis/studies/condor_zbb_chunk_catalog_schema_20261001.json`.
The completed offline audit of that partial snapshot, including the raw-pair
candidate cutflow and finite-MC interval, is reviewed in
`docs/CONDOR_ZBB_OFFLINE_REVIEW_2026-10-01.md`.

## Step 1: freeze a reproducible offline input manifest

Record absolute ROOT/Parquet paths, SHA256, source IDs, input events, ROOT
`eventsProcessed` counts where available, card/config hashes, software
revision, and exact flattening command. Verify the 100k candidate schemas and
the stage-1 counts above. Use a distinct trial directory for a <=1,000-event
development slice from each sample. Preserve every baseline candidate row in
the diagnostic table; add boolean stage flags instead of dropping failed rows.
For a production cutflow, use the full already-produced 100k tables only after
the trial validates schema and candidate identity.

## Step 2: compare named reconstructed-observable scenarios

Calculate flags solely from reconstructed columns. Start with these independent
scenarios, then evaluate their combinations in a fixed order:

1. Same-hemisphere selected-photon pi0 veto at +/-20 MeV, eta veto at +/-50
   MeV, and their combination, using **all** eligible pair masses. A missing
   partner passes and is counted as its own category. Keep the previous 100k
   scan as a cross-check: combined veto kept 55,202/55,293 PHSP matches,
   55,301/55,393 physics matches, 26,917/39,772 matched eta feed-down, and
   812/982 first-file Z->bb candidates. These figures use candidate
   denominators and have no physical yield normalization.
2. An all-raw-type-22-photon variant using
   `gamma_combo_other_gamma_mass`, separately from the selected-container
   same-hemisphere variant. The former includes photons outside `Photon#0`
   and both hemispheres, so its rate and interpretation must be reported
   separately. Do not use `m_gg_best` alone for the eta veto: it retains only
   the partner closest to pi0.
3. The proposed 1.5 GeV diphoton-energy rule, once its observable and pass
   direction are fixed. The current pair-mass/index lists do **not** contain
   every partner energy, so either compute the requested energy from the
   source EDM4hep event with an unambiguous join or persist it in a new
   reconstruction diagnostic. Do not substitute `E_gamma2`: that is only
   the partner closest to pi0. Compare this rule both alone and with the
   mass vetoes. Existing Condor ROOT chunks persist the raw all-type-22 pair
   masses/indices, but not the complete selected same-hemisphere pair list.
   A same-definition Z->bb comparison requires an unambiguous join to its
   original EDM4hep events or a new, versioned reconstruction output; do not
   substitute the raw-list veto under the selected-list label.
4. Photon isolation (`iso_R03_noLambda`, `iso_R05_noLambda`) and Lambda0
   displacement (`lambda_d0_sig`, flight distance/significance) as scans with
   thresholds learned on a development partition and evaluated on a separate
   partition. The baseline already cuts flight Rxy >=0.3 mm and significance
   >=2; those flags should reproduce 100% retention on the candidate table.
   `lambda_pv_cos` is geometry relative to the PV, not a justified Lambda_b
   pointing cut. The photon-ray proxies do not measure a photon vertex.

For every stage and sample report baseline, passing, and failing **candidate
and distinct-event** counts; conditional and cumulative retention; true
signal, wrong forced-signal combinations, matched eta feed-down, wrong eta
combinations, and inclusive Z->bb separately. Show both charge signs, mass
and cos(theta_p) before/after, and efficiency versus generated angle in PHSP
with physics-MC validation. Candidate multiplicity requires an explicit final
one-candidate-per-event policy before a fit or yield estimate.

## Step 3: prepare truth-labelled model samples

Use PHSP direct full matches for binary training and inclusive central Z->bb
for background; retain forced wrong combinations and eta feed-down for
independent evaluation. Keep the 100k physics HELAMP sample entirely out of
training for angular-model validation. Build candidates and cut flags before
attaching truth labels. Model inputs must exclude `lb_mass`, `cos_theta_p`,
truth/ancestry, identifiers, and the unmeasured photon-origin proxies. Keep
pair features with an explicit no-partner value or mask. Use source-file or
production-chunk partitions for Z->bb, and event-grouped splits for forced
samples; no event may cross partitions. Freeze preprocessing, features,
splits, model, and score working points before evaluating the held-out files.

The existing `prepare_bdt_dataset.py`, `prepare_training_inputs.py`, and
`train_postlambda_bdt.py` are the starting implementation. The historical
39/41-feature BDT showed very strong separation on a million-event central
sample, but its leading `E_same` and `deltaE` variables may reflect a
forced-signal versus central-Z->bb production difference. Compare a compact
topology/isolation model with and without these global-event variables, and
check held-out mass and angular sculpting. The all-Z->bb campaign is needed
to quantify rare background tails; zero held-out survivors imply an upper
limit, never zero expected background.

## Step 4: yield envelope and fit-ready sample gate

Use the same frozen offline stages, score cuts, and 4.5-6.5 GeV fit range on
all four modes. Resolve the physical signal, Lambda0, eta, and b-baryon
production factors as explicit scenario inputs; the existing
`config/yield_projection.json` uses a Lambda_b share of one among b baryons
as an upper envelope, not a measured Lambda_b fraction. Normalize inclusive
Z->bb from **processed generated events and weights**, with statistical
uncertainty from independent held-out source files. Show the 5.4-5.9 GeV
peak interval only as a diagnostic subset of the fit range. Check sideband
shape, mass-angle correlation, charge categories, candidate multiplicity,
and signal angular acceptance before preparing a final fit table. Keep PHSP
acceptance and physics-MC validation distinct.

## PI review gates

After each step, write a short note giving the question, exact input and
command, assumptions, event/decay/candidate denominators, observed changes,
statistical limitations, and one proposed next choice. The PI decides whether
any veto, isolation threshold, BDT score, detector scenario, or fit range
becomes reference. The current nominal candidate tables and reconstruction
remain the comparison baseline throughout this study.

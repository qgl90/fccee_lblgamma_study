# PI review: inclusive Z->bb Condor preselection snapshot (1 October 2026)

## Question and scope

What is the reconstructed-candidate rate, and what fraction passes a raw
all-photon pi0 then eta veto, in the **submitted Condor Z->bb campaign**?
This is a partial-campaign offline audit, not a final selection decision or
a physical Z-pole yield. It supersedes the older one-file Z->bb pilot as the
active inclusive background input.

## Provenance and exact procedure

The native FCCAnalyses outputs are under
`/eos/lhcb/lbdt3/user/rquaglia/fcc_ee/lblgamma/outputs/zbb_full_condor/native_batch/p8_ee_Zbb_ecm91/`.
The 1,200 generated job scripts under
`external/FCCAnalyses/BatchOutputs/2026-09-30_18-23-32/p8_ee_Zbb_ecm91/`
list 4,398 unique central Winter2023 IDEA `p8_ee_Zbb_ecm91` source files.
They run `analysis/studies/analysis_preselection_zbb.py`, which delegates to
the nominal one-photon candidate builder with
`config/lb_reco_preselection_15mev_45_65.json` (current SHA256
`f1119e7e7d62b3f467c9a9ef6559e080f2b6fce7960377eddfdd861320fdfb0f`).
The pinned FCCAnalyses checkout is `pre-edm4hep1` at
`91c7d6c5a5c8ad5c3848d6d7cf8383e93c9b74e3`. The job scripts record the
input-file list and command, but do not embed an immutable per-job hash of
the analysis code/config; that provenance should be added before declaring a
final production frozen.

The code for this audit is `catalog_condor_zbb_chunks.py`,
`flatten_candidates.py`, `offline_selection_audit.py`, and
`process_condor_zbb_catalog.py` in `studies/reconstruction/`. The first
development flatten used only 1,000 candidate-bearing ROOT entries of chunk
112, then a complete chunk and three-chunk trial validated counts and keys.
The complete snapshot was reproduced with:

```bash
myenv/bin/python studies/reconstruction/catalog_condor_zbb_chunks.py \
  --job-dir external/FCCAnalyses/BatchOutputs/2026-09-30_18-23-32/p8_ee_Zbb_ecm91 \
  --root-dir /eos/lhcb/lbdt3/user/rquaglia/fcc_ee/lblgamma/outputs/zbb_full_condor/native_batch/p8_ee_Zbb_ecm91 \
  --output outputs/analysis/studies/condor_zbb_chunk_catalog_schema_20261001.json
myenv/bin/python studies/reconstruction/process_condor_zbb_catalog.py \
  --catalog outputs/analysis/studies/condor_zbb_chunk_catalog_schema_20261001.json \
  --output-dir /tmp/rquaglia/fccee_lblgamma_zbb_offline_20261001 --workers 4
```

The catalogue fixes **284** valid chunks present at its scan, covering
1,136 distinct central input files. Their ROOT `eventsProcessed` counters
sum to **113,274,120 input events**. All 284 have the same branch/type
signature; `eventsSelected` agrees with the filtered `events` tree length
in every chunk. This is a snapshot while 916 of the 1,200 jobs were absent.
The exact chunk/input map and denominators are in the catalogue JSON.

Flattening used `source_id=chunk_id`, with `event_entry` and
`candidate_slot` completing the candidate key. Every chunk's flattened
candidate-bearing event and candidate counts were checked against its ROOT
and audit summaries. The large intermediate Parquets are in `/tmp/rquaglia`
because the AFS work volume was at 99% quota; the compact, persistent result
is `outputs/analysis/studies/condor_zbb_offline_20261001/processed_catalog_summary.json`.
The exact per-chunk commands are also saved in temporary per-chunk logs.

## Definitions and effect

The nominal reconstruction already requires the fitted Lambda0 +/-15 MeV
window, 4.5-6.5 GeV Lambda-gamma mass, the configured vertex/displacement
cuts, and the Lambda-photon thrust-hemisphere condition. The offline test
forms each candidate photon's mass against **every other raw type-22
reconstructed photon in the event**. A candidate passes if no pair lies
within +/-20 MeV of pi0, followed by no pair within +/-50 MeV of eta. A
candidate without another type-22 photon passes. These flags use no MC truth.

Truth labels are attached afterward. Among all inclusive candidate rows,
205 are full direct Lambda_b -> Lambda0 gamma truth matches and are excluded
from the `inclusive_zbb_other` background count. Both charge conjugates
remain included. Counts below are sums across independent chunk IDs;
candidate-bearing event counts use `(chunk_id,event_entry)`.

| Stage | Other Z->bb candidates | Conditional candidate retention | Cumulative candidate retention | Background candidate-bearing events |
|---|---:|---:|---:|---:|
| Nominal preselection | 1,780,957 | 100% | 100% | 1,413,278 |
| Raw pi0 veto | 575,450 | 32.31% | 32.31% | 493,938 |
| Then raw eta veto | 186,314 | 32.38% | 10.46% | 165,700 |

The nominal background rate is 0.0157225 candidate combinations per
processed Z->bb input event. After both raw vetoes it is 0.00164481 per
processed event. A fixed-seed bootstrap resampling whole Condor chunks 5,000
times gives 95% **finite-MC** intervals of [0.0156946, 0.0157500] and
[0.00163604, 0.00165330] per input event, respectively. The conditional
background candidate retention interval is [10.4116%, 10.5119%]. These
intervals do not include detector, generator, selection-model, or sample
normalization uncertainty. Candidate counts can exceed event counts because
an event can contain multiple combinations.

## Comparison to forced samples and limitations

The **same raw all-type-22** combined veto retains 41,879/55,293 (75.74%)
matched PHSP signal candidates, 42,088/55,393 (75.98%) matched physics
signal candidates, and 10,672/39,772 (26.83%) matched eta feed-down
candidates in the already-produced 100k forced-sample tables. These are
conditional candidate retentions after nominal preselection; generated-decay
denominators need a separate generator audit. Forced-sample counts are not
physical Z->bb yields.

The previously studied **selected same-hemisphere** pi0/eta veto is a
different scenario. Existing native Condor chunks persist raw pair masses
and indices, but not every selected same-hemisphere pair mass and partner
energy. They cannot directly measure that scenario without joining to the
original EDM4hep files or regenerating a versioned reconstruction. The
historical one-file Z->bb table also had a narrower 4.9-6.3 GeV candidate
mass range, so its 812/982 veto retention is not an equivalent current
baseline comparison.

The full Condor production was still running at this snapshot. No mass or
cos(theta_p) shape/acceptance check has yet been made after the raw veto.
The proposed diphoton-energy requirement remains undefined pending the
specific energy observable, and per-partner energies are not stored in these
pair lists. Before a BDT or fit projection, finish the campaign catalogue,
freeze the code/config provenance and mass-fit range, validate mass/angle
sculpting and charge efficiency, and split inclusive training/test data by
whole source-file chunks. A physical yield also needs the final processed
generated-event/weight denominator and explicit Lambda_b production and
branching-fraction assumptions. The PI should review these comparisons
before adopting either veto definition.

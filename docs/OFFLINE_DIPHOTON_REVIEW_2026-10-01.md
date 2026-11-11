# PI review: offline diphoton veto definitions (1 October 2026)

## Question and decision sought

Should the nominal Lambda_b -> Lambda0 gamma candidate be vetoed when its
photon forms a pi0- or eta-like pair with another reconstructed photon? This
note compares two **diagnostic** partner definitions on the unchanged nominal
candidate rows. No cut is promoted to the reference selection.

## Provenance and exact comparison

The three forced-sample candidate tables were produced with
`config/lb_reco_preselection_15mev_45_65.json`, the IDEA detector output,
and FCCAnalyses `pre-edm4hep1` commit
`91c7d6c5a5c8ad5c3848d6d7cf8383e93c9b74e3`. The 100k reconstruction
commands, input and output hashes, and event counts are in the EOS
`nominal_preselection_100k_run_manifest.json` under
`/eos/lhcb/lbdt3/user/rquaglia/fcc_ee/lblgamma/outputs`. The later
`diphoton_*_100k_15mev_*.parquet` tables supplied pair lists. The historical
first-file Z->bb table instead came from the earlier 4.9-6.3 GeV
reconstruction followed by an offline +/-15 MeV Lambda window, so its
candidate rate is **not** comparable to the new 4.5-6.5 GeV Condor baseline.
Their input
SHA256 values are:

| Input | SHA256 |
|---|---|
| `diphoton_phsp_100k_15mev_signal.parquet` | `276a6f63ac81c9297ffe9b180ea4a3985cb718af2e9e4676d3bf66529a91c15e` |
| `diphoton_physics_100k_15mev_signal.parquet` | `d6c294cb3031e4b64c86d8dffad270d21483f431745fc7d27b563d948e471f28` |
| `diphoton_phsp_100k_15mev_eta_as_gamma.parquet` | `ea54143b9dd02ce993560e649b26ac2e5489052c3b03be6017e8ae277d59f84a` |
| `diphoton_phsp_100k_15mev_zbb.parquet` | `beb813d22f37f7eaeb8be537c4c0948895904f2e9dae2d78786342cf8e73c376` |

The exact offline command, replacing `SAMPLE`, `INPUT`, and `OUTPUT`, was:

```bash
myenv/bin/python studies/reconstruction/offline_selection_audit.py \
  --input INPUT --sample SAMPLE --max-events 0 --output-prefix OUTPUT
```

The production outputs are under
`outputs/analysis/studies/offline_selection_100k_20261001/`. Development
first used at most 1,000 **candidate-bearing output events** per forced mode
under `offline_selection_pilot_20261001/`. The Z->bb first-file table has
982 candidates in 816 such events; its pilot audit is in that directory.
The script saves every candidate with independent pass flags, nearest mass
distances, partner-availability flags, and truth diagnostic category. It
reports candidate counts, distinct `(source_id,event_entry)` counts, and
conditional/cumulative retention at each stage.
Optional `--iso-r03-nolambda-max` and `--lambda-d0-abs-sig-min` flags can
append exploratory stages; they were not enabled for the 100k counts below.
An example with 0.25 and 2.0 was checked on the first 1,000 candidate-bearing
PHSP output events only and is not a selected working point.

The selected definition pairs the candidate photon with every other
`Photon#0` photon on its same reconstructed thrust hemisphere. The raw
definition uses every other type-22 reconstructed photon in the event, with
no hemisphere condition. Both reject a candidate if **any** eligible pair
has `|m(gamma gamma)-m(pi0)| <= 20 MeV` or
`|m(gamma gamma)-m(eta)| <= 50 MeV`; no-partner candidates pass. MC truth
labels are applied only after these reconstructed-observable flags.

## Observed effect

Each forced mode has 100,000 input generated events; the direct-decay
denominator has not been independently audited in this comparison. The table
below therefore gives **candidate** retention within each truth category,
not generated-decay efficiency. The Z->bb row comes from one central 100k
input file and is not an all-campaign rate.

| Category | Nominal candidates | Selected same-hemisphere pi0 then eta | All raw type-22 pi0 then eta |
|---|---:|---:|---:|
| PHSP direct full match | 55,293 | 55,202 (99.835%) | 41,879 (75.740%) |
| PHSP wrong/unmatched combination | 5,131 | 4,626 (90.158%) | 1,824 (35.549%) |
| Physics direct full match | 55,393 | 55,301 (99.834%) | 42,088 (75.981%) |
| Physics wrong/unmatched combination | 5,200 | 4,743 (91.212%) | 1,874 (36.038%) |
| Matched eta feed-down as gamma | 39,772 | 26,917 (67.678%) | 10,672 (26.833%) |
| Eta-sample wrong/unmatched combination | 5,158 | 3,876 (75.145%) | 880 (17.061%) |
| Historical central Z->bb first-file pilot, narrower Lambda-gamma range | 982 | 812 (82.688%) | Unavailable in this older table |

For all candidates, not just the labelled categories, the selected-pair
combined veto leaves 59,828/60,424 PHSP, 60,044/60,593 physics,
30,793/44,930 eta, and 812/982 first-file Z->bb rows. The corresponding
distinct output-event counts are 56,552/56,735, 56,714/56,866,
28,933/41,956, and 699/816. The selected-pair counts exactly reproduce
the earlier 100k diphoton study, including 812/982 Z->bb candidates.

The raw definition has a partner for nearly every forced-sample candidate
because it accepts lower-threshold photons and the opposite hemisphere. Its
substantially larger signal loss is therefore expected from the changed
definition; it is not evidence that the same-hemisphere veto is unstable.

## Limitations and proposed next step

The selected same-hemisphere inclusive Z->bb comparison above uses one
historical 100k-event file and is no longer the active background input.
The Condor-based pilot and its distinct raw-pair definition are recorded
below. The full-campaign Condor ROOT chunks were still arriving during this
review and need a complete source-file and processed-event audit before
merging and flattening.
The selected-pair veto's effect on reconstructed mass, cos(theta_p), charge,
and generated-angle acceptance has not yet been checked in this new offline
cutflow. Neither forced eta counts nor forced signal counts give a physical
Z->bb yield. The proposed 1.5 GeV diphoton-energy rule also needs an exact
definition and per-partner energies; `E_gamma2` records only the partner
closest to pi0, while the stored all-pair lists contain masses and indices.

Keep both veto definitions as named diagnostic scenarios. Next, attach the
requested per-pair energy observable with a checked event join, scan it
alongside isolation and Lambda displacement on independent development and
evaluation partitions, and repeat the cutflow on properly catalogued
inclusive Z->bb chunks. Review mass and angular sculpting before any
threshold is considered for the reference selection.

## Condor background correction, 1 October 2026

The active inclusive sample is the native FCCAnalyses Condor production under
`/eos/lhcb/lbdt3/user/rquaglia/fcc_ee/lblgamma/outputs/zbb_full_condor/native_batch/p8_ee_Zbb_ecm91/`.
`catalog_condor_zbb_chunks.py` checked the 1,200 generated job scripts:
their input lists contain 4,398 unique central source files. At the recorded
snapshot, 284 ROOT chunks were present and valid, had one identical branch/type
signature, and reported 113,274,120 processed events in their ROOT
`eventsProcessed` parameters. The corresponding `events` trees contain
1,413,475 candidate-bearing output events. These are a *partial production*
total. The catalogue is
`outputs/analysis/studies/condor_zbb_chunk_catalog_schema_20261001.json`.

The first complete post-reconstruction check used Condor `chunk_112.root`.
Its generated job script lists four central source files and its ROOT file
reports 400,000 processed events and 4,954 candidate-bearing output events.
The exact commands were:

```bash
myenv/bin/python studies/reconstruction/flatten_candidates.py \
  --input /eos/lhcb/lbdt3/user/rquaglia/fcc_ee/lblgamma/outputs/zbb_full_condor/native_batch/p8_ee_Zbb_ecm91/chunk_112.root \
  --output outputs/analysis/studies/condor_zbb_pilot_20261001/chunk_112_all.parquet \
  --mode zbb --source-id 112 --chunk-events 500
myenv/bin/python studies/reconstruction/offline_selection_audit.py \
  --input outputs/analysis/studies/condor_zbb_pilot_20261001/chunk_112_all.parquet \
  --sample zbb --max-events 0 \
  --output-prefix outputs/analysis/studies/condor_zbb_pilot_20261001/chunk_112_all_rawpair_audit
```

The first trial flattened at most 1,000 candidate-bearing output events,
then the full chunk was processed. The full chunk has 6,284 candidate rows:
6,283 other inclusive combinations and **one** direct truth-matched signal
candidate, kept separate from the background label. The raw all-type-22
pi0+eta veto retains 696/6,283 other candidates (11.08% conditional to
nominal preselection) in 616/4,953 background candidate-bearing events.
It retains the one direct signal candidate. These are conditional candidate
and event retentions within one 400k-event chunk, not a full-campaign rate.

The native chunk stores `gamma_combo_other_gamma_mass` for every candidate,
but it does not store the **full** selected same-hemisphere pair list used by
the earlier historical Z->bb scan. The two veto definitions must not be
compared as though identical. The validated partial Condor snapshot has since
been flattened with `source_id=chunk_id` and evaluated with the same raw-pair
definition across all four modes. Its complete counts and limits are in
`docs/CONDOR_ZBB_OFFLINE_REVIEW_2026-10-01.md`. Reconstructing selected
same-hemisphere pairs from the original EDM4hep files still requires a
separate checked join.

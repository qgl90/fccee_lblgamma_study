# Raw pπ mass prefilter check (30 September 2026)

## Question

Can a ±50 MeV window around the PDG Λ⁰ mass, calculated from original
reconstructed track momenta under either pπ mass assignment, reject enough
track pairs before vertexing to be useful without removing too much signal?

## Scenario and provenance

- Reference: `config/lb_reco_preselection_15mev_45_65.json`.
- Test: `config/lb_reco_preselection_15mev_45_65_rawmass50.json`, identical
  selection plus `raw_mass_prefilter_half_window_gev = 0.05`.
- The gate runs after track-link, PV-membership, and daughter-d0-significance
  checks, before the two-track Λ vertex fit. It accepts the pair if either raw
  pπ assignment is within 0.05 GeV of 1.115683 GeV.
- Both runs use reconstructed quantities for construction. MC labels are
  attached afterward and used only to count matched candidates.
- FCCAnalyses checkout: `pre-edm4hep1`, commit
  `91c7d6c5a5c8ad5c3848d6d7cf8383e93c9b74e3`; Key4hep stack `2024-03-10`.
- No detector card or generation changes. Both input files are processed to
  1,000 entries with one CPU thread.

Commands:

```bash
scripts/run_reco_preselection.sh signal_phsp \
  outputs/delphes/Lb2LambdaGamma_nev500000_IDEA_edm4hep.root \
  outputs/analysis/studies/LbGamma_prefilter50_signal_baseline_1000.root \
  1000 config/lb_reco_preselection_15mev_45_65.json 1
scripts/run_reco_preselection.sh signal_phsp \
  outputs/delphes/Lb2LambdaGamma_nev500000_IDEA_edm4hep.root \
  outputs/analysis/studies/LbGamma_prefilter50_signal_rawmass50_1000.root \
  1000 config/lb_reco_preselection_15mev_45_65_rawmass50.json 1
scripts/run_reco_preselection.sh zbb \
  work/cache/winter2023_zbb/events_000083138.root \
  outputs/analysis/studies/Zbb_prefilter50_baseline_1000.root \
  1000 config/lb_reco_preselection_15mev_45_65.json 1
scripts/run_reco_preselection.sh zbb \
  work/cache/winter2023_zbb/events_000083138.root \
  outputs/analysis/studies/Zbb_prefilter50_rawmass50_1000.root \
  1000 config/lb_reco_preselection_15mev_45_65_rawmass50.json 1
```

The ROOT outputs are flattened to one row per selected candidate with
`studies/reconstruction/flatten_candidates.py`; source IDs are 0 in these
single-file tests. The Parquet files are stored beside the ROOT tests for
signal and in `/tmp` for Z→bb candidate-count comparison.

## Results

| Sample / measure | Reference | ±50 MeV raw prefilter | Change |
|---|---:|---:|---:|
| Signal selected candidate rows | 594 | 250 | −57.9% |
| Signal truth-matched candidate rows | 528 | 208 | −60.6% |
| Signal unmatched/wrong candidate rows | 66 | 42 | −36.4% |
| Z→bb selected candidate rows | 21 | 17 | −19.0% |

Each run read 1,000 input entries. Event prerequisites left 970 signal and 908
Z→bb entries in the reconstructed event tree; the candidate tables contain
only events with at least one final selected candidate.

Among events that have at least one selected candidate in **both** paired
outputs, the pair counters show:

| Common candidate-bearing events | Baseline pairs after d₀ checks | Prefilter pairs / vertex fits | Fewer fits |
|---|---:|---:|---:|
| Signal (228 events) | 3,503 | 542 | 84.5% |
| Z→bb (13 events) | 568 | 62 | 89.1% |

Every prefiltered final candidate is also present in the reference candidate
set. On signal, the prefilter removes 320 of 528 truth-matched reference
candidates and 24 of 66 unmatched/wrong candidates. The reduction in fit calls
is large, but the relative rejection is not favorable: most removed final
candidates are true matched signal. The Z→bb test retains only 21 reference
candidates, so it is too small for a reliable background-rejection estimate.

The pair-fit percentages above are computed on events with selected
candidates in both outputs, because a candidate Parquet table has no row for
events with zero candidates. They are not all-input-event totals. The ROOT
outputs contain per-event counters for a complete cutflow rerun. Counts in
this note are candidates, not generated decays or physical yields.

## Review and next step

Keep the current reference unchanged and do not enable the ±50 MeV raw mass
gate as a default. It does what it was intended to do computationally, but
the 1,000-event signal comparison shows substantial loss of correctly matched
candidates without comparable fake-candidate rejection. If reducing fit load
remains necessary, test a wider raw-mass gate on the same paired samples and
report signal efficiency against generated/reconstructible decays as well as
candidate counts. The PI should decide whether that speed/efficiency tradeoff
is acceptable before promoting a prefilter scenario.

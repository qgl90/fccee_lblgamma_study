# Stage 1 v3 Physics versus available Zbb: inspection reference

## Question and scope

Which new reconstructed activity, recoil, and daughter kinematic variables
show separation between truth-matched Λb→Λ⁰γ Physics candidates and inclusive
Zbb candidates after the established offline Λ⁰ mass window and optional
same-hemisphere π⁰ veto? This is an inspection and candidate-cut discovery
step. The PI has not adopted an additional rectangular cut.

## Frozen inputs and assumptions

- Physics: `/eos/lhcb/lbdt3/user/rquaglia/fcc_ee/lblgamma/outputs/stage1_v3_my_run/signal_physics.root`.
  Its ROOT counter records 100,000 processed generated events.
- Zbb: `outputs/analysis/studies/v3_offline_inspection_20261002/zbb_catalog_snapshot.json`;
  191 valid, schema-identical ROOT chunks from the 1,200-job Condor campaign,
  with 76,222,397 processed input events and 953,634 candidate-bearing Stage 1
  output events. The remaining jobs are excluded from this frozen snapshot.
- Offline config: `config/lb_offline_selections.json`, scenario
  `lambda5_same_hemi_all`, then optional `mass5_pi0` plotting selection.
- Stage 1 config recorded as
  `config/lb_reco_preselection_15mev_45_65_3d.json`; exact config, catalog,
  script hashes, revisions, and commands are in the generated `summary.json`
  and `manifest.json` files.
- The mass range is 4.7–6.5 GeV in m(Λγ), then
  `|m(pπ)−1.115683 GeV|≤0.005 GeV`. The optional π⁰ veto uses all other raw
  type-22 photons on the reconstructed Λ⁰ hemisphere, with a ±20 MeV π⁰
  mass window. Empty partner lists pass.

Truth is attached after candidate construction. It is used to distinguish
true Physics signal, Physics wrong combinations, and nonmatched Zbb in the
plots and scan denominators. No truth field enters these offline cuts.

## Outputs and reading guide

The no-veto mass-window reference is
`outputs/analysis/studies/v3_offline_inspection_20261002/reference_mass5/`.
It has one full-column selected Parquet and one all-candidate audit Parquet
per source. The optional-veto reference and plot pages are under
`outputs/analysis/studies/v3_offline_inspection_20261002/reference_mass5_pi0/`.
Every downstream row has `sample`, `source_id`, `event_entry`,
`candidate_slot`, and `candidates_in_event`. Compare events using the
processed-event denominators in the summaries; counts of candidate-bearing
ROOT rows or candidate rows are different quantities.

The plots normalize each category to unit candidate count separately.
`single_variable_cut_scan.csv` ranks a single lower or upper bound per
variable by Zbb candidate retention, requiring at least 99% of selected
truth-matched Physics candidates on the *same* sample. It is exploratory:
there is no independent validation set, combination of cuts, or full-campaign
Zbb estimate in this step. The scan is conditional on all earlier cuts, so it
must not be read as 99% retention relative to generated Physics decays.

## Counts and observed effect

The no-veto preparation completed on all frozen sources. Its
`reference_mass5/summary.json` records:

| Stage | Physics direct candidates | Physics wrong candidates | Physics selected events | Zbb nonmatched candidates | Zbb selected events |
|---|---:|---:|---:|---:|---:|
| Stage 1 output | 55,395 | 5,203 | 56,871 | 1,200,677 | 953,634 |
| Λb fit range | 55,395 | 4,508 | 56,711 | 979,293 | 795,332 |
| Λ⁰ ±5 MeV | 54,324 | 4,036 | 55,507 | 619,133 | 521,467 |
| Λ⁰ ±5 MeV, same-hemisphere π⁰ veto | 52,789 | 2,326 | 53,687 | 207,110 | 187,519 |

The Λ window retains 54,324/55,395 = 98.07% of the Stage 1 truth-matched
Physics candidates, and 619,133/1,200,677 = 51.57% of the nonmatched Zbb
candidates. The direct-signal candidate efficiency relative to the 100,000
generated Physics events is 54.324%; the Zbb candidate rate relative to
76,222,397 processed input events is 619,133/76,222,397. These are distinct
denominators. The optional π⁰ veto retains 52,789/54,324 = 97.17% of direct
signal candidates and 207,110/619,133 = 33.45% of nonmatched Zbb candidates,
conditional on the Λ window. It retains 53,687/55,507 = 96.72% of Physics
candidate-bearing events and 187,519/521,467 = 35.96% of Zbb
candidate-bearing events. Relative to input events, its direct-signal
candidate rate is 52,789/100,000 and its nonmatched Zbb candidate rate is
207,110/76,222,397. The optional selection has not been added to the
reference JSON.

Among the π⁰-veto survivors, 4,399/52,789 direct Physics candidates and
104/207,110 nonmatched Zbb candidates have no eligible partner photon.
They pass the veto. The finite diphoton-distance plot axes omit their `+inf`
sentinel, while the candidate Parquets preserve it.

The best one-variable candidate scan result on this same selected sample is
`lb_E ≥ 11.4517 GeV`: it retains 99.00% of direct Physics candidates and
26.14% of nonmatched Zbb candidates. This is a discovery estimate on the
same candidates used to find the bound; it is not yet a validated selection.

## PI review point

Choose a variable and bound, if any, for a named offline scenario only after
checking its signal loss relative to generated decays and its Zbb event and
candidate retention. Repeat on the completed Zbb campaign and use an
independent validation subset before interpreting a physical background
yield. The available v3 reference is intended for direct plotting and
follow-up studies; [the command guide](../howto/v3_reference_plots.md) gives
the reproducible invocation.

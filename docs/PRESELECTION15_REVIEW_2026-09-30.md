# PI review: requested Λ mass preselection pilot

## Question and assumption

Does a fitted-Λ **±15 MeV** window around 1.115683 GeV together with
4.5–6.5 GeV in reconstructed m(Λγ) retain direct Λb→Λγ while providing a
candidate table for later displacement and photon studies? “15 MeV window”
is interpreted as a half-width, consistent with the earlier ±10 MeV study.
The current working-tree `config/lb_reco.json` is the unchanged comparison;
it actually uses 4.7–6.5 GeV, while the historical BDT snapshot used
4.9–6.3 GeV. No pointing or photon veto is added.

## Exact comparison and provenance

Run `bash scripts/run_preselection_pilot.sh 1000`. It processes the first
1,000 events in each file under both configs with the same
`analysis/studies/lb2lambda_gamma_reco.py`, then flattens and applies the
offline Λ mass cut. The forced signal input is
`outputs/delphes/Lb2LambdaGamma_nev500000_IDEA_edm4hep.root`; the central
Winter2023 IDEA inclusive Z→bb input is the cached byte copy
`work/cache/winter2023_zbb/events_000083138.root` of the first catalogued
`p8_ee_Zbb_ecm91` file. This is one central file, not independent training
and test files. The photon container, detector card, vertex quality,
daughter d0 significance, Λ flight, and thrust-hemisphere requirements are
otherwise those of the current baseline JSON.

FCCAnalyses `pre-edm4hep1` revision:
`91c7d6c5a5c8ad5c3848d6d7cf8383e93c9b74e3`. Exact input, card, and
config SHA256 values, command logs, ROOT and Parquet outputs are under
`outputs/analysis/studies/preselection15_pilot1000/` and the associated
named ROOT/Parquet files in `outputs/analysis/studies/`. Signal and Z→bb
each use `--nevents 1000 --ncpus 1`; all output names are distinct.

## Observed effect

| 1,000 input events per sample | Baseline builder candidates | Baseline + ±15 MeV | 4.5–6.5 builder candidates | 4.5–6.5 + ±15 MeV |
|---|---:|---:|---:|---:|
| Direct truth-matched Λb→Λγ | 535 | 528 | 535 | 528 |
| Other forced-signal combinations | 142 | 59 | 159 | 66 |
| Inclusive Z→bb combinations | 77 | 16 | 99 | 21 |

The offline window retains 528/535 = 98.7% of direct candidates entering
that step in either reconstruction. Its cumulative direct-candidate count is
528 from 1,000 input events, and those 528 occupy 528 distinct events.
The same first 1,000 forced events contain 1,001 generated direct decays in
the earlier generated-chain audit, so the decay-denominator fraction is
528/1,001 = 52.7%. Both charge signs are present: 259 Λb and 269 anti-Λb
selected true candidates.

In the widened reconstruction, the offline window retains 66/159 = 41.5%
of other forced-signal combinations and 21/99 = 21.2% of Z→bb combinations
relative to their own builder outputs. These are candidate retentions,
not generated-event efficiencies. The 21 Z→bb candidates occupy 16 distinct
events; the baseline has 16 candidates in 14 events. Widening from the
working-tree baseline adds zero matched direct candidates, seven selected
other forced-signal combinations, and five selected Z→bb combinations in
this pilot. Forced signal counts do not represent physical Z→bb yields.

The selected and rejected Parquet tables retain `source_id`, `event_entry`,
`candidate_slot`, `candidates_in_event`, fitted PV/SV and daughter displacement
fields, Λ-to-PV geometry, selected photon original object index and measured
`px,py,pz,E`, plus truth labels for diagnosis. Candidate construction and
the offline mass cut use reconstructed quantities only. The Λ-to-PV DCA and
cosine are kept for study: a Λ from a displaced Λb is not required to point
back to the PV. The photon ray proxy is not a measured photon vertex.

The current reconstruction additionally stores `lambda_d0`,
`lambda_d0_sigma`, and signed `lambda_d0_sig`. Its sign convention is
`d0 = (SV−PV)·(p_y,−p_x)/pT`. The uncertainty projects the summed fitted SV
and PV xy covariance matrices onto that transverse normal. It is a linearized
estimate that assumes independent PV/SV fits and does not propagate the Λ
direction uncertainty.

## Limit and proposed next step

One thousand Z→bb events give only 21 selected combinations. They cannot
measure rare-tail BDT rejection, fit a background shape, or justify changing
the reference selection. Review the added 4.5–4.7 GeV candidates and the
displacement/photon distributions before adopting the range. Then run the
named scenario on independent central Z→bb source files and forced Λη
evaluation data, build the post-Λ audit with
`studies/reconstruction/prepare_bdt_dataset.py --lambda-half-window .015
--lb-mass-min 4.5 --lb-mass-max 6.5`, and train with
`studies/reconstruction/train_postlambda_bdt.py`. Keep the current BDT and
its 4.9–6.3 GeV snapshot as a separate reference.

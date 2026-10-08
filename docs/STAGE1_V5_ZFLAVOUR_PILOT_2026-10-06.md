# v5 opposite-jet flavour pilot — 6 October 2026

## Question

Can the v5 event-jet scores identify the generated Z→bb, Z→cc, and Z→ss
flavour in events with a selected Λb-like candidate, and does the opposite-jet
b score separate direct Λb→Λ⁰γ signal from selected Z→ss candidates?

This is an exploratory discriminator check using the pretrained Weaver scores.
It is not a trained v5 BDT or a normalized background-yield estimate.

## Inputs and processing

For each inclusive sample, the first 1,000 entries of six distinct 100k-event
ROOT files were reconstructed with the v5 chain and
`config/lb_reco_v5_training.json`: **6,000 input events per sample**. Files
were selected by ascending numeric file ID from the mounted Winter2023 IDEA
directories:

| Sample | Six file IDs |
|---|---|
| Zbb | 000083138, 000101935, 000116655, 000248631, 000273908, 000317536 |
| Zcc | 000046867, 000150703, 000195074, 000277162, 000314236, 000331342 |
| Zss | 000099129, 000133883, 000134865, 000142551, 000218368, 000223817 |

The input pattern was
`/eos/experiment/fcc/ee/generation/DelphesEvents/winter2023/IDEA/p8_ee_Z{bb,cc,ss}_ecm91/events_*.root`.
Each run used `LB_RECO_ANALYSIS=analysis/studies/lb2lambda_gamma_reco_v5.py`,
an event limit of 1,000, one CPU, and the v5 training config. ROOT tuples and
flattened candidate Parquets are under
`/tmp/rquaglia/fccee_lblgamma_study/flavour_tagging_v5_zflavour_trial/`.
Their concatenated candidate table, JSON summary, and score plot are under its
`results/` subdirectory. The direct-signal reference is the existing first
1,000-event pilot
`outputs/analysis/studies/flavour_tagging_v5_trial/signal_1000_v5_candidates_all_ft.parquet`.
The same v5 reconstruction tree and pretrained model as the 2026-10-05 signal
pilot were used: FCCAnalyses checkout `0315db1e2941e2886813cb645193e348f3863d5d`,
config `lb_reco_v5_training.json`, and model
`fccee_flavtagging_edm4hep_wc_v1`. See the [signal pilot note](STAGE1_V5_FLAVTAG_SIGNAL_PILOT_2026-10-05.md)
for the config and model file checksums.

The reconstruction command for each file was:

```bash
env LB_RECO_ANALYSIS=analysis/studies/lb2lambda_gamma_reco_v5.py \
  timeout 1200 scripts/run_reco_preselection.sh zbb \
  /eos/experiment/fcc/ee/generation/DelphesEvents/winter2023/IDEA/p8_ee_Zbb_ecm91/events_000083138.root \
  /tmp/rquaglia/fccee_lblgamma_study/flavour_tagging_v5_zflavour_trial/zbb_events_000083138_1000.root \
  1000 config/lb_reco_v5_training.json 1
```

For Zcc and Zss, replace the sample label and input path with the corresponding
`p8_ee_Zcc_ecm91`/`zcc` or `p8_ee_Zss_ecm91`/`zss` values and use the file IDs
in the table above. Flattening each tuple used `flatten_candidates.py --mode
zbb --source-id FILE_INDEX`; the all-file comparison was run with
`studies/reconstruction/compare_v5_zflavour_pilot.py`.

The downstream common region is `E(Λb) >= 10.5 GeV` and fitted
`|m(Λ⁰)-1.115683 GeV| <= 12.5 MeV`, after the v5 Stage-1 builder requirements.
For event-level summaries, one candidate per event was selected by highest
reconstructed Λb energy, with `candidate_slot` as a tie breaker. This ranking
does not use flavour scores.

## Selected candidate and event counts

| Sample | Input events | Candidate rows before common region | Rows in common region | Selected events | Signal truth matches |
|---|---:|---:|---:|---:|---:|
| Zbb | 6,000 | 16 | 16 | 16 | 0 |
| Zcc | 6,000 | 30 | 29 | 26 | 0 |
| Zss | 6,000 | 40 | 39 | 36 | 0 |
| Direct signal reference | 1,000 | 572 matched rows | 572 | 572 | 572 |

The selected background sample is small: only 78 events across all three
flavours. All Z sample candidate rows are unmatched to the Λb signal truth
chain, as expected. Every row in the common region had all ten candidate-
aligned B/C/S/Q/G score values present and valid.

## Opposite-jet flavour response

Among one-candidate-per-event representatives, choose the largest of the
other-jet B, C, and S scores as the predicted flavour:

| Generated sample | Predicted B | Predicted C | Predicted S |
|---|---:|---:|---:|
| Zbb | 16/16 | 0/16 | 0/16 |
| Zcc | 0/26 | 24/26 | 2/26 |
| Zss | 1/36 | 1/36 | 34/36 |

The event-level one-score AUCs were 1.000 for Zss versus Zbb using the other-
jet S score, 0.991 for Zss versus Zcc using S, and 0.988 for Zcc versus Zbb
using C. These values describe this small, unweighted pilot sample; they are
not performance estimates for the inclusive production mixture.

The normalized distributions are in
[otherjet_bcs_scores.png](/tmp/rquaglia/fccee_lblgamma_study/flavour_tagging_v5_zflavour_trial/results/otherjet_bcs_scores.png),
and full counts and AUC values are in
[summary.json](/tmp/rquaglia/fccee_lblgamma_study/flavour_tagging_v5_zflavour_trial/results/summary.json).

## Simple signal-versus-Zss check

For the direct matched signal reference versus Zss, the event-level AUC of the
other-jet B score was 0.993. A raw score requirement `other-jet B >= 0.8`
retained **506/572 (88.5%)** direct signal events and retained **0/36** Zss
events in this pilot. Thresholds 0.90 and 0.95 retained 85.3% and 80.1% of
signal, respectively, while also retaining 0/36 selected Zss events. The
threshold 0.99 retained 40.7% of signal and 0/36 Zss events.

At the `other-jet B >= 0.8` threshold the sample-by-sample event retention was:

| Sample | Retained | Retention |
|---|---:|---:|
| Direct signal | 506/572 | 88.5% |
| Zbb background candidates | 13/16 | 81.3% |
| Zcc background candidates | 0/26 | 0% observed |
| Zss background candidates | 0/36 | 0% observed |

If instead keeping events only when B is the largest of the other-jet B/C/S
scores, the pilot keeps 533/572 (93.2%) signal, 16/16 Zbb, 0/26 Zcc, and 1/36
Zss events. This captures the key limitation: an opposite b jet is expected
both for direct signal from Zbb and for Zbb combinatorial candidates, so this
tagger information by itself does not reject the Zbb component. It may help
separate Zss and Zcc candidates from signal-like Zbb events.

This is encouraging evidence for the proposed direction: the other jet is
usually b-like in the matched signal and s-like in selected Zss candidates.
The observation of zero Zss events passing does **not** establish zero Zss
background after a cut. With only 36 selected Zss events, the pass fraction is
poorly constrained; larger independent samples are needed before choosing a
cut or quoting a rejection efficiency.

## Limits and next step

- Only 1,000 entries were processed from each of six 100k-event files; the
  remaining events in those files were not read by Stage 1.
- File IDs and entry ranges form a bounded pilot, not a frozen random or
  representative catalog sample. No production cross-section weights were
  applied.
- The output comes from the pretrained model with a reconstructed PV supplied
  in place of its upstream MC-PV input. Candidate daughters remain in the
  exclusive event-jet clustering. Both can affect score calibration.
- Scores are not calibrated probabilities in this modified setup. The check
  uses a raw score and does not test the combined offline BDT.
- Candidate multiplicity and event counts are both reported; the event-level
  score result uses one candidate per event to avoid giving multi-candidate
  events extra weight.

The result supports carrying the other-jet B/C/S variables into the next
training iteration and expanding the validation sample. Keep the threshold as
a diagnostic proposal; test it on larger, independent v5 Zbb/Zcc/Zss samples
and compare at fixed direct-signal efficiency before requesting a selection
change.

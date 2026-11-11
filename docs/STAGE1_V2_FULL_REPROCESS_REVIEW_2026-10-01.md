# Direct-sample stage-1 v2 reprocessing — PI review

## Question and comparison

Do the new 3D-flight, isolation, thrust, and Z-closure branches preserve the
candidate labels and common observables of the previous stage-1 output on
the same generated events? Physics Λb→Λγ, PHSP Λb→Λγ, and Λb→Λη are each
reconstructed with the **same one-photon** script. Zbb is reserved for the
PI's Condor campaign.

This is a separately named `_v2` scenario. The old tuple used
`config/lb_reco_preselection_15mev_45_65.json` (Rxy distance/significance),
whereas v2 uses `config/lb_reco_preselection_15mev_45_65_3d.json` (3D
distance/significance). The new producer also writes the activity and
closure fields without selecting on them. The old tuple and its provenance
remain intact.

## Exact inputs and commands

All inputs have 100,000 generated events. The directly executed commands use
the FCCAnalyses checkout at `0315db1e2941e2886813cb645193e348f3863d5d`
with local analysis edits, `--ncpus 4`, and no `--nevents` limit:

```bash
source external/FCCAnalyses/setup.sh
LB_RECO_CONFIG="$PWD/config/lb_reco_preselection_15mev_45_65_3d.json" \
  fccanalysis run analysis/studies/lb2lambda_gamma_reco.py \
  --files-list /eos/lhcb/lbdt3/user/rquaglia/fcc_ee/lblgamma/outputs/Lb2LambdaGammaPhysics_nev100000_IDEA_edm4hep.root \
  --output /eos/lhcb/lbdt3/user/rquaglia/fcc_ee/lblgamma/outputs/nominal_preselection_100k_signal_physics_reco_v2.root --ncpus 4
LB_RECO_CONFIG="$PWD/config/lb_reco_preselection_15mev_45_65_3d.json" \
  fccanalysis run analysis/studies/lb2lambda_gamma_reco.py \
  --files-list /eos/lhcb/lbdt3/user/rquaglia/fcc_ee/lblgamma/outputs/Lb2LambdaGamma_nev100000_IDEA_edm4hep.root \
  --output /eos/lhcb/lbdt3/user/rquaglia/fcc_ee/lblgamma/outputs/nominal_preselection_100k_signal_phsp_reco_v2.root --ncpus 4
LB_RECO_CONFIG="$PWD/config/lb_reco_preselection_15mev_45_65_3d.json" \
  fccanalysis run analysis/studies/lb2lambda_gamma_reco.py \
  --files-list /eos/lhcb/lbdt3/user/rquaglia/fcc_ee/lblgamma/outputs/Lb2LambdaEta_nev100000_IDEA_edm4hep.root \
  --output /eos/lhcb/lbdt3/user/rquaglia/fcc_ee/lblgamma/outputs/nominal_preselection_100k_lbgamma_eta_reco_v2.root --ncpus 4
```

The comparison script is `studies/reconstruction/compare_stage1_v2.py`.
The historical and v2 outputs unexpectedly assign different `event_entry`
values to many **identical physical events**, even though the PHSP source
file and old ROOT hashes match the old production manifest. For example,
the same PHSP event with exactly equal PV, thrust, object indices, and
fitted mass was labelled `4450` previously and `10027` in v2. The script
therefore joins physical events by their reconstructed count/PV/thrust
fingerprint, then candidates by charge hypothesis and reconstructed
proton/pion/photon indices. It reports `event_entry` remapping separately.
Within a single tuple `event_entry` remains unique, but it is **not a safe
cross-production event key** in this comparison. Truth is a comparison
label only, never a candidate selection input.

## Results and decision

All three jobs exited with code 0 after processing 100,000 source events.
`verify_stage1_v2_outputs.py` streamed all new trees: each has 332 ROOT
branches, and all 161 specifically checked new candidate-vector branches
have the expected length in every event.

| Sample | Old events with candidates | V2 events with candidates | Old candidates | V2 candidates | Old → v2 direct truth matches | Old only / v2 only candidates | Shared-candidate label mismatches |
|---|---:|---:|---:|---:|---:|---:|---:|
| Physics Λb→Λγ | 56,866 | 56,871 | 60,593 | 60,598 | 55,393 → 55,395 | 1 / 6 | 0 |
| PHSP Λb→Λγ | 56,735 | 56,737 | 60,424 | 60,426 | 55,293 → 55,294 | 0 / 2 | 0 |
| Λb→Λη as one γ | 41,956 | 41,957 | 44,930 | 44,932 | not applicable to γ truth label | 0 / 2 | 0 |

The Physics comparison finds 60,592 common candidates, one old-only
truth-matched candidate, and six v2-only candidates, three of which are
truth matched. PHSP has all 60,424 old candidates plus two v2-only ones,
one truth matched. The η sample has all 44,930 old candidates plus two
v2-only ones. Every shared candidate has identical checked truth-match and
mass-hypothesis labels, truth MC indices, fitted Λ and Λb masses,
reconstructed/truth helicity angles, and hemisphere fields within 1e-5
absolute and 1e-6 relative tolerance for floating values.

The cumulative direct-candidate efficiencies per generated source event are
55,395/100,000 = 55.395% for Physics v2 and 55,294/100,000 = 55.294%
for PHSP v2. Candidate-bearing-event fractions are 56.871% and 56.737%
respectively. The η forced sample is a feed-down shape study, not a
physical Z→bb yield; `lb_truth_matched` is zero in one-photon γ mode and
does not measure η feed-down matching.

The changed 3D flight selection gives a genuinely different candidate set,
albeit a small change on these forced samples. Keep `_v2` outputs as a named
scenario. Do not overwrite the old ROOT files or describe the two as
identical. The event-ID remapping also means an analysis comparing old and
v2 tuples must use the stored fingerprint or another validated persistent
event identifier.

The exact input, source, and output SHA-256 values, paths, counts, and
commands are in `config/lb_stage1_v2_samples.json`. The comparison JSONs,
mass and cosθp overlays, and new-branch validation JSONs are preserved under
`outputs/analysis/studies/offline_bdt_session_20261001/stage1_v2_full_comparison/`.
The direct candidate Parquets in the EOS output directory carry `_v2` in
their names; each has one candidate per row, retains `event_entry` and
`candidate_slot`, and preserves the newly added observables. They were
flattened with `flatten_candidates.py --mode gamma`, including the η sample
because it is intentionally reconstructed under the one-photon hypothesis.

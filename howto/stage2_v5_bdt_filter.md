# v5 Stage 2: BDT score and filter for all samples

One Condor job per v5 Stage-1 ROOT file runs
`studies/reconstruction/stage2_v5_filter.py`. The job attaches the trained
RBDT score to every candidate and keeps the events that have at least one
candidate with `v5_bdt_score > 0.4`. All Stage-1 branches are kept, including
the photon-pair lists, the Armenteros variables and the fitted Λ mass, so the
output can be filtered and augmented again later.

Samples (the defaults of `scripts/make_v5_stage2_queue.py`): `signal_physics`,
`signal_phsp`, `lambda_eta`, `lambda_pi0`, `zbb`, `zcc`, `zss`.

Output: `/eos/lhcb/lbdt3/user/rquaglia/fcc_ee/lblgamma/outputs/stage2_v5_bdt0p4_20261007/<sample>/<source_id>.root`,
each next to its `.stage2.json` sidecar. The model files the workers read,
with their SHA-256 values, are in `model/` under the same folder.

## Run

```bash
python3 scripts/make_v5_stage2_queue.py            # skips completed ROOT + sidecar pairs
condor_submit scripts/condor_v5_stage2.sub         # from lxplus, repository root
env -u PYTHONPATH -u PYTHONHOME myenv/bin/python studies/reconstruction/summarize_v5_stage2.py \
  --stage2-dir /eos/lhcb/lbdt3/user/rquaglia/fcc_ee/lblgamma/outputs/stage2_v5_bdt0p4_20261007 \
  --output-dir outputs/stage2_v5_bdt0p4_20261007_summary
```

Rerunning the queue maker after jobs finish lists files missing either the
ROOT payload or its sidecar. Check `condor_q` first to avoid duplicating jobs
that are still pending or running. Each job uses about 1 minute and 1.3 GB of
memory on one core.

Jobs run in `myenv/run`, ROOT 6.36, which is the version that wrote the RBDT
file. Key4hep ROOT 6.28 cannot read that model. The worker copies each input
and the model from EOS with `xrdcp` to local scratch before ROOT opens them;
`--source-file` preserves the original EOS path used by the training split
hash. Single-threaded jobs make `rdfentry_` equal to the Stage-1 row number.

## Added branches and bookkeeping

| Branch | Meaning |
|---|---|
| `v5_bdt_score` | RVec<double>, one score per candidate, same order as `lb_mass` |
| `v5_bdt_pass` | score > cut, per candidate. Kept events retain all their candidates; select with this flag |
| `stage1_entry` | Stage-1 row number of the event |
| `v5_bdt_split` | 0/1/2 = train/validation/test for signal, zbb, zcc, zss (the training's own rule and seed); −1 for PHSP, η, π⁰ |

Use only `v5_bdt_split` ∈ {1, 2} events (and −1 samples) for yields, shapes
and efficiencies; training events have optimistic scores.

Each file stores, as `TParameter<Long64_t>` objects that `hadd` sums and in
its sidecar:

- **Stage 1 counters:** `eventsProcessed` (generated events) and `eventsSelected` (Stage-1 events).
- **Stage 2 counters:** `stage2_events_in`, `stage2_events_out`, `stage2_events_with_pass`,
  `stage2_candidates_in`, `stage2_candidates_pass`.
- **Truth counters:** `stage2_truth_candidates_{in,pass}` and `stage2_truth_events_{in,pass}`,
  using `lb_truth_matched == 1` as an evaluation label only.

From these, `summarize_v5_stage2.py` reports the Stage-1, Stage-2 and total
event efficiencies, the candidate efficiency, and the truth-matched
efficiencies per sample.

## Validation (7 October 2026, one file per sample)

- **Scores:** RBDT scores agree with the XGBoost model on 2,621 Zss candidates
  (mean |Δ| = 1×10⁻⁶, maximum 2.5×10⁻³).
- **Split:** `v5_bdt_split` matches the training split for every event present
  in the training data (5415/5415 signal events, 5/5 Zss events).
- **Analysis branches:** the photon-pair lists, `arm_alpha`, `arm_qt`,
  `lb_lambda_mass`, `lb_cos_theta_p`, `lambda_d0_sig` and `dm_gg_pi0` are
  bit-identical to Stage 1 for the kept events.
- **Veto code:** `offline_selection_audit.pair_flags` runs unchanged on the output.
- **Counters:** `hadd` sums all counters correctly.

`apply_v5_rbdt_stage2.py`, from the parallel session, is unchanged except for
the ROOT-version switch and the float-dictionary fix. It still fails at
`Snapshot` under ROOT 6.36 when the event filter is enabled, which is why the
production uses `stage2_v5_filter.py`. That script scores in a first pass and
looks the score up by row in the writing pass.

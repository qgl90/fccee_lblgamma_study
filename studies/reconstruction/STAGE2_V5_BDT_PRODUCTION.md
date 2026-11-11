# Stage 2 v5: attach the BDT and make the combined ntuple

`run_v5_stage2_production.py` reads the complete v5 Stage-1 outputs for the
forced `Lb2LambdaGammaPhysics` signal and the Zbb, Zcc, and Zss samples. It
applies the trained ROOT TMVA RBDT model with the strict requirement
`v5_bdt_score > 0.4` and merges the four species into one ROOT file.

## Run

From the repository root, after setting up the same Key4hep/PyROOT environment
used for Stage 1, run:

```bash
myenv/run python studies/reconstruction/run_v5_stage2_production.py \
  --output-dir /tmp/rquaglia/stage2_v5_bdt_20261007 \
  --threads 8 --bdt-cut 0.4
```

The default inputs are the v5 Stage-1 locations under
`/eos/lhcb/lbdt3/user/rquaglia/fcc_ee/lblgamma/outputs`. The default model is
the trained `v5_weighted_bdt_rbdt.root` under
`/tmp/rquaglia/v5_bdt_all_20261007/model_complete/`. Use `--dry-run` to print
the discovered file counts and endpoints without processing. Each input
directory can be overridden with `--signal-dir`, `--zbb-dir`, `--zcc-dir`, or
`--zss-dir`. The output directory must be empty; the runner refuses to replace
an existing result.

The final ROOT output is `stage2_v5_bdt.root`; `stage2_manifest.json` records
input paths, model and cut provenance, sample IDs, and yield/efficiency
summaries. Temporary per-species ROOT files are removed after a successful
merge.

## What is written

The `events` tree retains every input Stage-1 branch and adds:

| Branch | Meaning |
| --- | --- |
| `v5_bdt_score` | RBDT score aligned with the original candidate ordering |
| `v5_bdt_pass` | Candidate flag for the strict `v5_bdt_score > cut` test |
| `v5_analysis_candidate` | Training-consistent truth category: matched signal candidates; unmatched generic-Z candidates |
| `v5_bdt_selected` | Candidate mask: analysis candidate and passing BDT score |
| `sample_id` | `0=signal`, `1=zbb`, `2=zcc`, `3=zss` |
| `v5_expected_candidate_weight` | Expected physical yield per candidate, from the configured branching fractions divided by summed `eventsProcessed` |
| `stage1_efficiency` | Stage-1 selected/generated event efficiency for that species |

Events with no candidate passing both the relevant truth category and the BDT
cut are omitted. In retained events, the original candidate vectors remain
unchanged so that all Stage-1 information is preserved. Use
`v5_bdt_selected` to select the actual candidate population in an RDataFrame
analysis; do not count every candidate in a retained event as passing.

The separate `stage2_sample_summary` tree has one row per species and stores
the input generated and Stage-1 event counts, eligible and passing candidate
counts, both efficiencies (including `stage2_bdt_efficiency`), per-candidate
physical weight, and expected yields before and after the BDT cut. It also stores
the Stage-1 candidate yield per generated event and the combined candidate
yield per generated event, since candidate multiplicities mean those cannot in
general be reconstructed by multiplying event efficiencies alone. The same
information and the sample-name mapping are in `stage2_manifest.json`.

## Weighting and efficiencies

For each Z flavour, the candidate weight is

```text
N_Z * BR(Z -> q qbar) / sum(eventsProcessed)
```

For the direct signal it is

```text
N_Z * BR(Z -> bb) * 2 * f(Lambda_b per b) * BR(Lambda_b -> Lambda gamma)
    * BR(Lambda -> p pi) / sum(eventsProcessed_signal)
```

The Stage-1 candidate count already incorporates the Stage-1 selection. Thus
the weighted expected yield after Stage 1 is
`eligible Stage-1 candidates * v5_expected_candidate_weight`, and the yield
after Stage 2 is that quantity times `stage2_bdt_efficiency`. The summary
reports `stage1_efficiency` (event level), `stage2_event_efficiency`, and their
product for event-retention studies. For candidate yields, use the reported
candidate counts or `stage1_candidate_yield_per_generated_event` times
`stage2_bdt_efficiency`; do not multiply the candidate yield by the event-level
`stage1_efficiency` again.

For an RDataFrame significance scan, use the event-level species weight and
candidate masks, for example by defining candidate values with
`Take(lb_mass, v5_bdt_selected)` (or an equivalent vector selection), then
weighting those values by `v5_expected_candidate_weight`. The BDT score remains
available to scan thresholds above or below 0.4 without rerunning inference;
events rejected at the initial 0.4 threshold are absent, so scans below 0.4
require producing a looser Stage-2 sample.

The generic-Z background category follows the training convention and excludes
truth-matched candidates. Signal yields use truth-matched candidates from the
forced direct-decay sample. The full `lb_truth_matched` column remains in the
output for independent checks.

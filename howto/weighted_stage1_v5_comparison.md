# Plotting the v5 Stage-1 flavour samples

The comparison can be run directly on the Stage-1 ROOT chunks. The `events`
tree keeps candidates in per-event vectors, and the plotting script reads those
vectors and fills candidate-level histograms. **Flattening is not required for
these plots.** Flattening is useful for the later offline-selection and BDT
training tables; inspect `studies/reconstruction/flatten_candidates.py` for
that path.

## Script and inputs

Run from the repository root:

```bash
myenv/bin/python studies/reconstruction/plot_v5_weighted_stage1_comparison.py \
  --output-dir /tmp/rquaglia/fccee_lblgamma_study/v5_comparison
```

The default normalization file is
`config/stage1_v5_weighted_comparison.json`. It contains luminosity-equivalent
`N_Z`, branching fractions, and the signal fragmentation/decay factors. It does
not define the Stage-1 selection: that selection is already embodied in the
input v5 ROOT tuples. You may pass another normalization file with `--config`.

By default it reads:

```text
/eos/lhcb/lbdt3/user/rquaglia/fcc_ee/lblgamma/outputs/zbb_full_condor/stage1_v5_flavtag_20261006/p8_ee_Zbb_ecm91
/eos/lhcb/lbdt3/user/rquaglia/fcc_ee/lblgamma/outputs/zcc_full_condor/stage1_v5_flavtag_20261006/p8_ee_Zcc_ecm91
/eos/lhcb/lbdt3/user/rquaglia/fcc_ee/lblgamma/outputs/zss_full_condor/stage1_v5_flavtag_20261006/p8_ee_Zss_ecm91
/eos/lhcb/lbdt3/user/rquaglia/fcc_ee/lblgamma/outputs/stage1_v5_forced_modes_1m_20261006
```

The signal input is specifically the forced `Lb2LambdaGammaPhysics` mode;
PHSP is intended for the subsequent acceptance study. Set `--zbb-dir`,
`--zcc-dir`, `--zss-dir`, or `--signal-dir` to use different locations. The
output directory receives `stage1_v5_weighted_flavour_comparison.pdf` and
`summary.json` (including file coverage, counter totals, branching fractions,
weights, and histogram under/overflow counts).

At startup the plotter prints each sample's glob and every matched input path.
After reading a sample, it prints the summed `eventsProcessed` and
`eventsSelected`, computed Stage-1 efficiency, per-candidate weight, and
weighted candidate yield. Use `--quiet-files` to suppress individual paths
while retaining each glob and file count.

To check one file from each sample first:

```bash
myenv/bin/python studies/reconstruction/plot_v5_weighted_stage1_comparison.py \
  --max-files 1 --workers 1 \
  --output-dir /tmp/rquaglia/fccee_lblgamma_study/v5_comparison_pilot
```

Use `--help` for the full list. The `--br-zbb`, `--br-zcc`, `--br-zss`,
`--n-z`, `--f-lambdab-per-b`, `--br-lb-lambda-gamma`, and `--br-lambda-p-pi`
options let you vary the normalization without editing the script. Defaults
come from `config/stage1_v5_weighted_comparison.json`.

## RDataFrame backend

A pilot compared all 114 plotted variables on 20 Zbb files and 20 direct-signal
files. The RDataFrame and Uproot histograms matched bin-by-bin. On four workers,
RDataFrame was about 5.5 times faster for Zbb and 4.0 times faster for signal
in that pilot, including RDataFrame setup/JIT time. The plotter now accepts
`--backend rdataframe`; Uproot remains the default. The RDataFrame backend
needs the Key4hep environment (PyROOT), while `myenv` alone is sufficient for
the Uproot backend.

Run the RDataFrame pilot from the repository root with:

```bash
source external/FCCAnalyses/setup.sh
python studies/reconstruction/plot_v5_weighted_stage1_comparison.py \
  --backend rdataframe --max-files 20 --workers 4 \
  --output-dir /tmp/rquaglia/fccee_lblgamma_study/v5_rdf_pilot
```

Remove `--max-files 20` for the full current snapshot. ROOT printed
`TNetXNGFile::Open: Invalid address` messages for the mounted EOS paths during
the pilot, but the event loop completed and histogram counts matched. Check
the ROOT/EOS access log if this backend is used for a long full-sample run.

## What the plotted normalization means

For each generic Z sample, the script weights each selected candidate by

```text
N_Z * BR(Z -> qq) / sum(eventsProcessed)
```

The selected candidate rows already contain the Stage-1 acceptance and
selection. Equivalently, the total plotted yield is proportional to
`N_Z * BR * (eventsSelected/eventsProcessed) * (candidate rows/eventsSelected)`.
The script reports `eventsSelected/eventsProcessed` separately so that this
efficiency can be checked. Multiplying it into the histogram weight again
would count the Stage-1 selection twice. Multiple candidates in an event are
kept as separate rows, matching the current candidate-level comparison.

For signal, the nominal weight is

```text
N_Z * BR(Z -> bb) * 2 * f(b -> Lambda_b)
    * BR(Lambda_b -> Lambda gamma) * BR(Lambda -> p pi)
    / sum(eventsProcessed in forced physics-gamma sample)
```

This assumes one generated direct `Lambda_b -> Lambda gamma` decay per
processed signal event. Signal candidates are required to have
`lb_truth_matched == 1`; generic Z candidates with that truth label are omitted
from the background stack. The Zss default `0.156` in the config is an
equal-down-type approximation to one third of the inclusive down-type Z rate,
not a direct measured `Z -> ss` fraction. The background stack is on the left
axis and signal is on an independent right axis; their vertical heights are
not directly comparable. This is a descriptive Stage-1 comparison, not a BDT
training result.

## Candidate flattening for later training

After selecting the ROOT chunks to train on, use
`studies/reconstruction/flatten_candidates.py` to make one row per candidate.
For a single example chunk:

```bash
python3 studies/reconstruction/flatten_candidates.py \
  --mode zbb \
  --input /path/to/chunk_0.root \
  --output /tmp/zbb_chunk0.parquet \
  --source-id 0
```

Check the script's `--help` for required arguments and options before batching.
The flattened tables are for training and offline selection; use the ROOT-based
plotter above to review Stage-1 variables and the physical scale factors.

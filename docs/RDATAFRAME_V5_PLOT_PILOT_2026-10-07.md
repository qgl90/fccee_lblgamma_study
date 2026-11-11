# v5 Stage-1 plot backend pilot — 7 October 2026

## Purpose

Compare the current Uproot/Awkward histogram path with ROOT RDataFrame for the
114 candidate variables used by
`studies/reconstruction/plot_v5_weighted_stage1_comparison.py`. The test uses
the same first 20 ROOT files in each sample, the same v5 truth-matching mask,
and the same histogram edges. It is a performance and histogram-equivalence
pilot, not a full-snapshot result.

## Results

| Sample | Files | Bytes scanned | Uproot time | RDataFrame time | RDataFrame speedup | Bin comparison |
|---|---:|---:|---:|---:|---:|---|
| Zbb | 20 | 235,499,149 | 55.4 s | 10.0 s | 5.5× | all 114 histograms match exactly |
| Direct `Lb2LambdaGammaPhysics` | 20 | 707,856,750 | 52.5 s | 13.1 s | 4.0× | all 114 histograms match exactly |

Both backends used four workers; the Uproot backend used a 64 MB `step-size`.
RDataFrame timing includes C++ JIT setup and the event loop. The signal test
uses the truth-matched candidate mask; the generic Z test removes those direct
truth matches. A separate one-file-per-sample run of the full plotting script
completed through PDF and JSON generation with the RDataFrame backend.

## Reproduce

The benchmark script is
`studies/reconstruction/benchmark_v5_rdataframe.py`. It compares the same
histogram-kernel functions and emits per-variable exact-bin checks. Run it in
the Key4hep environment:

```bash
source external/FCCAnalyses/setup.sh
python studies/reconstruction/benchmark_v5_rdataframe.py \
  --sample zbb --max-files 20 --workers 4

python studies/reconstruction/benchmark_v5_rdataframe.py \
  --sample signal --max-files 20 --workers 4
```

The main plotting script accepts `--backend rdataframe`; the Uproot backend
remains the default. The one-file-per-sample integration output used for the
deck was written under
`/tmp/rquaglia/fccee_lblgamma_study/v5_rdf_plot_pilot_retry/`.

## Caveats

- These timings are from a bounded 20-file subset and depend on EOS cache and
  host load. They do not guarantee the same full-sample speedup.
- ROOT emitted `TNetXNGFile::Open: Invalid address` messages while accessing
  mounted EOS paths, although event loops completed and all tested histograms
  matched. Investigate the ROOT/EOS URL handling before adopting this backend
  as the default.
- The backend uses the Key4hep PyROOT environment; the repository analysis
  virtualenv alone does not provide ROOT.
- Use a modest number of threads on shared EOS storage. Thirty-two workers
  were slower in the user's full plotting run; the pilot used four.

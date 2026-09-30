# Post-preselection BDT workflow and PI review contract

## Question and reference

Can a reconstructed-observable BDT reject generic Winter2023 IDEA
`p8_ee_Zbb_ecm91` combinations after the present Λγ candidate builder and
a fitted-Λ mass window, while retaining a useful Λb→Λγ mass–angle sample?
The reference reconstruction remains `analysis/studies/lb2lambda_gamma_reco.py`
with `config/lb_reco.json`; the BDT changes only the downstream candidate
selection. The mass fit range stays **4.9–6.3 GeV**. A 5.4–5.9 GeV
interval is used only to diagnose the expected background under the signal
peak. All plots and cut counts must state whether they count candidates,
distinct events, or generated decays.

## Samples

| Sample | Decay file / campaign | Role |
|---|---|---|
| Forced Λb→Λ(pπ)γ PHSP | `evtgen/Lb2LambdaGamma.dec` | Acceptance baseline and truth-matched training signal. |
| Forced Λb→Λ(pπ)γ HELAMP | `evtgen/Lb2LambdaGamma_trpol.dec` | Independent physics-angular-model check; never used in BDT fitting. |
| Forced Λb→Λ(pπ)η(γγ) | `evtgen/Lb2LambdaEta.dec` | Partially reconstructed feed-down under the one-photon signal builder. |
| Inclusive Z→bb | Ten distinct Winter2023 IDEA `p8_ee_Zbb_ecm91` files | Combinatorial background; separate source files for training/validation/test. |

The HELAMP amplitudes in the new file are the values in the
[LHCb Sim10 decay file](https://gitlab.cern.ch/lhcb-datapkg/Gen/DecFiles/-/blob/Sim10/dkfiles/Lb_gammaLambda%3Dtrpol.dec):
`Lambda_b0sig→MyLambda0 gamma HELAMP 0 0 1 0` and
`MyLambda0→p+ pi− HELAMP .906 0 .423 0`.
The local aliases were adapted to the `Lambdab0_SIGNAL` Pythia8 interface.
No LHCb acceptance cut was copied. The source metadata marks a polarized
Λb setup, but the local decay file alone does not establish the Z-pole Λb
production spin density. PHSP remains the angular acceptance reference.
Both charge-conjugate chains are generated and reconstructed.

## Execute and inspect one stage at a time

The driver is `scripts/run_bdt_study.sh`. Its stages can be invoked
independently and safely rerun; existing named outputs are retained. The
configured default generates 10,000 events in each forced sample and uses
exactly ten 100k-event central Zbb files. The host has 48 cores, while 40
are visible to this process; the default Zbb batch uses ten independent
jobs × four threads. Each Zbb ROOT and Parquet output carries
its original file index as `source_id`.

```bash
bash scripts/run_bdt_study.sh provenance
bash scripts/run_bdt_study.sh catalog
bash scripts/run_bdt_study.sh cache
bash scripts/run_bdt_study.sh generate
bash scripts/run_bdt_study.sh reco_forced
bash scripts/run_bdt_study.sh reco_zbb
bash scripts/run_bdt_study.sh flatten
bash scripts/run_bdt_study.sh dataset
bash scripts/run_bdt_study.sh statistics
bash scripts/run_bdt_study.sh train
bash scripts/run_bdt_study.sh angular
bash scripts/run_bdt_study.sh projection
bash scripts/run_bdt_study.sh slides
```

`bash scripts/run_bdt_study.sh all` executes that order. The environment
variables `STUDY_TAG`, `FORCED_EVENTS`, `FORCED_THREADS`,
`ZBB_THREADS_PER_FILE`, `ZBB_PARALLEL_FILES`, `ANALYSIS_PYTHON`, and the
three forced EDM/Parquet path overrides are resolved at script start.
The exact per-stage commands, output names, and seeds are in that readable
shell script. `provenance.txt`, the candidate-table manifest, generator
logs, and individual Zbb reconstruction logs record the actual run.

The central EOS files are copied with `scripts/cache_zbb_inputs.sh` into
`work/cache/winter2023_zbb/` and checked against EOS file sizes. The pinned
`fccanalysis` runner rewrites `/eos/` inputs to a `root://` endpoint; that
endpoint is unavailable in this sandbox. Running the local copies avoids
that I/O dependency. The cache is a byte copy of the same central files,
not a new generator sample.

## Dataset, split, and variables

`prepare_bdt_dataset.py` saves an unchanged stage-1 candidate audit and a
post-Λ audit/table with `|m(pπ)−1.115683|<0.010 GeV`. The cut uses the
fitted-momentum mass. Truth and ancestry label candidate classes afterward.
All nonmatched combinations remain in the audit. The model trains on full
PHSP truth matches versus generic Zbb combinations; wrong combinations and
Λη feed-down are scored only for validation. Each candidate is one row,
with `source_id`, `event_entry`, `candidate_slot`, and multiplicity preserved.

Generic Zbb source files 0–6 train, file 7 validates, and files 8–9 test.
PHSP signal uses a deterministic event hash, so multiple candidates from a
signal event cannot straddle splits. This is stronger than the earlier
100k-file `--pilot` event split. The historical snapshot used 39 BDT inputs;
the current feature table adds Lambda d0 and its significance for 41 inputs.
Units, missing-value
handling, and construction of photon isolation, ROE recoil, vertex, and
thrust features are documented in [BDT_FEATURES.md](BDT_FEATURES.md).
Neither Λγ mass nor reconstructed/generated cosθp enters the BDT.

`train_postlambda_bdt.py` fits fixed-depth XGBoost trees with balanced
class weights, uses validation for early stopping, and chooses score
thresholds solely from validation-signal quantiles. It then reports
file-held-out Zbb rejection and test signal retention. It writes
`bdt_model.json`, a scored candidate Parquet retaining all labels and fit
observables, a ROC, score distributions, gain rankings, mass/angle shape
checks, and `metrics.json`/`metrics.md`. The independent HELAMP sample is
scored at those frozen thresholds. The `angular` stage compares selected
and generated cosθp in held-out PHSP events and the independent HELAMP
sample, showing generated-bin counts behind each efficiency. The HELAMP
multithreaded snapshot has event rows reordered relative to the generator
input after part of the run, so the angular stage validates its selected
decays by unique truth angle and charge before forming the distribution.
Do not join that table to generated rows by `event_entry`. No threshold is
promoted to the reference analysis without PI review.

## Yield scale and required background statistics

The projection uses `config/yield_projection.json`, with 5×10¹² Z,
`B(Z→bb)=0.1512`, a Z-pole fraction 0.084 for **all** weakly decaying
b baryons, `B(Λb→Λγ)=10⁻⁵` as the PI benchmark, and physical Λ→pπ and
η→γγ fractions. The `lambda_b_share_of_b_baryons=1` field is an
upper-envelope proxy, not a measured Λb-specific production fraction.
`plot_yield_projection.py --input-manifest ...` resolves the actual
generated event denominators before making candidate-yield plots.
`plot_bdt_yield_projection.py` adds frozen `sig80` and `sig50` score stages
using only held-out PHSP signal and source-file-held-out Zbb, plus the
independent forced Λη evaluation. The same mass and cosθp displays are
saved at each stage; blank bins have no MC support.

The earlier 100k Zbb projection had 814 candidates after the ±10 MeV Λ
window, or 0.00814 per generated Zbb event. In the 5×10¹² Z scenario,
the post-Λ generic background was about 6.15×10⁹ candidates, while the
signal upper proxy was about 4.52×10⁵. Thus a BDT can be trained with a
million Zbb events, but demonstrating a high-purity peak requires a much
larger **independent test** sample. `estimate_zbb_statistics.py` calculates
the required test and total events for 10%, 50%, and 90% target purity
using the approximate zero-survivor 95% Poisson upper bound of three MC
events. Empty test bins are never treated as zero physical background.

## Review gate

The PI should compare the new post-Λ selection to the unchanged stage-1
rows on the same events, including the true signal, signal wrong
combinations, η feed-down, and generic Zbb. Review the file-held-out ROC,
candidate and event efficiencies, score-dependent mass/angle shapes, and
physics HELAMP versus PHSP angular efficiency. In particular, the largest
pilot BDT gains came from `E_same` and `deltaE`; a discrepancy between
local forced production and central Zbb event modeling could make those
features deceptively powerful. The independent-file test checks
overfitting to Zbb files, while a future central or otherwise matched
signal production is needed to test that sample-domain question.
The completed one-million-Zbb review and numerical limits are recorded in
[BDT_REVIEW_2026-09-29.md](BDT_REVIEW_2026-09-29.md).

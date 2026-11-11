# Stage 1 v3 isolation energy ratios: Physics versus frozen Zbb snapshot

## Question

Does normalizing the new same-hemisphere activity energy by the candidate
photon energy improve the simple-cut separation beyond the raw energy sums?
The PI recalled an older isolation-energy ratio, so this study also checks
what can be compared directly.

## Inputs and definition

Input is the completed `reference_mass5_pi0/candidates/` Parquet dataset in
`outputs/analysis/studies/v3_offline_inspection_20261002/`: the Physics v3
sample (100,000 generated events) and the same frozen 191 Zbb chunks
(76,222,397 processed events) used in the v3 reference study. The rows
already pass the 4.7–6.5 GeV Λb fit range, Λ⁰ ±5 MeV window, and
same-hemisphere π⁰ veto. Denominators for this comparison are **52,789
truth-matched Physics candidates and 207,110 nonmatched Zbb candidates**.
Wrong Physics combinations are shown separately in distribution plots.

For each cone, center, and charge class, the new quantity is
`{iso,lambda0_iso}_RXX_{all,charged,neutral}_energy / gamma_E`.
The numerator is the scalar energy sum of reconstructed activity on the
fitted Λ⁰ hemisphere in the named cone. Candidate proton and pion are
excluded from charged activity; candidate photon is excluded from neutral
activity; all three are excluded from all activity. `gamma_E` is the
candidate photon energy. Every studied candidate had valid positive
`gamma_E`. This uses only reconstructed information.

The older Stage 1 `iso_R03_E` and `iso_R05_E` ratio branches have a
**different numerator**: they do not impose the fitted Λ⁰ hemisphere and
include the Λ⁰ daughters. The ratios here are derived from the new
same-hemisphere sums in the candidate Parquets. They are not numerically
equivalent to those old branches. See
[`howto/understand_isolation.md`](../howto/understand_isolation.md).

## Observed one-variable working points

Each threshold was chosen on the same truth-matched Physics candidates on
which its retention is reported, and then applied to the nonmatched Zbb
candidates. The Zbb event retention uses unique `(source_id,event_entry)`
among those candidates. All values below are conditional on the preceding
offline selection.

| Signal candidate retention | Observable and upper bound | Zbb candidate retention | Zbb event retention |
|---:|---|---:|---:|
| ≥99% | Photon R03 all ΣE/Eγ ≤ 1.023 | 34.1% | 36.0% |
| ≥99% | Photon R03 all ΣE ≤ 11.705 GeV | 53.3% | 54.3% |
| ≥99% | Photon R05 all ΣE/Eγ ≤ 2.066 | 39.8% | 41.7% |
| ≥99% | Photon R05 all ΣE ≤ 17.497 GeV | 52.6% | 53.4% |
| ≥95% | Photon R05 all ΣE/Eγ ≤ 0.933 | 20.1% | 21.2% |
| ≥95% | Photon R05 all ΣE ≤ 10.806 GeV | 33.9% | 34.9% |

At 99% signal retention the best single ratio here is photon-centered R03
all activity. Charged and neutral R03 ratios separately retain about 48.6%
and 47.4% of Zbb candidates; the all-activity ratio retains 34.1%.
The Λ⁰-centered R03 all-energy ratio retains 70.4%, so the photon-centered
ratio is the stronger single handle on this sample.

The [ratio-versus-raw plot](../outputs/analysis/studies/v3_offline_inspection_20261002/isolation_ratio_study_pi0/ratio_vs_raw_retention.png),
[focused ratio distributions](../outputs/analysis/studies/v3_offline_inspection_20261002/isolation_ratio_study_pi0/focus_ratios_1.png),
and [full working-point CSV](../outputs/analysis/studies/v3_offline_inspection_20261002/isolation_ratio_study_pi0/isolation_working_points.csv)
are under the dedicated session output folder. The script and exact command
are in [`study_v3_isolation_ratios.py`](../studies/reconstruction/study_v3_isolation_ratios.py)
and its generated `manifest.json`.

## PI review point

The all-energy/photon-energy ratio is a promising **candidate** for a named
offline scenario. These thresholds are exploratory because they were chosen
and evaluated on the same candidates, and because the Zbb catalog is still
a partial Condor campaign. No reference selection or BDT has been changed.
Before adopting a cut, validate it on withheld chunks and measure its joint
effect with the other simple cuts and BDT, including the generated-event
signal efficiency and Zbb event denominator.

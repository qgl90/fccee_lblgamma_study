# v3 offline reference: Λ⁰ mass window, Λb energy, and diphoton diagnostics

## Question and selections

The PI first requested an offline reference after Stage 1 with a Λ⁰ mass
window and **no π⁰/η veto**, then a separate comparison with a simple Λb
energy cut near 9 GeV. The earlier reference was
`lambda5_same_hemi_all`: `4.7 ≤ m(Λγ) ≤ 6.5 GeV` and
`|m(pπ)−1.115683 GeV| ≤ 0.005 GeV`. It still records same-hemisphere
raw-photon partner masses. The named comparison
`lambda5_lbE9_same_hemi_all` adds reconstructed `lb_E ≥ 9 GeV`.
The PI subsequently selected `lambda12p5_lbE10p5_same_hemi_all` as the new
offline default before BDT training. None of these scenarios applies a photon
veto or uses truth in a cut.

## Frozen inputs and mass-window choice

The exact Physics v3 ROOT input and 191-chunk Zbb snapshot are in the
[`reference_mass5/summary.json`](../outputs/analysis/studies/v3_offline_inspection_20261002/reference_mass5/summary.json).
They contain 100,000 Physics and 76,222,397 Zbb processed input events.
The corresponding audit Parquets retain all Stage 1 candidates. The mass
window scan on these same events gives:

| Λ⁰ half-window | Direct Physics candidates | Nonmatched Zbb candidates |
|---:|---:|---:|
| ±5 MeV | 54,324 | 619,133 |
| ±7.5 MeV | 54,793 | 709,691 |
| ±10 MeV | 55,072 | 799,537 |
| ±15 MeV | 55,395 | 979,293 |

Thus ±5 MeV retains 98.07% of the direct signal candidates already within
the Stage 1 ±15 MeV window, while retaining 63.22% of nonmatched Zbb
candidates in that window. The
[mass-window plot](../outputs/analysis/studies/v3_offline_inspection_20261002/reference_mass5_lbE9/plots/lambda_mass_window_scan.png)
and CSV show all scanned widths. This is a comparison within Stage 1's
existing ±15 MeV acceptance; decays outside that Stage 1 window cannot be
recovered offline.

## Λb energy comparison on the same candidates

The study script reads the frozen mass-window selected Parquets and writes
one full-column candidate Parquet per source in
`outputs/analysis/studies/v3_offline_inspection_20261002/reference_mass5_lbE9/candidates/`.
Every original candidate column is retained, and 36 same-hemisphere
`{iso,lambda0_iso}_RXX_{all,charged,neutral}_energy_over_gamma_E`
columns are added. The unchanged all-candidate audits remain in the parent
`reference_mass5/` directory. The
[manifest](../outputs/analysis/studies/v3_offline_inspection_20261002/reference_mass5_lbE9/manifest.json)
records the command, hashes, processed-event denominators, and one-row-per-
candidate source files.

| Stage | Direct Physics candidates | Physics wrong candidates | Physics candidate-bearing events | Nonmatched Zbb candidates | Zbb candidate-bearing events |
|---|---:|---:|---:|---:|---:|
| Λ⁰ ±5 MeV, no photon veto | 54,324 | 4,036 | 55,507 | 619,133 | 521,467 |
| Plus Λb energy ≥9 GeV | 54,134 | 3,254 | 55,158 | 272,385 | 251,084 |

The energy cut retains 99.65% of direct Physics candidates and 43.99% of
nonmatched Zbb candidates, conditional on the mass-window sample. It retains
99.37% of Physics candidate-bearing events and 48.15% of Zbb
candidate-bearing events. Relative to all processed input events, the direct
signal candidate rate is 54,134/100,000 and the nonmatched Zbb candidate
rate is 272,385/76,222,397. These are not physical expected yields.
On a capped 1,000-output-event preparation, the named JSON scenario applied
through `derive_offline_scenario.py` reproduced the study script's candidate
counts exactly: 1,008 Physics and 266 Zbb candidates. This checks that the
saved-table comparison matches the configured cut semantics.

The full [kinematics](../outputs/analysis/studies/v3_offline_inspection_20261002/reference_mass5_lbE9/plots/kinematics_1.png),
[recoil](../outputs/analysis/studies/v3_offline_inspection_20261002/reference_mass5_lbE9/plots/recoil_1.png),
and photon-/Λ⁰-centered activity pages for all six cones are in `plots/`.
The [single-variable scan](../outputs/analysis/studies/v3_offline_inspection_20261002/reference_mass5_lbE9/single_variable_cut_scan.csv)
includes the derived ratios. After the energy cut, photon-centered R03
all-energy/Eγ ≤1.084 retains 99.00% of the remaining direct candidates
and 40.27% of the remaining nonmatched Zbb candidates. All scan thresholds
are derived and evaluated on this same sample, so they are exploratory.

## Same-hemisphere diphoton masses, no veto applied

The [diphoton diagnostic plot](../outputs/analysis/studies/v3_offline_inspection_20261002/reference_mass5_lbE9/plots/diphoton_min_and_veto_windows.png)
shows the minimum partner `m(γγ)`, nearest distance to π⁰ and η masses, and
the no-partner fraction after the mass and energy selections. The selected
candidate photon is paired with other raw type-22 photons on the fitted Λ⁰
hemisphere. Candidates with no eligible partner have `min_pair = +inf` and
are retained.

Among the energy-selected candidates, 4,398/54,134 direct Physics and
85/272,385 nonmatched Zbb candidates have no eligible partner. A π⁰-window
partner (±20 MeV) occurs for 1,517 direct Physics and 160,257 nonmatched
Zbb candidates; an η-window partner (±50 MeV) occurs for 10,601 and
154,641 respectively. The union occurs for 11,591 direct Physics and
224,274 nonmatched Zbb candidates. These are diagnostic potential veto
effects; **no veto has been applied**. `min_pair` alone does not define the
veto, because a second or later partner can lie in a mass window even when
the minimum partner mass does not.

## PI review point

The joint scan uses the unchanged fit-range Stage 1 baseline: 55,395 direct
Physics candidates, 4,508 wrong Physics combinations, and 979,293 nonmatched
Zbb candidates from 100,000 Physics and 76,222,397 Zbb processed input
events. It applies only reconstructed Λ⁰ mass and Λb energy cuts. The
[scan CSV](../outputs/analysis/studies/v3_offline_inspection_20261002/joint_mass_energy_scan/fixed_energy_grid.csv)
and [frontier plot](../outputs/analysis/studies/v3_offline_inspection_20261002/joint_mass_energy_scan/joint_frontier.png)
give conditional and cumulative candidate comparisons on identical events.

| Λ⁰ half-window | Minimum Λb energy | Direct signal / 55,395 | Nonmatched Zbb / 979,293 | Zbb events / 76,222,397 |
|---:|---:|---:|---:|---:|
| ±5 MeV | 9 GeV | 54,134 (97.72%) | 272,385 (27.81%) | 251,084 |
| ±10 MeV | 9 GeV | 54,882 (99.07%) | 343,724 (35.10%) | 313,815 |
| ±12.5 MeV | 10.5 GeV | 54,872 (99.06%) | 214,554 (21.91%) | 199,782 |
| ±15 MeV | 11 GeV | 54,913 (99.13%) | 194,499 (19.86%) | 181,169 |

The ±5 MeV window alone retains only 98.07% of fit-range Stage 1 direct
candidates; no energy threshold can meet a joint 99% target with it. The
strongest numerical point among the scanned windows at 99% uses ±15 MeV
and `E(Λb) ≥ 11.37535 GeV`, leaving 170,026 Zbb candidates, but ±15 MeV
is Stage 1's existing window rather than a new mass restriction, and the
threshold is fitted on the same sample. A simple **named study option** with
both cuts is ±12.5 MeV and `E(Λb) ≥ 10.5 GeV`. It reduces the Zbb candidate
count by 78.09% relative to fit-range Stage 1 while retaining 99.06% of
direct Physics candidates. It is saved as
`lambda12p5_lbE10p5_same_hemi_all` in the JSON, with selected full-column
Parquets and LHCb-style plots under `reference_mass12p5_lbE10p5/`.

For that named option, the ±12.5 MeV mass cut alone leaves 55,264 direct
Physics candidates and 889,560 nonmatched Zbb candidates in 730,051 Zbb
events. The energy cut then retains 54,872/55,264 = 99.29% of those direct
candidates and 214,554/889,560 = 24.12% of those Zbb candidates. This gives
both the conditional and cumulative losses on the same frozen inputs.

The candidate retention uses Stage 1 fit-range direct candidates as its
denominator; the selected direct-candidate rate per originally generated
Physics event is 54,872/100,000. Zbb event retention is a separate quantity:
199,782 candidate-bearing events / 76,222,397 processed Zbb input events.
These rates are not final signal or background yields and no photon veto or
BDT has been applied. Thresholds were chosen and evaluated on the same
available 191 of 1,200 Zbb chunks. The PI has now made the ±12.5 MeV,
`E(Λb) ≥ 10.5 GeV` no-veto option the offline default for the next training
study; the full campaign and held-out chunks are still needed to measure its
final background performance. The older ±5 MeV scenario remains available
for comparison. Photon-partner diagnostics are preserved as BDT inputs and
for later veto comparisons.

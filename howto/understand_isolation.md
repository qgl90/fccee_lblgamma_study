# Stage 1 photon and Λ⁰ isolation: calculation and saved branches

This describes the current Stage 1 implementation in
[`lb_candidate_observables.h`](../analysis/studies/lb_candidate_observables.h),
the branch mapping in
[`observables_stage1.py`](../analysis/studies/observables_stage1.py), and the
cone values in [`lb_observables.json`](../config/lb_observables.json).
Observables are calculated **after** Λb→Λ⁰γ candidates are built. There is
one value per candidate in each output vector; these fields do not select
candidates during Stage 1. The calculation uses reconstructed objects and
does not consult truth labels.

## Same-hemisphere activity sums

For every Λb candidate, Stage 1 builds two sets of cones: one centered on
the **candidate photon** (`iso_RXX_*`), and one centered on the **fitted Λ⁰
momentum direction** (`lambda0_iso_RXX_*`). The same reconstructed event
objects are tested against both centers. The code:

1. Keeps only objects on the fitted Λ⁰ side of the **original full-event
   thrust axis**: `(thrust · p_Λ) × (thrust · p_object) > 0`. The Λ⁰ momentum
   used here comes from the candidate fit. A zero projection fails the strict
   comparison. This is the event thrust stored by the candidate builder,
   which includes candidate objects, rather than the separate ROE thrust.
2. Requires finite reconstructed `px`, `py`, `pz`, and energy; then requires
   `ΔR(center, object) < cone radius`. The center and object
   directions use `η = asinh(pz / hypot(px,py))`, `φ = atan2(py,px)`, and the
   wrapped difference in φ. Objects with undefined η do not enter a cone.
3. Classifies all entries of `ReconstructedParticles` by reconstructed
   charge: `charged` if `charge != 0`, otherwise `neutral`. This does not
   restrict activity to selected tracks or selected photons.
4. Removes the candidate **proton and pion** from `charged`, the candidate
   **photon** from `neutral`, and **all three** from `all`. These rules are
   the same for photon-centered and Λ⁰-centered cones. The fitted Λ⁰ is not
   an extra reconstructed-particle entry; its daughters are removed by their
   indices. Other reconstructed photons remain eligible.

The six radii are set in the JSON configuration:

| Branch radius | ΔR radius |
| --- | ---: |
| `R02` | 0.2 |
| `R03` | 0.3 |
| `R05` | 0.5 |
| `R07` | 0.7 |
| `R10` | 1.0 |
| `R20` | 2.0 |

The earlier 7.0-wide `R70` cone is replaced by `R20` in new Stage 1 output;
old tuples still contain `R70` and cannot be interpreted as `R20`. All
radius comparisons are strict `<`; cones are nested, so an object can
contribute to several saved cones.

For each radius `RXX`, each center prefix (`iso` or `lambda0_iso`), and each
class (`all`, `charged`, or `neutral`), Stage 1 saves:

| Branch pattern | Meaning | Unit |
| --- | --- | --- |
| `{iso,lambda0_iso}_RXX_CLASS_px`, `_py`, `_pz` | Components of the **vector sum** of included reconstructed momenta | GeV |
| `{iso,lambda0_iso}_RXX_CLASS_p` | Magnitude `sqrt((Σpx)² + (Σpy)² + (Σpz)²)` of that sum | GeV |
| `{iso,lambda0_iso}_RXX_CLASS_energy` | Scalar sum `ΣE` of included reconstructed energies | GeV |
| `{iso,lambda0_iso}_RXX_CLASS_n` | Number of included reconstructed objects | count |

For example, `iso_R05_neutral_energy` is the total energy of neutral
reconstructed objects within ΔR < 0.5 of the candidate photon, on the
fitted Λ⁰ hemisphere, excluding the candidate photon. By contrast,
`lambda0_iso_R05_charged_energy` is charged activity within ΔR < 0.5 of
the fitted Λ⁰ direction, excluding its proton and pion. `p` is **not** the
sum of individual momentum magnitudes or transverse momenta. For the
component sums, energy, and count, `all = charged + neutral` up to floating
point rounding. In general, `all_p` is not `charged_p + neutral_p` because
it is computed after vector addition. Empty activity gives zero sums and
zero count.

### Charged-object impact parameters

Each radius also has these charged-only branches:

| Branch pattern | Meaning | Unit |
| --- | --- | --- |
| `{iso,lambda0_iso}_RXX_charged_d0_min`, `_d0_max` | Minimum and maximum **signed** PV-adjusted `d0` | mm |
| `{iso,lambda0_iso}_RXX_charged_absd0_min`, `_absd0_max` | Minimum and maximum absolute PV-adjusted `d0` | mm |
| `{iso,lambda0_iso}_RXX_charged_n_d0` | Number of included charged objects with a finite computable `d0` | count |

These use the **first linked** `EFlowTrack_1` track of each charged object,
only when the candidate PV is valid. The stored value is
`track.D0 + PV_x sin(track.phi) − PV_y cos(track.phi)`. Thus `n_d0` can be
smaller than `charged_n`; it counts objects with usable first tracks, not all
linked tracks. If `n_d0 = 0`, each of the four extrema is `-999`, even if
there are charged objects in the cone. These fields are distances, not `d0`
significances.

There are 23 fields per cone: six metrics for each of three charge classes,
plus five charged `d0` metrics. Across six cones and two centers this gives
**276 activity branches**. Each branch is an event-level vector aligned with the
Stage 1 candidate slots; downstream one-candidate-per-row tables flatten
those vectors into columns.

## Older `iso_*` ratio branches have a different definition

The older branches remain in the Stage 1 output for compatibility. They
exclude the candidate photon but **do not require the fitted Λ⁰ hemisphere**.
They are ratios, unlike the new activity sums:

| Branches | Numerator / denominator | Candidate proton and pion included? |
| --- | --- | --- |
| `iso_R02`, `iso_R03`, `iso_R05` | `ΣpT / pT(candidate γ)` within the named cone | Yes |
| `iso_R02_E`, `iso_R03_E`, `iso_R05_E` | `ΣE / E(candidate γ)` within the named cone | Yes |
| `iso_R03_noLambda`, `iso_R05_noLambda` | `ΣpT / pT(candidate γ)` | No |
| `iso_R03_noLambda_E`, `iso_R05_noLambda_E` | `ΣE / E(candidate γ)` | No |
| `iso_charged`, `iso_neutral` | Charge-class `ΣpT / pT(candidate γ)` within R03 | No |
| `iso_charged_E`, `iso_neutral_E` | Charge-class `ΣE / E(candidate γ)` within R03 | No |

Here `pT = hypot(px,py)`. A zero or invalid denominator returns `-999`.
`iso_delphes = -999` and `iso_delphes_available = 0`: the pinned IDEA
EDM4hep output does not provide the Delphes `IsolationVar` branch. Also,
`n_photons_DR03` and `n_photons_DR05` count other **selected** photons in
both hemispheres; they are separate from the new neutral-object count.

The `gamma_combo_same_hemi_all_*` and
`gamma_combo_same_hemi_selected_*` di-photon lists use the fitted Λ⁰
hemisphere, but have no isolation-cone radius restriction. They are partner
mass/index lists for photon veto studies, not isolation sums. See
[`STAGE1_OBSERVABLES.md`](../studies/reconstruction/STAGE1_OBSERVABLES.md)
for the other candidate observables, and [`stage2.md`](stage2.md) for
downstream preservation of Stage 1 columns.

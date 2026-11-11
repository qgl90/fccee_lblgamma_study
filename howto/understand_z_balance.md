# Stage 1 Z energy and momentum balance variables

Stage 1 assumes a center-of-mass four-vector
`P_Z = (px,py,pz,E) = (0,0,0,91.2 GeV)` from
[`lb_observables.json`](../config/lb_observables.json). The quantities are
calculated per reconstructed Λb→Λ⁰γ candidate in
[`lb_candidate_observables.h`](../analysis/studies/lb_candidate_observables.h).

`P_sig` is the fitted Λ⁰ four-vector plus the candidate's reconstructed
photon four-vector. The Λ⁰ energy is recomputed from its fitted momentum and
reconstructed mass. The candidate proton, pion, and photon are excluded from
the rest-of-event sums, so they are not counted twice.

`P_opp` is the sum of other reconstructed particles on the **opposite** side
of the original event thrust axis from the fitted Λ⁰ direction. `P_ROE` is
the sum of all other reconstructed particles, in both hemispheres. The code
forms:

| Saved field | Definition | Unit |
|---|---|---|
| `z_partial_deltaE` | `E_sig + E_opp − 91.2` | GeV |
| `z_partial_px,py,pz` | `p_sig + p_opp` components | GeV |
| `z_partial_deltaP` | `|p_sig + p_opp|` | GeV |
| `z_full_deltaE` | `E_sig + E_ROE − 91.2` | GeV |
| `z_full_px,py,pz` | `p_sig + p_ROE` components | GeV |
| `z_full_deltaP` | `|p_sig + p_ROE|` | GeV |

“Partial” means that other activity on the candidate's hemisphere is omitted.
It is an intentionally incomplete event balance, so even a genuine signal
candidate is **not expected to have `z_partial_deltaE = 0` or
`z_partial_deltaP = 0`**. It may still separate candidates because a true
high-energy Λb candidate plus the opposite hemisphere captures a different
fraction of the collision than a combinatorial low-energy candidate.

“Full” includes the remaining reconstructed event. An ideal fully visible
Z event at rest would have both full residuals close to zero. Detector losses,
neutrinos, reconstruction response, beam effects, and incorrect candidate
assignment broaden or shift them. `deltaP` is a nonnegative momentum
magnitude, while the stored `px,py,pz` retain the signed components. These
variables use reconstructed objects only; no truth identity enters them.

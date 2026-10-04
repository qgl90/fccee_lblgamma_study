# PI review: angular acceptance after the proposed Armenteros veto

**Question.** If the reconstructed Armenteros box proposed to reject
\(K^0_S\to\pi\pi\) pairs is applied **after** the frozen v3 BDT, what
additional loss and angular response does it produce on 100k PHSP
\(\Lambda_b\to\Lambda\gamma\) events? This is a no-PID veto scenario for
inspection, not an adopted reference cut.

## Inputs and selection

The denominator is the same **100,007 generated direct PHSP decays** in
100,000 input events as the [baseline acceptance review](STAGE2_V3_PHSP_ANGLE_REVIEW_2026-10-04.md).
Stage 1, offline selection, and the frozen 1,028-chunk BDT score
\(\geq0.9787055254\) are unchanged. The post-BDT table is
`/eos/lhcb/lbdt3/user/rquaglia/fcc_ee/lblgamma/outputs/stage2_v3_phsp_100k_bdt1028/stage2/bdt_selected/signal_phsp_v3_-2.parquet`.
The [post-BDT Zbb ancestry study](STAGE2_V3_ARMENTEROS_REVIEW_2026-10-03.md)
defines the additional reconstructed-only veto: reject a candidate if
**0.67≤|α|≤0.78 and 0.075≤qT≤0.120 GeV**, inclusive at the bounds.
The fitted proton/pion momenta supply α and qT; no truth or PID enters
the cut. Generated truth and full ancestry label candidates only after
selection. The same candidate table reproduces all ten baseline BDT bins
before the veto.

## Measured effect

| Stage | Direct candidate rows | Unique direct decays | Cumulative / 100,007 generated direct decays | Conditional from BDT |
|---|---:|---:|---:|---:|
| Frozen BDT, no Armenteros veto | 26,436 | 26,429 | 26.43% | 100% |
| BDT plus proposed box veto | 20,155 | 20,149 | 20.15% | 76.24% |

The veto removes 6,281 direct candidate rows and 6,280 unique direct decays.
After it, 10,111 \(\Lambda_b\) and 10,038 anti-\(\Lambda_b\) generated
decays have a surviving fully matched candidate. The
[acceptance and conditional-retention figure](figures/stage2_v3_phsp_armenteros_100k_bdt1028/cos_theta_p_acceptance_armenteros.png)
shows that its signal cost is highly angle dependent: retention is **98.6%**
for \(-1\leq\cos\theta_p<-0.8\), **43.8%** for
\(0.2\leq\cos\theta_p<0.4\), and 88.9% for the highest bin.
The absolute post-veto acceptance ranges from 38.3% in the most negative
bin to 8.80% at \(0.2\leq\cos\theta_p<0.4\). The
[charge-separated figure](figures/stage2_v3_phsp_armenteros_100k_bdt1028/cos_theta_p_acceptance_by_charge.png)
checks both conjugates.

For 20,149 unique selected decays, reconstructed minus truth
\(\cos\theta_p\) has median \(-5.94\times10^{-6}\), central 68% half-width
0.01191 and RMS 0.09011; 6.35% have |Δ|>0.1. The
[migration figure](figures/stage2_v3_phsp_armenteros_100k_bdt1028/cos_theta_p_migration_armenteros.png)
and [response JSON](data/stage2_v3_phsp_armenteros_100k_bdt1028/acceptance_resolution.json)
give truth rows and reconstructed columns, normalized per generated decay
in each truth bin. Fit the generated angle shape through this response if
the veto is adopted. The [fit CSV](data/stage2_v3_phsp_armenteros_100k_bdt1028/cos_theta_p_acceptance_for_fit.csv)
has exact bin counts and conditional retention.

The original Zbb study suggested substantial \(K^0_S\) suppression but
also found a roughly 20% direct-signal loss. This PHSP check finds an even
larger **23.8%** loss under the same frozen BDT and a pronounced angular
distortion. The box was chosen after inspecting the Zbb sample, so its
background rejection still needs fresh validation. Before adopting it,
compare the alternative reconstructed \(\pi\pi\)-mass hypothesis veto,
and assess the change in angular-fit precision and bias with this response.
The selection and outputs are reproducible via
[the how-to](../howto/v3_phsp_armenteros_acceptance.md).

## Results and figures

- [Baseline versus post-veto acceptance and conditional retention](figures/stage2_v3_phsp_armenteros_100k_bdt1028/cos_theta_p_acceptance_armenteros.png)
- [Post-veto acceptance by charge](figures/stage2_v3_phsp_armenteros_100k_bdt1028/cos_theta_p_acceptance_by_charge.png)
- [Post-veto truth-to-reco migration](figures/stage2_v3_phsp_armenteros_100k_bdt1028/cos_theta_p_migration_armenteros.png)
- [Fit CSV](data/stage2_v3_phsp_armenteros_100k_bdt1028/cos_theta_p_acceptance_for_fit.csv), [full response JSON](data/stage2_v3_phsp_armenteros_100k_bdt1028/acceptance_resolution.json), and [selected-decay table](data/stage2_v3_phsp_armenteros_100k_bdt1028/selected_direct_resolution.parquet)

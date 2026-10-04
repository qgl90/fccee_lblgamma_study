# PI review: 100k Λπ⁰ and Λη physics backgrounds through v3 BDT

**Question.** How often do forced \(\Lambda_b\to\Lambda\pi^0(\gamma\gamma)\)
and \(\Lambda_b\to\Lambda\eta(\gamma\gamma)\) appear as one-photon
\(\Lambda_b\to\Lambda\gamma\) candidates after the current v3 Stage 1,
named offline cuts and fixed BDT score? What yields follow from explicit
parent and daughter branching-fraction scenarios in the provisional
5.4–5.9 GeV signal window? No π⁰ or η veto is enabled.

## Independent 100k generation and reconstruction

Ten 10k chunks per physics model were generated with independent seeds
71801–71810 (π⁰) and 71901–71910 (η), then merged with the repository
Snakemake chain. The [reproduction guide](../howto/v3_pseudoscalar_backgrounds_100k.md)
gives the commands. The complete generator audit finds **100,005** direct
Λπ⁰(γγ) decays (49,965 Λb, 50,040 anti-Λb) and **100,000** direct
Λη(γγ) decays (49,808 Λb, 50,192 anti-Λb), in 100,000 input events each.
The π⁰ generated mean cos θp is −0.19260 ± 0.00172; η is
+0.16013 ± 0.00176. These check the named HELAMP generator scenarios,
not a measurement of their physical angular models. The generated audit
plots are linked below.

The card is `cards/card_IDEA.tcl`, SHA256
`11d81b4ee2bafa33e0715c4a390d235e38487521ce8e43bdb360890c9e8ec3d3`.
The decay files are `evtgen/Lb2LambdaPi0.dec`, SHA256
`ca8b154eb122ce01d540ca28cf8b5498a4fde504b61bdf034b4fa`, and
`evtgen/Lb2LambdaEtaPhysics.dec`, SHA256
`8b79147f78c656a9b75cad399648cb4e027a44eee7b1311207cb2af6ebaf4b3b`.
The two merged EDM4hep SHA256 values are
`60b1309b579e8169fbe983b77c78a37df4ef76f35a42637597ba1f818019ec7f`
(π⁰) and
`72e75e64b5361a40dbf5efb0619a3795425ba8cf520f8c5b596c95b7145f5d15`
(η). They are archived under
`/eos/lhcb/lbdt3/user/rquaglia/fcc_ee/lblgamma/outputs/stage0_v3_pseudoscalar_physics_100k_20261004/`.
Other Stage 0 SHA256 values are Pythia card
`3fae9b7cd90c8ce5436ec6dd254f54d91fb0cb73f1ea7805c1551b3b359f8a09`,
EDM4hep mapping card
`e834548595517fa2ea9fbc25dd96b9c408507c6cabc61da8feb1cbada8624982`,
inclusive `evtgen/DECAY.DEC`
`ac3161823b4e69a2d2629a7174484682083abe52c361558bcb07ef0a7ca0f799`,
and particle table `evtgen/evt.pdl`
`b337e3a332ed3d25d688f466cf3e57752d3609a1a3be41b1c6bb6cb283d5dd1a`.

Both samples used the same one-photon v3 Stage 1 runner and
`config/lb_reco_preselection_15mev_45_65_3d.json` (SHA256
`b872906ad0b25f94299c2ba627b0804d558c407134ca01f3e212c638e6cffa18`),
with eight RDataFrame threads per sample and no event limit. The pinned
FCCAnalyses revision is `0315db1e2941e2886813cb645193e348f3863d5d`.
The reconstructed candidate builder does not use MC identity. The v3
Stage 1 ROOT tuples are archived separately under
`/eos/lhcb/lbdt3/user/rquaglia/fcc_ee/lblgamma/outputs/stage1_v3_pseudoscalar_physics_100k_20261004/`.
Their SHA256 values are
`09605c1f32e029290c434d9c3aa230248cefe250cd063a0e54fd74992d819803`
(π⁰) and
`84f31a21353a9dde3d7cd33941d1e2aac92e5781f6500ee87c64217a7cdade2e`
(η); the local and EOS copies match byte for byte.

The offline scenario is `lambda12p5_lbE10p5_same_hemi_all`: reconstructed
Λ mass within 12.5 MeV, Λb energy ≥10.5 GeV, same hemisphere, no explicit
π⁰ or η veto. The same [1,091-chunk v3 BDT proposal](STAGE2_V3_BDT_PEAK_REVIEW_2026-10-04.md)
scores both samples at **≥0.9538269639**; its model SHA256 is
`e2890376c7738ca1010758bee765aa62f2425d9c18e2522f08f3b77004de5b66`.
The 20 score inputs are reconstructed variables; the pair-distance inputs
may respond to a second photon, even though no explicit meson veto is made.
Truth and ancestry classify candidates only *after* the cuts.
The complete Stage 2 audit, offline and BDT Parquet tables are archived at
`/eos/lhcb/lbdt3/user/rquaglia/fcc_ee/lblgamma/outputs/stage2_v3_pseudoscalar_physics_100k_bdt1091peak/`.
Their manifest SHA256 values are
`7709e3bba1682e32ecd0ee5c1d844761dd44d8e738be7125edd8195a73072c5e`
(π⁰) and
`e3eab87c373da3097919d0d1463c5b5daded103a10328c3469db58f83acc9954`
(η), matched between scratch and EOS copies.

## Stage counts and peaking-region behaviour

These are candidate rows; generated decays, input events and candidate-bearing
events are recorded separately in the linked JSON summaries. “Direct
partial” means the fitted Λ daughters and chosen photon trace to the same
generated Λb, with the photon from the generated π⁰ or η. Wrong/unmatched
includes other combinations and incomplete associations.

| Stage | η physics all / direct partial | π⁰ physics all / direct partial | η conditional all | π⁰ conditional all |
|---|---:|---:|---:|---:|
| Stage 1 | 44,717 / 39,568 | 48,298 / 37,964 | — | — |
| Offline selected | 35,267 / 32,675 | 39,639 / 31,833 | 78.87% | 82.07% |
| Fixed BDT | 11,125 / 11,042 | 11,512 / 7,988 | 31.55% | 29.04% |

The corresponding **candidate-bearing event** counts, out of 100,000 input
events per mode, are 41,752 → 34,072 → 11,123 for η and
45,104 → 38,237 → 11,506 for π⁰ (Stage 1 → offline → BDT).
These event counts are not interchangeable with candidate rows or with
the generated-decay denominators in the yield formula.

In **5.4–5.9 GeV** after the BDT, η has **3,120 candidate rows in
3,118 events**: 3,099 direct partial and 21 wrong/unmatched rows.
π⁰ has **5,937 rows in 5,937 events**: 2,519 direct partial and 3,418
wrong/unmatched. The latter dominate its surviving peak candidates in
this forced sample. The [η mass and angle](figures/stage2_v3_pseudoscalar_100k_bdt1091peak/eta_physics_post_bdt_mass_angle.png)
and [π⁰ mass and angle](figures/stage2_v3_pseudoscalar_100k_bdt1091peak/pi0_physics_post_bdt_mass_angle.png)
show both truth categories rather than hiding the combinatorial component.
The stage-by-stage mass distributions are linked in the results list.

## Physical scale and its limits

The [branching scenario config](../config/v3_pseudoscalar_branching_scenarios.json)
uses \(N_Z=6\times10^{12}\), \(\mathcal B(Z\to b\bar b)=0.15\),
\(f_{\Lambda_b}=0.10\) per b quark, and
\(\mathcal B(\Lambda\to p\pi)=0.639\), matching the signal projection.
For each forced mode the expected *candidate* count is

\[
N_Z\,\mathcal B(Z\to b\bar b)\,2f_{\Lambda_b}\,
\mathcal B(\Lambda_b\to\Lambda P)\,
\mathcal B(\Lambda\to p\pi)\,\mathcal B(P\to\gamma\gamma)
\frac{N_{\rm selected\ candidate\ rows}}{N_{\rm generated\ direct\ decays}}.
\]

The η parent branching input **\((9.3^{+7.3}_{-5.3})\times10^{-6}\)**
is the [LHCb evidence result](https://arxiv.org/abs/1505.03295).
The π⁰ parent input **\(1.58\times10^{-8}\)** is the \(N_c^{\rm eff}=3\)
[Mohanta–Giri–Khanna theory benchmark](https://arxiv.org/pdf/hep-ph/0006109),
with their 1.2–3.22×10⁻⁸ variants shown as a scenario range. The
two-photon fractions are 0.3936 for [η](https://pdg.lbl.gov/2025/listings/rpp2025-list-eta.pdf)
and 0.98823 for [π⁰](https://pdg.lbl.gov/2025/listings/rpp2025-list-pi-zero.pdf).
Those daughter fractions must be applied because the EvtGen files force
the γγ chains.

| Mode | BDT MC candidates in peak / generated direct decays | Projected candidates in peak | Parent-BR scenario range | Projected per parent BR of 10⁻⁶ |
|---|---:|---:|---:|---:|
| Λη physics | 3,120 / 100,000 | **13,136** | 5,650–23,447 | 1,412 |
| Λπ⁰ physics | 5,937 / 100,005 | **107** | 81–217 | 6,748 |

Approximate 95% MC candidate-count intervals at fixed branching inputs
are 12,679–13,605 for η and 104–109 for π⁰. They exclude candidate
correlations, production, detector, BDT and branching-fraction uncertainties.
The [expected mass overlay](figures/stage2_v3_pseudoscalar_100k_bdt1091peak/expected_mass_comparison.png)
places these estimates alongside the fixed-score independent-test signal
(300,245) and inclusive nonmatched Zbb (628,461) projections in the same
peak window. The inclusive Zbb tail has only 56 test candidates, so its
binned mass shape is visibly sparse. **Do not add** the forced η/π⁰ yields
to inclusive Zbb without checking overlap: inclusive Zbb can already
contain these modes. The forced samples provide their shape and conditional
rate, while the physical scale is conditional on the stated branching
scenario.

The existing 100k η **PHSP** sample, scored with the same model, gives
3,492 peak BDT candidates and 14,702 projected candidates under the
same η branching value. Its [separate shape](figures/stage2_v3_pseudoscalar_100k_bdt1091peak/eta_phsp_post_bdt_mass_angle.png)
and [summary](data/stage2_v3_pseudoscalar_100k_bdt1091peak/eta_phsp_summary.json)
show the sensitivity to the generated angular model; the HELAMP physics
sample is the requested primary scenario. Before a final background fit,
the PI should settle the signal peak window, parent branching inputs and
whether to model these shapes explicitly or from inclusive Zbb, then
check the possible overlap and BDT mass sculpting.

## Results and figures

- [Generated Λη HELAMP angle](figures/stage2_v3_pseudoscalar_100k_bdt1091peak/eta_physics_generated_angle.png) and [generated Λπ⁰ HELAMP angle](figures/stage2_v3_pseudoscalar_100k_bdt1091peak/pi0_physics_generated_angle.png)
- [η physics mass cutflow](figures/stage2_v3_pseudoscalar_100k_bdt1091peak/eta_physics_mass_cutflow.png) and [π⁰ physics mass cutflow](figures/stage2_v3_pseudoscalar_100k_bdt1091peak/pi0_physics_mass_cutflow.png)
- [η physics post-BDT mass and angle](figures/stage2_v3_pseudoscalar_100k_bdt1091peak/eta_physics_post_bdt_mass_angle.png) and [π⁰ physics post-BDT mass and angle](figures/stage2_v3_pseudoscalar_100k_bdt1091peak/pi0_physics_post_bdt_mass_angle.png)
- [η branching-scaled mass](figures/stage2_v3_pseudoscalar_100k_bdt1091peak/eta_physics_post_bdt_expected_mass.png), [π⁰ branching-scaled mass](figures/stage2_v3_pseudoscalar_100k_bdt1091peak/pi0_physics_post_bdt_expected_mass.png), and [signal/Zbb/forced-mode comparison](figures/stage2_v3_pseudoscalar_100k_bdt1091peak/expected_mass_comparison.png)
- [η PHSP cross-check mass and angle](figures/stage2_v3_pseudoscalar_100k_bdt1091peak/eta_phsp_post_bdt_mass_angle.png) and [its stage cutflow](figures/stage2_v3_pseudoscalar_100k_bdt1091peak/eta_phsp_mass_cutflow.png)
- [η PHSP branching-scaled mass](figures/stage2_v3_pseudoscalar_100k_bdt1091peak/eta_phsp_post_bdt_expected_mass.png)
- [Generated audits, per-stage counts, branching projection, comparison JSON and study manifest](data/stage2_v3_pseudoscalar_100k_bdt1091peak/)
- [Beamer PI review deck](../presentations/stage2_v3_pseudoscalar_100k_bdt1091peak/stage2_v3_pseudoscalar_100k_bdt1091peak.pdf)

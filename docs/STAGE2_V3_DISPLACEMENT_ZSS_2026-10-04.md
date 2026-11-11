# PI review: post-BDT Λ displacement and Zss

## Question and comparison

Would an additional reconstructed displacement requirement suppress the Zss
background that remains after the frozen v3 BDT, Armenteros box, π⁰ veto and
η veto proposals? This is a **paired, exploratory** scan on the same archived
candidate rows. It does not change candidate building, the BDT or the reference
selection. The comparison uses the 5.4–5.9 GeV reconstructed Λγ peak.

The score is ≥0.9538269639015198 from the 1,091-chunk Zbb peak model. The
Stage 1/offline preselection is Λ mass within 12.5 MeV, Λb energy ≥10.5 GeV,
and same hemisphere. The Armenteros box rejects
`0.67 ≤ |alpha| ≤ 0.78` and `0.075 ≤ qT ≤ 0.120 GeV`; π⁰ and η veto windows
are 20 and 50 MeV. We compare a lower threshold on the absolute reconstructed
Λ trajectory impact-parameter significance, `|lambda_d0_sig|`, against the
same baseline. A PV-to-Λ-SV 3D flight-significance threshold is a control.
Neither cut uses MC identity. Truth is attached only for the diagnostic pair
origin and direct-signal classification after reconstruction.

Inputs are the 100k forced direct signal, 1,091/1,200 Zbb chunks, and all
1,200/1,200 v3 Zcc and Zss chunks. The latter contain 499,786,495 and
499,842,440 processed input events. The exact paths, hashes, commands,
denominators, and output names are frozen in the [JSON result](data/stage2_v3_displacement_zss_1091peak/displacement_scan.json)
and [reproduction guide](../howto/v3_displacement_zss.md). The score, model,
catalog and row counts are checked by the script.

## Results

These are **candidate rows in the peak**, not unique generated decays. Each
threshold is conditional on the unchanged four-step baseline; the latter is
already cumulative from Stage 1 and BDT. Direct-signal rows are truth matched
only for reporting. The Zss pair-origin column is a post-selection truth audit.

| Additional `|lambda_d0_sig|` minimum | Direct signal | Zbb | Zcc | Zss | True Λ in Zss | Central S/√(S+B) | Central S/(S+B) |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 0, baseline | 23,849 | 27 | 252 | 514 | 483 | 154.8 | 12.3% |
| 3 | 18,395 | 23 | 112 | 203 | 192 | 174.1 | 20.2% |
| 5 | 15,686 | 21 | 63 | 132 | 123 | 178.7 | 24.9% |
| 8 | 12,745 | 16 | 46 | 86 | 81 | 171.6 | 28.3% |

At 5, conditional direct-signal retention is 65.8%; Zss retention is 25.7%,
Zcc 25.0%, and Zbb 77.8%. For true-Λ Zss pairs it is 123/483 = 25.5%.
The corresponding central projected peak candidates are signal 194,757→128,096;
Zbb 61,422→47,773; Zcc 363,943→90,986; Zss 962,511→247,182. These use
6×10¹² Z, B(Zbb)=0.15, B(Zcc)=0.1203, and **assumed** B(Zss)=0.156, the
down-type average, with processed-event denominators. The significance and
purity columns use `B = Zbb + Zcc + Zss`, all in the same peak. Forced Λη and
Λπ⁰ are separate because their projections may overlap inclusive Zbb: their
raw peak rows change 457→310 and 3,321→2,416 at 5.

The 3D flight-significance cut does not help here. A threshold of 100 retains
19,722/23,849 signal and 444/514 Zss peak rows; its central counting metric
falls to about 138. The BDT already uses `lambda_flight_xyz_sig` as a feature,
whereas `lambda_d0_sig` is absent from the frozen feature list. This explains
why the second observable can add discrimination, although it does not establish
that it would improve a retrained model.

Figures:

- [Displacement scan and flight-significance control](figures/stage2_v3_displacement_zss_1091peak/displacement_retention_linear.png)
- [Paired linear-scale mass and cos θp distributions, baseline and threshold 5](figures/stage2_v3_displacement_zss_1091peak/mass_angle_d0sig5_linear.png)
- [Machine-readable scan CSV](data/stage2_v3_displacement_zss_1091peak/displacement_scan.csv)

## Limitations and PI decision

The threshold was inspected on these same samples. The central peak objective
is descriptive, not an independently validated optimum. Zbb has only 21 rows
at threshold 5 and its counting interval is broad. Branching fractions,
fragmentation, response and reconstruction uncertainties are absent from the
counting intervals. The Λ impact-parameter significance uncertainty does not
include Λ direction uncertainty, so a PV/SV and track-resolution scenario
check is required. The cos θp shape changes; the 100k PHSP angular acceptance
and resolution must be recomputed for any chosen threshold, including the
existing Armenteros and photon veto sequence. A frozen independent validation
split and a BDT feature-ablation or retraining study would test whether this
increment survives optimization. **No displacement threshold is adopted here.**

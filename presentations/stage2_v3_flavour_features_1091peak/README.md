# PI deck: v3 three-flavour BDT input comparison

Build from repository root with
`bash presentations/stage2_v3_flavour_features_1091peak/build.sh`.
The 10-page PDF is `stage2_v3_flavour_features_1091peak.pdf`.
Its analysis source is the [PI review](../../docs/STAGE2_V3_FLAVOUR_FEATURES_2026-10-04.md);
the exact command is in [howto](../../howto/v3_flavour_feature_comparison.md).
The [raw histogram JSON](../../docs/data/stage2_v3_flavour_features_1091peak/flavour_feature_comparison.json)
has SHA-256
`029afc9fc2bf3d4a6085d3d006df8f02054e5e578bea02826cb59aa30f211317`.

Frozen Zbb catalog SHA-256:
`40121821162fb42d01ffa60715f1a167b6e6ef5ed31bee405816bf6dcac1a038`.
Projection SHA-256:
`48736dce351ddb0c3c66e0d8b566e6f1de0bacb4013d85f75f4a55784c8c3a5c`.
Zcc and Zss archived Stage 2 summary SHA-256:
`846012b27f5b2e628e2d378fbaf65db9dac05734fa4b160ee58b3b25bd19891d`
and `120dee8780493eae4f28a2dfbf0b55f5e463677a94fe9b14801d28bd818a1761`.

Each figure below is copied byte-for-byte from
`docs/figures/stage2_v3_flavour_features_1091peak/`.

| Deck figure | SHA-256 |
|---|---|
| [Score tail](../../docs/figures/stage2_v3_flavour_features_1091peak/pre_bdt_score_tail.png) | `2741b29f68b28a1d4561b70cebec73c08232da2d9ee611b572d6d53c9b350340` |
| [Peak kinematics](../../docs/figures/stage2_v3_flavour_features_1091peak/pre_bdt_peak_kinematics.png) | `a3df135cec0b7b8a662eeb945ab1c502cfef0a4571bd801afa3bb4ef30b5687f` |
| [Peak topology](../../docs/figures/stage2_v3_flavour_features_1091peak/pre_bdt_peak_topology.png) | `03a4f389a474654fe4343d5097b8bacf85ae0367015ecddae9a482b615101c8d` |
| [Peak activity](../../docs/figures/stage2_v3_flavour_features_1091peak/pre_bdt_peak_activity.png) | `186f8f22270448a3839855b9b02409ac7340dd881a60e9f96e9b81755343eb80` |
| [Survivor topology](../../docs/figures/stage2_v3_flavour_features_1091peak/post_bdt_vetoes_topology.png) | `87e1b589cc39d5e7927e9183f0161eea2076b60188b7ba0547d92a71d2b75b53` |
| [Final mass and angle](../../docs/figures/stage2_v3_flavour_features_1091peak/post_bdt_vetoes_mass_angle_linear.png) | `d65391e7e375a2751d6f05e901ec153fe951fb4aa35ab9cc11020b1d1b9b9204` |

The class-shape slides use unit-normalized candidate distributions. The score
plot has separate class-shape and physically weighted panels. The final
mass/angle plot shows central expected candidate rows on a linear scale.
The Zss normalization uses the explicitly assumed 15.6% down-type average.
The score and vetoes are existing proposals; no mixed model is trained here.

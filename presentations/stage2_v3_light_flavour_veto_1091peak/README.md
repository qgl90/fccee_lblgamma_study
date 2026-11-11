# PI deck: v3 light flavours and veto proposals

Build with `bash presentations/stage2_v3_light_flavour_veto_1091peak/build.sh`
from the repository root. The output is
`stage2_v3_light_flavour_veto_1091peak.pdf` (15 pages). The deck presents
expected candidate rows on a **linear scale**. Its source review is
[`docs/STAGE2_V3_ZCC_ZSS_AND_VETO_REVIEW_2026-10-04.md`](../../docs/STAGE2_V3_ZCC_ZSS_AND_VETO_REVIEW_2026-10-04.md);
reproduce all plots via [`howto/v3_post_bdt_veto_sequence.md`](../../howto/v3_post_bdt_veto_sequence.md).

Frozen Zcc catalog SHA-256:
`d725275fdf52322c6dcbfbe11f6934bc36c346e9f1de130a8419fa4fc60b0dc9`.
Frozen Zss catalog SHA-256:
`fd4f0425e4501ed7ae13ada938c2d908fd0bc15d7964b36ab7214bcfd8323dcc`.
The BDT model SHA-256 is
`e2890376c7738ca1010758bee765aa62f2425d9c18e2522f08f3b77004de5b66`;
the six-component summary SHA-256 is
`9ac4541058c7859474c9c22b05ec2339501d4b762b5ff2f9786a7bb772ed6b62`.

| Deck figure | Original frozen result | SHA-256 |
|---|---|---|
| `sequence_mass_linear.png` | [`docs/figures/stage2_v3_post_bdt_veto_sequence_1091peak_all/`](../../docs/figures/stage2_v3_post_bdt_veto_sequence_1091peak_all/sequence_mass_linear.png) | `15afde858e54691ef35d6ba9432d00c2b4e659ba48cf232587521227d825facf` |
| `sequence_angle_linear.png` | [`docs/figures/stage2_v3_post_bdt_veto_sequence_1091peak_all/`](../../docs/figures/stage2_v3_post_bdt_veto_sequence_1091peak_all/sequence_angle_linear.png) | `32d4166f8590651756187adfbff4f7170e7f82bfba246505ff53b01f3dab952c` |
| `sequence_mass_detail_linear.png` | [`docs/figures/stage2_v3_post_bdt_veto_sequence_1091peak_four/`](../../docs/figures/stage2_v3_post_bdt_veto_sequence_1091peak_four/sequence_mass_detail_linear.png) | `5382f8134a21568e3e850eff6141af3493d7507fe93100c6b5f68538ac31efee` |
| `sequence_angle_detail_linear.png` | [`docs/figures/stage2_v3_post_bdt_veto_sequence_1091peak_four/`](../../docs/figures/stage2_v3_post_bdt_veto_sequence_1091peak_four/sequence_angle_detail_linear.png) | `28046139106c6f93d81df51741687ebc4ba4c1ce0d7a7bf890a1a7ee8437347f` |
| `sequence_mass_pi0_linear.png` | [`docs/figures/stage2_v3_post_bdt_veto_sequence_1091peak_four/`](../../docs/figures/stage2_v3_post_bdt_veto_sequence_1091peak_four/sequence_mass_pi0_linear.png) | `0f216a0370ee8e337099944ecb3ad374b8025e03d91d2d01b817704ab0fc94ed` |
| `zss_peak_pair_origin.png` | [Zss pair-origin result](../../docs/figures/stage2_v3_zss_ancestry_1200_bdt1091peak/zss_peak_pair_origin.png) | `c04d6967f9cabe3f8a61b31afab12b815913e3723345bdbeb37e03871a09e22b` |
| `zss_peak_photon_origin.png` | [Zss photon-origin result](../../docs/figures/stage2_v3_zss_ancestry_1200_bdt1091peak/zss_peak_photon_origin.png) | `e77fb1e2bbca7d2b27e134df7124b50df5d30b36153d62501694add54a3b773e` |
| `zss_peak_photon_source.png` | [Zss photon-parent result](../../docs/figures/stage2_v3_zss_ancestry_1200_bdt1091peak/zss_peak_photon_source.png) | `a95c80526a9b8c7a541f4da6c35f84faf4002a281d12272583ee27130cef03ba` |
| `displacement_retention_linear.png` | [Displacement scan](../../docs/figures/stage2_v3_displacement_zss_1091peak/displacement_retention_linear.png) | `ece7a9f9fd76bd1dafa04db0b44f052c9e7894ed733fda082090553be3cc782c` |
| `mass_angle_d0sig5_linear.png` | [Paired mass and angle](../../docs/figures/stage2_v3_displacement_zss_1091peak/mass_angle_d0sig5_linear.png) | `19c8c48c897cc20150cfdb23da685601087f73e74635a505c3c6bd7f8f6f3e68` |

The all-component curves include Zcc and Zss. The smaller-component slides
use the four-component plot snapshot to make the forced modes and signal
visible under the same physical weights. Forced b-mode projections are never
summed with inclusive Zbb.
The Zss ancestry slides use the [separate frozen truth audit](../../docs/data/stage2_v3_zss_ancestry_1200_bdt1091peak/zss_ancestry.json),
SHA-256 `5f3df8bc0a2ce7b1ca3a03d5729a9955e51e1743ca0f61a95e099c7f09f6973f`.
The displacement slides use the [separate paired scan](../../docs/STAGE2_V3_DISPLACEMENT_ZSS_2026-10-04.md)
and [command](../../howto/v3_displacement_zss.md); its frozen JSON SHA-256 is
`bacf97f883d739587698f4ef97aad24855c9a27ce1e3920cf328331797dc1c64`.

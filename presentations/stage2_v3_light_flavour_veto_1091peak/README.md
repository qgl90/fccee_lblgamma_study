# PI deck: v3 light flavours and veto proposals

Build with `bash presentations/stage2_v3_light_flavour_veto_1091peak/build.sh`
from the repository root. The output is
`stage2_v3_light_flavour_veto_1091peak.pdf` (10 pages). The deck presents
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

The all-component curves include Zcc and Zss. The smaller-component slides
use the four-component plot snapshot to make the forced modes and signal
visible under the same physical weights. Forced b-mode projections are never
summed with inclusive Zbb.

# PI review: PHSP cos θp acceptance and resolution through v3 BDT

**Question.** What efficiency versus *generated* cos θp results when the
100k Λb→Λ⁰(pπ)γ PHSP sample passes the current v3 Stage 1 reconstruction,
named offline selection, and fixed XGBoost score? How far does the
reconstructed angle move from its generated value after all cuts? This is
an efficiency and response input for a later angular fit under this exact
selection scenario. It does not adopt the BDT score as a reference cut.

## Frozen inputs and stage boundaries

- Generator: 100,000 events in
  `/eos/lhcb/lbdt3/user/rquaglia/fcc_ee/lblgamma/outputs/Lb2LambdaGamma_nev100000_IDEA_edm4hep.root`.
  The repository PHSP decay definition is `evtgen/Lb2LambdaGamma.dec`:
  Λb and anti-Λb charge conjugates, Λ→pπ, and PHSP at each forced decay.
  The full generator ancestry audit finds **100,007 direct decays**:
  49,929 Λb and 50,078 anti-Λb. The seven additional decays make
  generated *decays*, rather than input events, the acceptance denominator.
  The EDM4hep file SHA256 is
  `675e4195c1eb892818f96e0df40aacad5c4346608400a541a5ccbf7436fff472`;
  the repository decay definition SHA256 is
  `dffa9b984590b70bd390bf45023fad9265b8bce3df4e26a7318490e99b4eb3da`.
- Stage 1 v3: existing full 100k ROOT tuple
  `/eos/lhcb/lbdt3/user/rquaglia/fcc_ee/lblgamma/outputs/stage1_v3_my_run/signal_phsp.root`
  with `eventsProcessed=100000` and `eventsSelected=56737`. Its full path
  identifies v3 although this historical basename lacks `_v3`. The
  reconstruction config is `config/lb_reco_preselection_15mev_45_65_3d.json`
  (SHA256 `b872906ad0b25f94299c2ba627b0804d558c407134ca01f3e212c638e6cffa18`).
  The ROOT tuple SHA256 is
  `088e38e2ab776f403395e0f2e4b4d121b7a0c5ca1ab9ed3dd69cec79ce57fbe5`.
- Stage 2: `lambda12p5_lbE10p5_same_hemi_all` in
  `config/lb_offline_selections.json` (SHA256
  `c26d246adb0f4e2ddb3ecc4b41b1be10db38b687541989cdd7c7148bf20a1779`):
  reconstructed Λ⁰ ±12.5 MeV, Λb energy ≥10.5 GeV, no photon veto.
- Stage 3: frozen 1,028-chunk model and validation score
  **≥0.9787055254** in [the BDT review](STAGE2_V3_BDT_REVIEW_2026-10-03.md).
  Model SHA256 is `d6170270a4210b6a3b01d2e9522c00a3dab0896c87618ff364783045b1095706`;
  projection SHA256 is
  `2344b7d44db447173b322c02837aa0c2d284475f35bfe8a90a4ab925f32057eb`.
  PHSP candidates were scored with that model; PHSP was not a training input.

The Stage 2 runner kept all Stage 1 candidates in its audit and attached
truth only as an evaluation label. `source_id`, `event_entry`, and
`candidate_slot` identify each row. A multithreaded Stage 1 snapshot does
not preserve raw EDM4hep row order. Selected direct candidates were matched
to generated decays by charge and generated cos θp content, with a maximum
angle difference of **2.98×10⁻⁸**; no raw row-index join was used.
Efficiency counts unique generated decays with at least one selected fully
truth-matched candidate. A few selected direct decays have duplicate
candidate rows, so raw candidate rows are not the numerator.

## Counts and angular acceptance

| Stage | All candidate rows | Direct candidate rows | Unique direct decays | Cumulative / 100,007 decays | Conditional from previous |
|---|---:|---:|---:|---:|---:|
| Stage 1 | 60,426 | 55,294 | 55,274 | 55.27% | — |
| Offline selected | 57,753 | 54,779 | 54,759 | 54.76% | 99.07% |
| Fixed BDT score | 26,590 | 26,436 | 26,429 | 26.43% | 48.26% |

The remaining nonmatched candidate counts are 5,132, 2,974 and 154 at
these three stages. After the BDT, 13,232 unique Λb and 13,197 unique
anti-Λb decays remain. The [ten-bin acceptance plot](figures/stage2_v3_phsp_angle_100k_bdt1028/cos_theta_p_acceptance.png)
shows all three cumulative efficiencies. The [charge split](figures/stage2_v3_phsp_angle_100k_bdt1028/cos_theta_p_acceptance_by_charge.png)
checks the convention for both conjugates. The
[fit CSV](data/stage2_v3_phsp_angle_100k_bdt1028/cos_theta_p_acceptance_for_fit.csv)
and [complete JSON](data/stage2_v3_phsp_angle_100k_bdt1028/acceptance_resolution.json)
give exact edges, generated and selected decay counts, cumulative and
conditional efficiencies, and 68% binomial counting intervals.

Stage 1 and offline efficiency is approximately 53–59% across the ten
equal-width truth bins. The fixed BDT creates a much stronger angular
dependence: **0.3885** for generated −1≤cos θp<−0.8 versus **0.1865**
for 0.4≤cos θp<0.6. The binomial intervals describe finite PHSP counts
only; detector and model systematics are not included. This variation must
be included in any angular likelihood for this score.

## Resolution and fit use

For the 26,429 unique selected direct decays, reconstructed minus generated
cos θp has median **1.0×10⁻⁵**, central 68% half-width **0.01182**, and
RMS **0.08879**. The larger RMS reflects tails: **5.60%** have |Δcos θp|>0.1,
and **1.36%** have |Δcos θp|>0.4. The
[core and binned width](figures/stage2_v3_phsp_angle_100k_bdt1028/cos_theta_p_resolution.png),
[full log-scale residual](figures/stage2_v3_phsp_angle_100k_bdt1028/cos_theta_p_residual_full.png),
and [truth-to-reco migration](figures/stage2_v3_phsp_angle_100k_bdt1028/cos_theta_p_migration.png)
show both the narrow core and non-Gaussian tails.

The JSON stores a ten-by-ten matrix with **generated truth bins as rows and
reconstructed bins as columns**. Each count is also divided by the number
of *generated* decays in its truth bin to form a response matrix that
includes both efficiency and migration. For a binned fit, fold a proposed
generated angular distribution through this matrix to predict reconstructed
bin counts. Directly dividing a reconstructed histogram by a truth-bin
efficiency curve would ignore migration. The selected direct-decay table is
in [Parquet](data/stage2_v3_phsp_angle_100k_bdt1028/selected_direct_resolution.parquet)
for an unbinned or finer-grained response study.

The complete Stage 2/BDT candidate tables and angular outputs are archived
at `/eos/lhcb/lbdt3/user/rquaglia/fcc_ee/lblgamma/outputs/stage2_v3_phsp_100k_bdt1028/`.
Their reproduction commands are in
[howto/v3_phsp_angle_acceptance.md](../howto/v3_phsp_angle_acceptance.md).
The PHSP acceptance and response must be recalculated if the PI changes the
offline selection, BDT model or score, or detector scenario. Before using
the response in a final fit, compare PHSP and physics-model reconstruction
and confirm the angular convention and modelling uncertainty.

## Results and figures

- [Cumulative acceptance through Stage 1, offline and BDT](figures/stage2_v3_phsp_angle_100k_bdt1028/cos_theta_p_acceptance.png)
- [BDT-selected acceptance by charge](figures/stage2_v3_phsp_angle_100k_bdt1028/cos_theta_p_acceptance_by_charge.png)
- [Residual core and width versus generated angle](figures/stage2_v3_phsp_angle_100k_bdt1028/cos_theta_p_resolution.png)
- [Full residual tails on a log scale](figures/stage2_v3_phsp_angle_100k_bdt1028/cos_theta_p_residual_full.png)
- [Truth-to-reconstructed angle migration](figures/stage2_v3_phsp_angle_100k_bdt1028/cos_theta_p_migration.png)
- [Fit-ready efficiency CSV](data/stage2_v3_phsp_angle_100k_bdt1028/cos_theta_p_acceptance_for_fit.csv) and [response matrix JSON](data/stage2_v3_phsp_angle_100k_bdt1028/acceptance_resolution.json)

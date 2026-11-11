# v3 Stage 2 BDT input proposal

## Question and inputs

The PI chose `|m(pπ)−1.115683 GeV| ≤ 12.5 MeV` and reconstructed
`E(Λb) ≥ 10.5 GeV` before training, with no π⁰/η veto. Which saved
reconstructed variables merit a first XGBoost comparison? The exact v3
Physics ROOT input, 191 valid Zbb ROOT chunks, hashes, and processed-event
counts are recorded in the
[preparation summary](../outputs/analysis/studies/v3_offline_inspection_20261002/reference_mass5/summary.json)
and the [selected-table manifest](../outputs/analysis/studies/v3_offline_inspection_20261002/reference_mass12p5_lbE10p5/manifest.json).
The selected comparison has 54,872 truth-matched Physics candidates,
3,005 wrong Physics combinations, and 214,554 nonmatched Zbb candidates.
Truth is used here only to label plotted categories and rank variables.

## First feature set

The named ordered list `v3_offline_no_veto_proposal` is in
[`lb_bdt_features.json`](../config/lb_bdt_features.json). The Stage 2
preparation derives the two new scalar inputs described below; all other
inputs are already saved from Stage 1 or the photon-pair calculation.

| Group | Proposed inputs | Reason to test |
|---|---|---|
| Kinematics | `lb_E`, `proton_p`, `pion_p`, `gamma_E`, `lambda_p` | Direct signal is harder than the surviving inclusive combinations. Retain energy information after the loose 10.5 GeV cut. |
| Topology | `proton_d0sig`, `pion_d0sig`, `lambda_flight_xyz_sig`, `lb_thrust_abs_cos` | Daughter displacement, 3D Λ⁰ flight, and Λb alignment with the original thrust axis. Absolute thrust cosine removes the arbitrary axis sign. |
| Photon activity | `iso_R03_all_energy_over_gamma_E`, `iso_R05_charged_n`, `iso_R03_neutral_n` | R03 activity/γ energy and neutral multiplicity separate well; R05 has the stronger charged-multiplicity separation among R02/R03/R05. All use the fitted Λ⁰ hemisphere and remove candidate daughters as documented in [the isolation guide](../howto/understand_isolation.md). |
| Λ⁰-cone tracks | `lambda0_iso_R05_charged_n_d0`, `lambda0_iso_R05_charged_absd0_min`, `lambda0_iso_R05_charged_absd0_max` | Test the largest and smallest absolute PV-corrected impact parameters and the number of usable tracks. R05 has better charged-track coverage than R03. |
| Event balance | `z_partial_deltaE`, `z_partial_deltaP` | Strong single-variable separation, although correlated with Λb energy. [Definitions](../howto/understand_z_balance.md). |
| Photon partners | `d_pi0`, `d_eta`, `min_pair` | Encode π⁰, η, and low-mass partner behavior in the model **without** a hard veto. Partners are other raw type-22 photons on the fitted Λ⁰ hemisphere. |

The Stage 2 preparer writes 36 activity-energy/γ-energy ratios when their
source columns exist and `lb_thrust_abs_cos = |lb_thrust_cos|`. It preserves
the raw variables too. `d_pi0`/`d_eta` are minimum absolute mass distances
over partners, and `min_pair` is the lowest partner mass. An empty partner
list gives `+inf`; the trainer maps it to missing, preserving the no-partner
category as an XGBoost missing branch. For charged-cone extrema, `n_d0=0`
gives `-999`, also mapped to missing. The d0 extrema are **distances in mm**,
not significances; they use the first linked charged-object track and the
candidate PV correction.

## Evidence from the same selected candidates

The [feature ranking CSV](../outputs/analysis/studies/v3_offline_inspection_20261002/reference_mass12p5_lbE10p5/feature_proposal/feature_candidates.csv)
reports one-variable candidate AUC on finite values and valid fractions.
The [focused activity plot](../outputs/analysis/studies/v3_offline_inspection_20261002/reference_mass12p5_lbE10p5/feature_proposal/activity_feature_proposal.png)
and [normalized comparison pages](../outputs/analysis/studies/v3_offline_inspection_20261002/reference_mass12p5_lbE10p5/feature_proposal/plots)
show shapes. AUC is quoted as `max(AUC, 1−AUC)` and is **exploratory**:
the cut and variable ranking used these same candidates, and correlations
mean one-variable ranks do not measure incremental BDT value.

| Variable | Finite-value separation AUC | Valid Physics / Zbb |
|---|---:|---:|
| `lb_E` | 0.980 | 100% / 100% |
| `z_partial_deltaE` | 0.950 | 100% / 100% |
| `z_partial_deltaP` | 0.939 | 100% / 100% |
| `d_pi0` | 0.915 | 91.8% / 100.0% |
| `iso_R03_all_energy_over_gamma_E` | 0.862 | 100% / 100% |
| `iso_R03_neutral_n` | 0.816 | 100% / 100% |
| `lambda0_iso_R05_charged_absd0_max` | 0.801 | 64.6% / 76.5% |
| `d_eta` | 0.757 | 91.8% / 100.0% |
| `iso_R05_charged_n` | 0.736 | 100% / 100% |
| `lb_thrust_abs_cos` | 0.711 | 100% / 100% |
| `lambda0_iso_R05_charged_absd0_min` | 0.604 | 64.6% / 76.5% |

The d0 minimum is weak by itself; it is included for an ablation rather than
claimed as a proven feature. The signed `lb_thrust_cos` has nearly 0.5
single-sided AUC because signal and background gather near both ±1; its
absolute value has clearer separation. The full-event balance variables
showed much weaker single-variable separation and are kept out of this first
set. Λb mass, Λ⁰ mass, cos θp, truth/ancestry, candidate multiplicity, and
pass flags are not training inputs. Mass and angle remain analysis outputs.

## Reproduce and next check

```bash
env -u PYTHONPATH -u PYTHONHOME myenv/bin/python \
  studies/reconstruction/study_v3_feature_candidates.py \
  --reference-dir outputs/analysis/studies/v3_offline_inspection_20261002/reference_mass12p5_lbE10p5/candidates \
  --output-dir outputs/analysis/studies/v3_offline_inspection_20261002/reference_mass12p5_lbE10p5/feature_proposal
```

The current pilot preparation using the new default, one Zbb chunk, and
1,000 Stage 1 output events per input confirms all 20 proposed columns are
present and no photon veto was applied. Its Physics and Zbb selected keys
match the independent full-sample study; 44 Physics and 108 Zbb pilot
candidates failing the diagnostic π⁰ window were retained. It is a schema check, not a BDT
performance result. The next training should compare feature-group ablations
on event/chunk-disjoint validation and test partitions, then inspect
`m(Λγ)` and `cos θp` before and after the BDT for sculpting. Evaluate the
fixed model on Λb→Λ⁰η feed-down separately. The 191-chunk Zbb tail is too
small to claim a one-million-background working point without its reported
MC interval; extend to the completed campaign when available.

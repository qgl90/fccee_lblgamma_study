# Direct ROOT observable comparison, 2026-10-01

## Question

What do the already stored post-preselection columns look like across direct
Λb→Λγ PHSP and physics MC, Λb→Λη(γγ) feeddown, and inclusive Z→bb?
This is a diagnostic comparison; the nominal reconstruction and selection are
unchanged and no extra cut is applied.

## Inputs and command

Repository HEAD during the read: `7efcf75030d9b7dabe4f6578fe9464cc2ab0135a`.
The three flat candidate ROOT files were:

- `/eos/lhcb/lbdt3/user/rquaglia/fcc_ee/lblgamma/outputs/nominal_preselection_100k_signal_phsp_candidates.root`
- `/eos/lhcb/lbdt3/user/rquaglia/fcc_ee/lblgamma/outputs/nominal_preselection_100k_signal_physics_candidates.root`
- `/eos/lhcb/lbdt3/user/rquaglia/fcc_ee/lblgamma/outputs/nominal_preselection_100k_lbgamma_eta_candidates.root`

The Zbb input list is frozen in
`outputs/analysis/studies/condor_zbb_chunk_catalog_plots_20261001.json`:
679 valid native ROOT chunks at the time of the scan. The catalog records
267,510,122 processed input events and 3,337,613 candidate-bearing ROOT
tree entries. The plots read the saved candidate branches directly; no new
Condor processing or candidate flattening was done.

```bash
myenv/bin/python studies/reconstruction/plot_existing_preselection_observables.py \
  --phsp /eos/lhcb/lbdt3/user/rquaglia/fcc_ee/lblgamma/outputs/nominal_preselection_100k_signal_phsp_candidates.root \
  --physics /eos/lhcb/lbdt3/user/rquaglia/fcc_ee/lblgamma/outputs/nominal_preselection_100k_signal_physics_candidates.root \
  --eta /eos/lhcb/lbdt3/user/rquaglia/fcc_ee/lblgamma/outputs/nominal_preselection_100k_lbgamma_eta_candidates.root \
  --zbb-catalog outputs/analysis/studies/condor_zbb_chunk_catalog_plots_20261001.json \
  --output-dir outputs/analysis/studies/extra_observables_root_full_20261001
```

The 1,000-entry-per-file pilot is saved separately at
`outputs/analysis/studies/extra_observables_root_pilot_20261001`.

## Counts and plots

The flat files contained 60,424 PHSP, 60,593 physics, and 44,930 eta
candidate rows. Truth is used only to split diagnostic classes after
reconstruction. Direct PHSP and physics counts were 55,293 and 55,393;
their wrong-combination counts were 5,131 and 5,200. The eta file contained
39,772 truth-associated feeddown and 5,158 other combinations. The native
Zbb chunks contributed 4,204,734 candidates outside the direct-signal truth
class. Counts refer to candidate rows, not independent events or generated
decays. Both charge signs are included. The JSON output records charge counts,
histogram bins, in-range counts, and the source paths.

The output directory contains `photon_isolation.png` (`iso_R03_noLambda`,
`iso_R05_noLambda`), `lambda_displacement.png` (absolute `lambda_d0_sig`,
`lambda_flight_rxy_sig`), `photon_partner.png` (`dm_gg_pi0`, `E_gamma2`),
`candidate_mass.png` (`lb_mass`), and `summary.json`. Each histogram bin is
divided by the full count of its diagnostic class; missing values and values
outside the displayed range remain in the denominator. Thus these are
per-candidate shape and occupancy plots, not physical yield predictions.

## Initial reading and limit

The direct PHSP and physics mass peaks and their isolation and displacement
shapes agree closely by eye. Eta feeddown has a broad low-mass distribution
and a visible feature around 0.4 GeV in the stored π0 mass-distance variable.
Only 8,251/55,293 direct PHSP, 8,268/55,393 direct physics, and
26,942/39,772 eta-feeddown candidates have a stored selected photon partner.
The corresponding inclusive-Zbb occupancy is 3,040,054/4,204,734.

`dm_gg_pi0` and `E_gamma2` describe **one** other selected photon in the
same thrust hemisphere: the partner closest to π0 mass. The ROOT columns do
not store all γγ pairs or a dedicated η mass-distance. These plots cannot
measure the efficiency of an η veto or of the proposed “at least one pair with
energy above 1.5 GeV” rule. For those decisions, derive all-pair observables
from the saved event photon collection if it is present, retain the no-partner
state, and compare candidate and event retention against this unchanged
baseline. No cut is proposed for adoption from the shape plots alone.

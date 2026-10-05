# v3 photon pointing input audit — 2026-10-05

## Question

Can the present post-selection candidates support a photon-displacement or
Λ–γ pointing study? This is an input audit, not a detector-response scenario
or a proposed cut.

## Exact inputs checked

- Stage 0 Physics signal: `/eos/lhcb/lbdt3/user/rquaglia/fcc_ee/lblgamma/outputs/Lb2LambdaGammaPhysics_nev100000_IDEA_edm4hep.root`, 100,000 input events.
- Stage 1 v3 Physics signal: `/eos/lhcb/lbdt3/user/rquaglia/fcc_ee/lblgamma/outputs/stage1_v3_my_run/signal_physics.root`, 56,871 candidate-bearing output events. The historical basename lacks `v3`; its scenario is identified by the path.
- Offline Stage 2: `outputs/analysis/studies/stage2_v3_incremental_20261002/prepared/signal_-1_selected.parquet` (57,877 candidate rows) and `signal_-1_audit.parquet` (60,598 candidate rows). These are offline-prepared tables, **not** a final BDT-selected count.

The Stage 1 ROOT `events` schema has `lb_photon_px/py/pz`, `lb_photon_energy`,
`lb_photon_index`, `event_entry`, and the reco-to-MC association vector
`reco_mc_index`. The general flattened Stage 1 table retains the reconstructed
`photon_px/py/pz` and `Gamma_Px/Py/Pz` aliases, along with `photon_mc_p`,
`photon_mc_pt`, `photon_mc_eta`, `photon_mc_cos_opening`, and the MC index.
The Stage 1 truth labeler **does not snapshot** MC photon `px/py/pz` or its
full production vertex; `photon_mc_vertex_rxy` is only a scalar radius.

The offline selected and audit Parquets retain `gamma_p`, `gamma_pt`,
`gamma_eta`, `gamma_E`, `photon_reco_index`, `photon_mc_index` and ancestry,
but **not reconstructed or true photon `px/py/pz`**. In the selected signal
table, 57,822 of 57,877 candidate rows have a unique matched MC photon index
and PDG 22. This is candidate-row availability, not a direct-signal efficiency.
`gamma_pt` and `gamma_eta` alone cannot recover `px` and `py` because the
azimuth is absent.

The Stage 0 EDM4hep `events` schema retains `Particle/Particle.momentum.x/y/z`
and `Particle/Particle.vertex.x/y/z`, plus reconstructed-particle momentum
and `EFlowPhoton/EFlowPhoton.position.x/y/z` and `directionError.x/y/z`.
The values and meaning of the latter calorimeter fields have **not yet been
validated** as independent photon pointing measurements. A read of even one
EFlowPhoton entry from the EOS file stalled during this audit; schema presence
alone is insufficient evidence of usable pointing resolution.

The existing `dca_Lam_gamma` and `Lxyz_implied` are geometric proxies that
back-project the reconstructed photon momentum from the fitted PV. They are
not measurements of a photon origin or a Λb decay vertex. The current
candidate builder uses only reconstructed inputs, and its truth labels are
attached afterward.

## Interpretation and next comparison

Reconstructed photon momentum is available at Stage 1; true momentum and
production vertex can be joined from Stage 0 using `event_entry` and the
candidate's matched `photon_mc_index` after validating the entry mapping on
a small sample. Both vectors are useful for response diagnostics. Their
difference alone cannot emulate an independent pointing measurement: a photon
*line* also needs an anchor at the calorimeter. The preferred anchor is a
validated cluster position. If that field is unusable, a named idealized ECAL
surface and the present origin-pointing reconstructed direction can define an
approximate impact position; this would be an explicit geometry assumption.
The independent incidence direction can then be generated from the MC photon
direction smeared by 1 mrad per specified angular component. MC truth is used
only to generate the synthetic detector response, never as an unsmeared
selection variable. The MC production vertex is needed to validate closure
and the displacement response.

For a first **conditional post-selection what-if**, keep the existing mass,
BDT score, Armenteros and Λ-IP choices fixed. Add the synthetic photon line
only for candidates that survived those cuts, compute its distance to the
fitted PV and its closest approach to the reconstructed Λ line, and compare
signal, Zbb, Zcc and Zss on the same selected rows. This does not require
rerunning the full Stage 1 or training, provided the selected rows can be
joined reliably to Stage 0 truth and cluster information. It does **not**
measure a new end-to-end efficiency: replacing photon momentum upstream would
change candidate mass, angular observables, isolation and potentially the
BDT. Such a reference detector scenario would require regeneration or a
validated reconstruction rerun.

Next, validate the Stage 0 `EFlowPhoton` position and direction fields and the
candidate-to-cluster relation on at most 1,000 events. Check whether the
post-selected Zss photons are truth displaced before interpreting the reach
of a pointing cut. A Λ–γ closest-approach/vertex fit must propagate the Λ
trajectory and photon-line uncertainties, especially for nearly parallel
lines. The PI should review the assumed detector resolution before any
displacement cut is interpreted physically.

Reproduction commands and field lists: [howto/stage2.md](../howto/stage2.md#photon-pointing-input-audit).

# Λb → Λη local production notes

The EvtGen file `evtgen/Lb2LambdaEta.dec` forces `Lambda_b0 → Lambda0(p+ pi−) eta(gamma gamma)` and charge conjugates. It uses PHSP, with all specified decay fractions set to one. Physical branching fractions are applied later in yield studies.

The current generation workflow is the default target in `Snakefile`, documented in [README.md](README.md). It produces both Λγ and Λη samples at 500,000 events each in ten 50,000-event chunks. The eta chunks use Pythia seeds 22355–22364 and merge into `outputs/delphes/Lb2LambdaEta_nev500000_IDEA_edm4hep.root`. The earlier 50,000-event output, made with seed 12346, remains separate.

An earlier 10,000 event eta file remains at `outputs/delphes/Lb2LambdaEta_IDEA_edm4hep.root`. Its validation report is `outputs/logs/Lb2LambdaEta.validation.json`: 10,000 saved events, with 4,987 Λb and 5,013 anti-Λb signal chains and eta → γγ in every event. Of these, 108 Λ decays contained additional radiative photons; later truth matching must allow these.

Reconstruction of `m(gamma gamma)` and `m(Lambda gamma gamma)` belongs in the later FCCAnalyses reconstruction stage. The generation workflow does not run reconstruction.

# Fixed-score Armenteros PI deck

Build with `bash build.sh` from this directory. The self-contained figures
are copied from `docs/figures/stage2_v3_armenteros_1028/` and are produced
by `studies/reconstruction/study_v3_post_bdt_armenteros.py` using the command
in `howto/v3_post_bdt_armenteros.md`. The input model and catalog are the
frozen 1,028-chunk v3 snapshot in `docs/STAGE2_V3_BDT_REVIEW_2026-10-03.md`.
The counts and exact input hashes are in
`docs/data/stage2_v3_armenteros_1028/broad_summary.json`.

Use `sha256sum presentations/stage2_v3_armenteros_1028/figures/*.png
docs/figures/stage2_v3_armenteros_1028/*.png` from the repository root to
check that slide copies match the study figures.
The score and Armenteros box are proposals for review, not reference cuts.

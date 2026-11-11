# Rebuild a PI study deck

Each deck lives in its own `presentations/STAGE_SCENARIO_SNAPSHOT/` directory.
Its `README.md` must name the frozen catalog or direct inputs, the plot source
paths and hashes, and the command that generated each figure. Its `figures/`
directory contains the image files referenced by the Beamer source.

For the existing Stage 1 v3 example, from the repository root:

```bash
cat presentations/stage1_v3_review/README.md
bash presentations/stage1_v3_review/build.sh
```

The result is `presentations/stage1_v3_review/stage1_v3_review.pdf`. Recreate
the focused source plots using the command in that deck's README before
replacing a figure. Check its source manifest against the copied figure and
keep the 191-chunk denominator shown in that historical presentation.

The current Stage 2 v3 1,028-chunk score review is in
[`presentations/stage2_v3_bdt_1028/`](../presentations/stage2_v3_bdt_1028/).
Rebuild it with:

```bash
bash presentations/stage2_v3_bdt_1028/build.sh
```

Its nine-slide PDF includes the PV/SV event display, frozen candidate
cutflow, held-out response, tight score and purity scans, independent test
projection, and angular-shape check. The underlying full scan and model are
in [`docs/data/stage2_v3_bdt_1028/`](../docs/data/stage2_v3_bdt_1028/).

For a new BDT deck, first finish the frozen Stage 2 preparation, train the
named model, and run the validation score scan as in [Stage 2](stage2.md).
Copy the resulting ROC, score, feature, working-point, mass and helicity-angle
figures into a new snapshot-named deck. Record the original paths, SHA-256,
catalog/model manifests, and numerical denominators in its README. Build the
PDF with the deck's `build.sh` and inspect it before PI review. A score shown
on slides is a candidate working point until the PI accepts it.

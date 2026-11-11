# PI presentation handoff

Use this after a study has frozen inputs, a review note, and reproducible
figures. The Stage 1 example is `presentations/stage1_v3_review/`, including
its self-contained `figures/`, Beamer source, build script, and README.

For a new stage or catalog snapshot, create a new directory under
`presentations/` named for the stage, scenario, and frozen snapshot. Select
only figures that answer the PI question. Copy them into `figures/` and record
each source path and SHA-256, the generating command or output manifest, and
the input catalog/model hash in the deck README. Do not silently replace a
figure from another catalog snapshot.

The deck should show the study question; exact samples and denominators;
selection or model definition; staged signal, wrong-combination and
background counts; the paired distributions and statistical intervals; and
the limitations and decision requested from the PI. State whether each plot
uses raw counts, unit-normalized shapes, or physical expected candidates.
Mark validation-derived score points as proposals until the PI chooses a
reference cut. Forced η/π⁰ counts are never labelled as inclusive Zbb yield.

Keep the Beamer `.tex` and `build.sh` in the repository. Run the build and
inspect the resulting PDF for unreadable axes, clipped captions, and missing
figures. Save the PDF with the same snapshot label. Update the relevant
`howto/` recipe and the PI review note at the same time, so a collaborator can
recreate each figure without relying on the slide copy.

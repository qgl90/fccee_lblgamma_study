#!/usr/bin/env python3
"""Zoom the frozen three-flavour S/sqrt(B) curves in the high-score tail."""

import argparse
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

import v3_plot_style  # noqa: F401


PARTS = ("all", "validation", "test")
STAGES = ("arm_only", "arm_eta", "arm_pi0", "arm_pi0_eta")
COLORS = {"arm_only": "#2670a8", "arm_eta": "#ba4148",
          "arm_pi0": "#d89428", "arm_pi0_eta": "#198466"}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--scan", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    scan = json.loads(args.scan.read_text())
    if scan.get("objective") != "s_over_sqrt_b":
        raise ValueError("Expected frozen S/sqrt(B) scan")
    x = np.asarray(scan["plot_grid"])
    fig, axes = plt.subplots(1, 3, figsize=(16, 4.7))
    for part, ax in zip(PARTS, axes):
        for stage in STAGES:
            y = np.array([np.nan if v is None else v
                          for v in scan["plot_curves"][part][stage]["significance"]])
            ax.plot(x, y, color=COLORS[stage], label=scan["scenario_labels"][stage])
            point = scan["choices"][stage][
                "test_at_validation_choice" if part == "test" else
                "validation_maximum" if part == "validation" else
                "all_at_validation_choice"]
            ax.scatter(point["score"], point["S_over_sqrt_B"],
                       color=COLORS[stage], s=32, zorder=4)
        if part != "validation":
            ax.axvline(scan["choices"]["arm_only"]["validation_maximum"]["score"],
                       color=COLORS["arm_only"], linestyle="--", linewidth=1)
        ax.set(xlim=(.975, .999), ylim=(100, 260),
               xlabel="Minimum frozen BDT score", ylabel=r"Peak $S/\sqrt{B}$",
               title={"all": "Full archive (descriptive)",
                      "validation": "Validation choice",
                      "test": "Test at validation choice"}[part])
        ax.grid(alpha=.2)
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="lower center", bbox_to_anchor=(.5, -.015),
               ncol=4, frameon=False)
    fig.suptitle("Armenteros applied; B = weighted Zbb + Zcc + Zss; peak 5.4–5.9 GeV")
    fig.tight_layout(rect=(0, .10, 1, .92))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(args.output, dpi=180, bbox_inches="tight")


if __name__ == "__main__":
    main()

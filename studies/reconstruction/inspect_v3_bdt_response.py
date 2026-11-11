#!/usr/bin/env python3
"""Plot held-out v3 BDT response and mass/angle shapes without loading all columns."""

# Author: Renato Quagliani (rquaglia@cern.ch)

import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile

os.environ.setdefault("MPLCONFIGDIR", str(Path(tempfile.gettempdir()) / "lblgamma-mplconfig"))
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pyarrow.parquet as pq
import v3_plot_style  # noqa: F401 - LHCb-style presentation figures

from train_offline_bdt import split_chunk, split_signal


SCORE_BINS = np.linspace(0., 1., 51)
MASS_BINS = np.linspace(4.7, 6.5, 55)
ANGLE_BINS = np.linspace(-1., 1., 41)
THRESHOLDS = (None, .5, .9)  # shape checks only, not a working-point choice
CATEGORIES = ("direct_physics", "wrong_physics", "zbb_nonmatched")
LABELS = {"direct_physics": "Direct Physics", "wrong_physics": "Wrong Physics combination",
          "zbb_nonmatched": "Inclusive Zbb other"}
COLORS = {"direct_physics": "#2563a6", "wrong_physics": "#777777",
          "zbb_nonmatched": "#d97931"}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--prepared-dir", type=Path, required=True)
    ap.add_argument("--model-dir", type=Path, required=True)
    ap.add_argument("--output-dir", type=Path, required=True)
    args = ap.parse_args()
    prepared_summary = args.model_dir / "prepared_manifest.json"
    training_summary = args.model_dir / "training_summary.json"
    prepared = json.loads(prepared_summary.read_text())
    trained = json.loads(training_summary.read_text())
    if trained["prepared_manifest_sha256"] != digest(prepared_summary):
        ap.error("The model's frozen preparation manifest has changed")
    args.output_dir.mkdir(parents=True, exist_ok=True)
    score_counts = {category: np.zeros(len(SCORE_BINS)-1, dtype=np.int64)
                    for category in CATEGORIES}
    shapes = {category: {threshold: {"mass": np.zeros(len(MASS_BINS)-1, dtype=np.int64),
                                     "angle": np.zeros(len(ANGLE_BINS)-1, dtype=np.int64),
                                     "candidates": 0}
                         for threshold in THRESHOLDS}
              for category in CATEGORIES}
    for record in prepared["records"]:
        source_id = record["source_id"]
        sample = "signal" if source_id == -1 else "zbb"
        path = args.model_dir / "scored_selected" / f"{sample}_{source_id}_selected.parquet"
        table = pq.read_table(path, columns=["bdt_score", "lb_mass", "cos_theta_p",
                                             "truth_matched", "event_entry"])
        score = table["bdt_score"].to_numpy(zero_copy_only=False)
        mass = table["lb_mass"].to_numpy(zero_copy_only=False)
        angle = table["cos_theta_p"].to_numpy(zero_copy_only=False)
        truth = table["truth_matched"].to_numpy(zero_copy_only=False) == 1
        if sample == "signal":
            entries = table["event_entry"].to_numpy(zero_copy_only=False)
            test = split_signal(entries) == "test"
            categories = (("direct_physics", truth & test),
                          ("wrong_physics", ~truth & test))
        elif split_chunk(source_id) == "test":
            categories = (("zbb_nonmatched", ~truth),)
        else:
            continue
        for category, category_mask in categories:
            score_counts[category] += np.histogram(score[category_mask], SCORE_BINS)[0]
            for threshold in THRESHOLDS:
                mask = category_mask if threshold is None else category_mask & (score >= threshold)
                shapes[category][threshold]["candidates"] += int(mask.sum())
                for variable, values, bins in (("mass", mass, MASS_BINS),
                                               ("angle", angle, ANGLE_BINS)):
                    shapes[category][threshold][variable] += np.histogram(
                        values[mask & np.isfinite(values)], bins)[0]
    fig, ax = plt.subplots(figsize=(9, 5.7), constrained_layout=True)
    for category in CATEGORIES:
        counts = score_counts[category]
        if counts.sum():
            ax.stairs(counts/counts.sum(), SCORE_BINS,
                      label=f"{LABELS[category]} ({counts.sum():,})",
                      color=COLORS[category], linewidth=1.7)
    ax.set(xlabel="BDT signal score", ylabel="Fraction of held-out candidates / bin",
           yscale="log", title="v3 offline selection: independent test response")
    ax.legend(fontsize=9)
    ax.grid(alpha=.2)
    fig.savefig(args.output_dir / "test_response_three_categories.png", dpi=180)
    plt.close(fig)
    fig, axes = plt.subplots(2, 2, figsize=(12, 7.6), constrained_layout=True)
    for row, category in enumerate(("direct_physics", "zbb_nonmatched")):
        for col, (variable, bins, xlabel) in enumerate(
                (("mass", MASS_BINS, r"$m(\Lambda\gamma)$ [GeV]"),
                 ("angle", ANGLE_BINS, r"$\cos\theta_p$"))):
            ax = axes[row, col]
            for threshold, color in zip(THRESHOLDS, ("#777777", "#2563a6", "#d97931")):
                counts = shapes[category][threshold][variable]
                if not counts.sum():
                    continue
                cut_label = "All" if threshold is None else f"Score $\geq${threshold:g}"
                ax.stairs(counts/counts.sum(), bins,
                          label=f"{cut_label} ({shapes[category][threshold]['candidates']:,})",
                          color=color, linewidth=1.5)
            ax.set(xlabel=xlabel, ylabel="Fraction in score subset / bin",
                   title=LABELS[category])
            ax.legend(fontsize=8)
            ax.grid(alpha=.2)
    fig.suptitle("Held-out mass and angle shapes after illustrative score cuts")
    fig.savefig(args.output_dir / "test_mass_angle_by_score.png", dpi=180)
    plt.close(fig)
    counts = {category: {"test_total": int(score_counts[category].sum()),
                         "after_score_0p5": shapes[category][.5]["candidates"],
                         "after_score_0p9": shapes[category][.9]["candidates"]}
              for category in CATEGORIES}
    result = {"command": sys.argv, "script_sha256": digest(Path(__file__)),
              "prepared_summary": str(prepared_summary),
              "prepared_summary_sha256": digest(prepared_summary),
              "training_summary": str(training_summary),
              "training_summary_sha256": digest(training_summary),
              "split": "signal event hash and Zbb chunk_id modulo 10, test partition only",
              "thresholds": "0.5 and 0.9 are illustrative shape diagnostics, not optimized cuts",
              "counts": counts}
    (args.output_dir / "response_manifest.json").write_text(json.dumps(result, indent=2)+"\n")
    print(json.dumps(counts, indent=2))


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Plot physically scaled forced-mode shapes alongside the held-out BDT projection.

The inclusive Zbb component can contain these rare modes. Curves are shown
separately; the script does not sum forced modes with inclusive Zbb.
"""
import argparse
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

import v3_plot_style  # noqa: F401


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--reference-projection", type=Path, required=True)
    ap.add_argument("--reference-candidates", type=Path, required=True)
    ap.add_argument("--eta-summary", type=Path, required=True)
    ap.add_argument("--eta-candidates", type=Path, required=True)
    ap.add_argument("--pi0-summary", type=Path, required=True)
    ap.add_argument("--pi0-candidates", type=Path, required=True)
    ap.add_argument("--output-dir", type=Path, required=True)
    args = ap.parse_args()
    reference_projection = json.loads(args.reference_projection.read_text())
    reference = pd.read_parquet(args.reference_candidates,
                                columns=["lb_mass", "expected_weight", "expected_component",
                                         "inside_optimization_mass_window"])
    modes = {}
    for name, summary_path, candidates_path in (
            ("eta_physics", args.eta_summary, args.eta_candidates),
            ("pi0_physics", args.pi0_summary, args.pi0_candidates)):
        summary = json.loads(summary_path.read_text())
        if summary["mode"] != name:
            raise ValueError(f"{summary_path} is not {name}")
        frame = pd.read_parquet(candidates_path, columns=["lb_mass"])
        if len(frame) != summary["stages"]["bdt_selected"]["candidate_rows"]:
            raise ValueError(f"{name} BDT table and summary differ")
        modes[name] = (summary, frame)
    eta, pi0 = (modes[name][0] for name in ("eta_physics", "pi0_physics"))
    if eta["bdt_score"] != pi0["bdt_score"] or \
            eta["model_sha256"] != pi0["model_sha256"] or \
            eta["signal_peak_window_gev"] != pi0["signal_peak_window_gev"]:
        raise ValueError("Forced modes do not use the same BDT and peak window")
    if reference_projection["model_sha256"] != eta["model_sha256"] or \
            reference_projection["validation_choice"]["score"] != eta["bdt_score"] or \
            reference_projection["optimization_mass_window_gev"] != eta["signal_peak_window_gev"]:
        raise ValueError("Forced modes do not match the reference projection")
    window = eta["signal_peak_window_gev"]
    peak = reference.lb_mass.between(*window)
    sums = {name: float(reference.loc[peak & reference.expected_component.eq(name),
                                      "expected_weight"].sum()) for name in ("signal", "zbb")}
    projection = {"reference_projection": str(args.reference_projection),
                  "reference_candidates": str(args.reference_candidates),
                  "reference_peak_projected_candidates": sums,
                  "forced_mode_peak_projected_candidates": {
                      name: modes[name][0]["projected_candidates"]["peak_candidates"]
                      for name in modes},
                  "warning": "Forced-mode curves are separate estimates and may overlap inclusive Zbb; do not add them to Zbb without an overlap audit",
                  "window_gev": window, "bdt_score": eta["bdt_score"],
                  "model_sha256": eta["model_sha256"]}
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "comparison.json").write_text(json.dumps(projection, indent=2) + "\n")
    edges = np.linspace(4.7, 6.5, 73)
    fig, ax = plt.subplots(figsize=(9, 5.8))
    for name, label, color in (("signal", "Direct Λγ signal", "#2670a8"),
                               ("zbb", "Inclusive Zbb other", "#444444")):
        part = reference.loc[reference.expected_component.eq(name)]
        counts, _ = np.histogram(part.lb_mass, bins=edges, weights=part.expected_weight)
        ax.stairs(counts, edges, label=label, color=color, linewidth=1.9)
    for name, label, color in (("eta_physics", "Forced Λη(γγ) estimate", "#ba4148"),
                               ("pi0_physics", "Forced Λπ⁰(γγ) benchmark", "#d89428")):
        summary, frame = modes[name]
        weight = (summary["projected_candidates"]["factor_before_selection"] /
                  summary["generated_direct_decays"])
        counts, _ = np.histogram(frame.lb_mass, bins=edges,
                                 weights=np.full(len(frame), weight))
        ax.stairs(counts, edges, label=label, color=color, linewidth=1.9)
    ax.axvspan(*window, color="0.85", alpha=.5)
    ax.set(xlabel=r"Reconstructed $m(\Lambda\gamma)$ [GeV]",
           ylabel="Projected candidates / 25 MeV", yscale="log",
           title="Fixed v3 BDT: separate estimates; Zbb test tail is MC-limited")
    ax.text(.02, .04, "Inclusive Zbb includes only 56 test candidates in the peak;\n"
            "forced-mode curves may overlap inclusive Zbb.", transform=ax.transAxes,
            fontsize=8, va="bottom", bbox={"facecolor": "white", "edgecolor": "0.8", "alpha": .9})
    ax.legend(frameon=False, fontsize=8)
    fig.tight_layout()
    fig.savefig(args.output_dir / "expected_mass_comparison.png", dpi=180)
    plt.close(fig)
    print(json.dumps(projection, indent=2))


if __name__ == "__main__":
    main()

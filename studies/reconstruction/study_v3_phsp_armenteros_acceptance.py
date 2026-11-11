#!/usr/bin/env python3
"""PHSP angular response after a named reconstructed Armenteros box veto.

Reuses the frozen generated-decay denominator and scored candidate table.
The veto acts only on fitted-track Armenteros variables; truth is used after
selection to measure acceptance and response.
"""
import argparse
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from study_v3_phsp_angle_acceptance import BINS, COLS, match_generated, sha, stage_result
import v3_plot_style  # noqa: F401


def resolution(frame, generated_counts):
    chosen = frame.sort_values("bdt_score", ascending=False).drop_duplicates("generated_decay_id")
    truth = chosen.generated_truth_angle.to_numpy(dtype=float)
    reco = chosen.cos_theta_p.to_numpy(dtype=float)
    residual = reco - truth
    if not np.isfinite(residual).all() or not np.all((-1 <= reco) & (reco <= 1)):
        raise ValueError("Invalid selected angular residual")
    matrix = np.histogram2d(truth, reco, bins=(BINS, BINS))[0].astype(int)
    return chosen, {"selected_unique_decays": len(chosen),
                    "residual_reco_minus_truth": {
                        "median": float(np.median(residual)),
                        "central_68pct_half_width": float((np.quantile(residual, .84)-np.quantile(residual, .16))/2),
                        "rms": float(np.sqrt(np.mean(residual**2))),
                        "fraction_abs_gt_0p1": float(np.mean(np.abs(residual) > .1)),
                        "fraction_abs_gt_0p4": float(np.mean(np.abs(residual) > .4))},
                    "migration_truth_rows_reco_columns": matrix.tolist(),
                    "response_per_generated_decay_truth_rows_reco_columns": (
                        matrix / generated_counts[:, None]).tolist()}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--baseline-angle-dir", type=Path, required=True)
    ap.add_argument("--bdt-candidates", type=Path, required=True)
    ap.add_argument("--box", nargs=4, type=float, default=(.67, .78, .075, .120),
                    metavar=("ALPHA_MIN", "ALPHA_MAX", "QT_MIN_GEV", "QT_MAX_GEV"))
    ap.add_argument("--output-dir", type=Path, required=True)
    args = ap.parse_args()
    amin, amax, qmin, qmax = args.box
    if not 0 <= amin < amax <= 1 or not 0 <= qmin < qmax:
        ap.error("Invalid box bounds")
    baseline_path = args.baseline_angle_dir / "acceptance_resolution.json"
    baseline = json.loads(baseline_path.read_text())
    generated = pd.read_parquet(args.baseline_angle_dir / "generated_direct_decays.parquet")
    if len(generated) != baseline["generated_direct_decays"]:
        raise ValueError("Generated denominator differs from baseline")
    if not np.allclose(BINS, baseline["bin_edges"]):
        raise ValueError("Baseline angular bins differ")
    raw = pd.read_parquet(args.bdt_candidates, columns=COLS + ["arm_alpha", "arm_qt"])
    direct, error = match_generated(raw, generated)
    original = stage_result(direct, generated)
    if original["selected_bin_counts"] != baseline["stages"]["bdt"]["selected_bin_counts"] or \
            original["candidate_rows"] != baseline["stages"]["bdt"]["candidate_rows"]:
        raise ValueError("Scored candidates do not reproduce the baseline BDT counts")
    if direct.duplicated(["source_id", "event_entry", "candidate_slot"]).any():
        raise ValueError("Duplicate candidate keys")
    if not np.isfinite(direct[["arm_alpha", "arm_qt"]].to_numpy()).all():
        raise ValueError("Nonfinite reconstructed Armenteros values")
    inside = direct.arm_alpha.abs().between(amin, amax) & direct.arm_qt.between(qmin, qmax)
    kept = direct.loc[~inside].copy()
    stage = stage_result(kept, generated)
    before_ids = set(direct.generated_decay_id)
    after_ids = set(kept.generated_decay_id)
    stage["conditional_retention_from_bdt"] = len(after_ids) / len(before_ids)
    before_bins = np.asarray(original["selected_bin_counts"])
    after_bins = np.asarray(stage["selected_bin_counts"])
    stage["conditional_retention_by_generated_bin"] = (after_bins / before_bins).tolist()
    den = np.asarray(stage["generated_bin_counts"], dtype=float)
    chosen, response = resolution(kept, den)
    result = {"scenario": "v3_phsp_100k_bdt1028_post_bdt_armenteros_broad",
              "baseline_angle_json": str(baseline_path), "baseline_angle_json_sha256": sha(baseline_path),
              "bdt_candidates": str(args.bdt_candidates),
              "bdt_candidates_sha256": sha(args.bdt_candidates),
              "model_sha256": baseline["model_sha256"], "fixed_bdt_score": baseline["fixed_bdt_score"],
              "box": {"abs_alpha_min": amin, "abs_alpha_max": amax,
                      "qt_min_gev": qmin, "qt_max_gev": qmax,
                      "reject_inside_inclusive_bounds": True},
              "definition": "post-BDT reconstructed-only veto; truth labels measure efficiency afterward",
              "generated_input_events": baseline["generated_input_events"],
              "generated_direct_decays": len(generated), "bin_edges": BINS.tolist(),
              "maximum_truth_angle_match_difference": error,
              "baseline_bdt": original, "post_bdt_armenteros": stage,
              "rejected_direct_candidate_rows": int(inside.sum()),
              "direct_decays_lost": len(before_ids-after_ids),
              "resolution": response}
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "acceptance_resolution.json").write_text(json.dumps(result, indent=2) + "\n")
    pd.DataFrame({"cos_theta_true_low": BINS[:-1], "cos_theta_true_high": BINS[1:],
                  "generated_decays": stage["generated_bin_counts"],
                  "bdt_selected_decays": original["selected_bin_counts"],
                  "bdt_efficiency": original["efficiency"],
                  "bdt_armenteros_selected_decays": stage["selected_bin_counts"],
                  "bdt_armenteros_efficiency": stage["efficiency"],
                  "armenteros_conditional_on_bdt": stage["conditional_retention_by_generated_bin"]}
                 ).to_csv(args.output_dir / "cos_theta_p_acceptance_for_fit.csv", index=False)
    chosen[["source_id", "event_entry", "candidate_slot", "lb_sign", "bdt_score", "lb_mass",
            "arm_alpha", "arm_qt", "generated_decay_id", "generated_truth_angle",
            "cos_theta_p"]].to_parquet(args.output_dir / "selected_direct_resolution.parquet", index=False)
    centers = (BINS[:-1] + BINS[1:]) / 2
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.8))
    axes[0].plot(centers, original["efficiency"], "o-", label="BDT baseline", color="#4c78a8")
    axes[0].plot(centers, stage["efficiency"], "o-", label="BDT + Armenteros veto", color="#ba4148")
    axes[0].set(ylabel="Selected direct decays / generated direct decays", ylim=(0, 1))
    axes[1].plot(centers, stage["conditional_retention_by_generated_bin"], "o-", color="#ba4148")
    axes[1].set(ylabel="Retained by Armenteros / BDT-selected", ylim=(0, 1))
    for ax in axes:
        ax.set(xlabel=r"Generated $\cos\theta_p$", xlim=(-1, 1))
        ax.grid(alpha=.2)
    axes[0].legend(frameon=False)
    fig.suptitle("100k PHSP v3: proposed reconstructed Armenteros veto after fixed BDT")
    fig.tight_layout()
    fig.savefig(args.output_dir / "cos_theta_p_acceptance_armenteros.png", dpi=180)
    plt.close(fig)
    fig, ax = plt.subplots(figsize=(8, 5.5))
    for sign, label, color in ((1, r"$\Lambda_b$", "#2670a8"), (-1, r"$\overline{\Lambda}_b$", "#ba4148")):
        ax.plot(centers, stage["by_charge"][str(sign)]["efficiency"], "o-", label=label, color=color)
    ax.set(xlabel=r"Generated $\cos\theta_p$", ylabel="BDT + Armenteros selected / generated direct decays",
           xlim=(-1, 1), ylim=(0, 1), title="Post-veto PHSP acceptance by charge")
    ax.grid(alpha=.2)
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(args.output_dir / "cos_theta_p_acceptance_by_charge.png", dpi=180)
    plt.close(fig)
    fig, ax = plt.subplots(figsize=(7.5, 6))
    image = ax.imshow(response["migration_truth_rows_reco_columns"], origin="lower",
                      extent=(-1, 1, -1, 1), aspect="auto", cmap="viridis")
    fig.colorbar(image, ax=ax, label="Selected direct decays / bin")
    ax.set(xlabel=r"Reconstructed $\cos\theta_p$", ylabel=r"Generated $\cos\theta_p$",
           title="Truth → reco after fixed BDT + Armenteros veto")
    fig.tight_layout()
    fig.savefig(args.output_dir / "cos_theta_p_migration_armenteros.png", dpi=180)
    plt.close(fig)
    print(json.dumps({"generated_decays": len(generated),
                      "bdt_unique_decays": original["unique_selected_decays"],
                      "post_veto_unique_decays": stage["unique_selected_decays"],
                      "conditional_retention": stage["conditional_retention_from_bdt"],
                      "resolution": response["residual_reco_minus_truth"]}, indent=2))


if __name__ == "__main__":
    main()

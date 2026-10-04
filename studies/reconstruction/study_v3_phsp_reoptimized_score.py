#!/usr/bin/env python3
"""PHSP angle acceptance for validation-selected three-flavour score scenarios."""

import argparse
import hashlib
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from study_v3_phsp_angle_acceptance import BINS, match_generated, stage_result
import v3_plot_style  # noqa: F401


BASE = Path("/eos/lhcb/lbdt3/user/rquaglia/fcc_ee/lblgamma/outputs")
COLS = ("source_id", "event_entry", "candidate_slot", "lb_mc_index", "lb_sign",
        "truth_matched", "truth_cos_theta_p", "cos_theta_p", "lb_mass",
        "bdt_score", "arm_alpha", "arm_qt", "pass_eta", "pass_pi0")


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--base", type=Path, default=BASE)
    ap.add_argument("--scan", type=Path, required=True)
    ap.add_argument("--config", type=Path, default=Path("config/v3_post_bdt_veto_sequence.json"))
    ap.add_argument("--output-dir", type=Path, required=True)
    args = ap.parse_args()
    scan = json.loads(args.scan.read_text())
    cfg = json.loads(args.config.read_text())
    if scan["config_sha256"] != sha(args.config):
        raise ValueError("Scan and veto configuration differ")
    root = args.base / "stage2_v3_phsp_100k_bdt1091peak"
    baseline = root / "v3_phsp_100k_angle_bdt1091peak"
    generated_path = baseline / "generated_direct_decays.parquet"
    candidates_path = root / "stage2/offline_selected/signal_phsp_v3_-2.parquet"
    generated = pd.read_parquet(generated_path)
    raw = pd.read_parquet(candidates_path, columns=list(COLS))
    if len(generated) != 100007 or len(raw) != 57753:
        raise ValueError("PHSP input differs from frozen 100k study")
    direct, error = match_generated(raw, generated)
    if direct.duplicated(["source_id", "event_entry", "candidate_slot"]).any():
        raise ValueError("Repeated PHSP candidate key")
    alpha = direct.arm_alpha.abs()
    qt = direct.arm_qt
    box = cfg["armenteros_reject_box"]
    arm = ~((alpha >= box["abs_alpha_min"]) & (alpha <= box["abs_alpha_max"]) &
            (qt >= box["qt_min_gev"]) & (qt <= box["qt_max_gev"]))
    previous = float(scan["fixed_previous_score"])
    new = float(scan["choices"]["arm_only"]["validation_maximum"]["score"])
    stages = {"offline": direct,
              "old_bdt_arm": direct.loc[(direct.bdt_score >= previous) & arm],
              "new_bdt_arm": direct.loc[(direct.bdt_score >= new) & arm],
              "new_bdt_arm_eta": direct.loc[(direct.bdt_score >= new) & arm & direct.pass_eta.astype(bool)]}
    results = {name: stage_result(frame, generated) for name, frame in stages.items()}
    for name, frame in stages.items():
        unique = frame.sort_values("bdt_score", ascending=False).drop_duplicates("generated_decay_id")
        residual = unique.cos_theta_p.to_numpy() - unique.generated_truth_angle.to_numpy()
        migration = np.histogram2d(unique.generated_truth_angle,
                                   unique.cos_theta_p, bins=(BINS, BINS))[0].astype(int)
        den = np.array(results[name]["generated_bin_counts"])
        results[name]["resolution"] = {
            "median_reco_minus_truth": float(np.median(residual)),
            "central_68pct_half_width": float((np.quantile(residual, .84)-np.quantile(residual, .16))/2),
            "rms": float(np.sqrt(np.mean(residual**2))),
            "fraction_abs_gt_0p1": float(np.mean(np.abs(residual) > .1)),
            "migration_truth_rows_reco_columns": migration.tolist(),
            "response_per_generated_decay_truth_rows_reco_columns":
                (migration / den[:, None]).tolist()}
    args.output_dir.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(9.2, 5.8))
    centers = (BINS[:-1] + BINS[1:]) / 2
    for name, label, color in (("offline", "Offline selected", "#8b8b8b"),
                               ("old_bdt_arm", "Old score + Armenteros", "#d89428"),
                               ("new_bdt_arm", "New score + Armenteros", "#2670a8"),
                               ("new_bdt_arm_eta", "New score + Armenteros + η", "#ba4148")):
        row = results[name]
        eff = np.array(row["efficiency"])
        lo, hi = np.array(row["binomial_68pct_interval"]).T
        ax.errorbar(centers, eff, yerr=(eff-lo, hi-eff), fmt="o-", capsize=2,
                    color=color, label=f"{label}: {row['unique_selected_decays']:,}")
    ax.set(xlabel=r"Generated $\cos\theta_p$",
           ylabel="Unique selected direct decays / generated direct decays",
           xlim=(-1, 1), ylim=(0, 1), title="v3 100k PHSP angular acceptance at the reoptimized score")
    ax.grid(alpha=.2)
    ax.legend(frameon=False, fontsize=9)
    fig.tight_layout()
    fig.savefig(args.output_dir / "phsp_reoptimized_acceptance.png", dpi=180)
    plt.close(fig)
    response = np.array(results["new_bdt_arm"]["resolution"]["response_per_generated_decay_truth_rows_reco_columns"])
    fig, ax = plt.subplots(figsize=(7.7, 5.8))
    im = ax.imshow(response, origin="lower", extent=(-1, 1, -1, 1), aspect="auto", cmap="viridis")
    fig.colorbar(im, ax=ax, label="Selected candidates / generated truth-bin decay")
    ax.set(xlabel=r"Reconstructed $\cos\theta_p$", ylabel=r"Generated $\cos\theta_p$",
           title="Acceptance × migration, new score + Armenteros")
    fig.tight_layout()
    fig.savefig(args.output_dir / "phsp_reoptimized_response.png", dpi=180)
    plt.close(fig)
    pd.DataFrame({"truth_low": BINS[:-1], "truth_high": BINS[1:],
                  "generated_decays": results["new_bdt_arm"]["generated_bin_counts"],
                  **{name + "_selected": row["selected_bin_counts"] for name, row in results.items()},
                  **{name + "_efficiency": row["efficiency"] for name, row in results.items()}}).to_csv(
                      args.output_dir / "phsp_reoptimized_acceptance_for_fit.csv", index=False)
    output = {"script_sha256": sha(Path(__file__)), "scan": str(args.scan),
              "scan_sha256": sha(args.scan), "config_sha256": sha(args.config),
              "generated": str(generated_path), "generated_sha256": sha(generated_path),
              "candidates": str(candidates_path), "candidates_sha256": sha(candidates_path),
              "generated_direct_decays": len(generated), "maximum_angle_match_error": error,
              "old_score": previous, "new_score": new,
              "bin_edges": BINS.tolist(), "stages": results}
    (args.output_dir / "phsp_reoptimized_acceptance.json").write_text(json.dumps(output, indent=2) + "\n")
    print(json.dumps({name: {"selected": row["unique_selected_decays"],
                             "efficiency": row["unique_selected_decays"]/len(generated),
                             "resolution": {key: value for key, value in row["resolution"].items()
                                            if key not in ("migration_truth_rows_reco_columns",
                                                           "response_per_generated_decay_truth_rows_reco_columns")}}
                      for name, row in results.items()}, indent=2))


if __name__ == "__main__":
    main()

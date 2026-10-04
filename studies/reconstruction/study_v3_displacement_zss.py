#!/usr/bin/env python3
"""Paired post-BDT Lambda displacement scan on full v3 flavour samples.

All cuts use reconstructed quantities. Truth is used after selection to split
direct signal and nonmatched inclusive candidates; forced modes stay separate.
"""

import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pyarrow.parquet as pq
from scipy.stats import chi2

from study_v3_post_bdt_veto_sequence import stages, COLORS, LABELS
from study_v3_post_bdt_armenteros import ancestry
import v3_plot_style  # noqa: F401


COLS = ("source_id", "event_entry", "candidate_slot", "lb_mass",
        "cos_theta_p", "truth_matched", "bdt_score", "arm_alpha", "arm_qt",
        "pass_pi0", "pass_eta", "lambda_d0_sig", "lambda_flight_xyz_sig",
        "proton_mc_pdg", "pion_mc_pdg", "photon_mc_pdg",
        "proton_mc_parent_pdg", "pion_mc_parent_pdg",
        "photon_mc_parent_pdg", "proton_mc_parent_index",
        "pion_mc_parent_index", "photon_mc_grandparent_pdg")
D0_THRESHOLDS = (0, 1, 2, 3, 4, 5, 6, 8, 10, 12, 15, 20, 30)
FLIGHT_THRESHOLDS = (0, 50, 100, 150, 200, 300, 500)
COMPONENTS = ("signal", "signal_wrong", "zbb", "zcc", "zss", "eta", "pi0")
INCLUSIVE = ("zbb", "zcc", "zss")


def digest(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def read_one(path, score):
    frame = pq.read_table(path, columns=list(COLS), use_threads=False).to_pandas()
    return frame.loc[frame.bdt_score >= score].copy()


def read_many(paths, score, workers):
    if not paths:
        raise ValueError("No candidate tables")
    with ThreadPoolExecutor(max_workers=workers) as pool:
        return pd.concat(pool.map(lambda path: read_one(path, score), paths),
                         ignore_index=True)


def check_keys(frame, name):
    if frame.duplicated(["source_id", "event_entry", "candidate_slot"]).any():
        raise ValueError(f"Repeated candidate key: {name}")


def interval(n, weight):
    return [float((.5 * chi2.ppf(.025, 2*n) if n else 0) * weight),
            float(.5 * chi2.ppf(.975, 2*(n+1)) * weight)]


def selected(frame, stage, cfg):
    return frame.loc[stages(frame, cfg["armenteros_reject_box"])[stage]].copy()


def scan_row(frames, weights, variable, threshold, baseline, stage, mass_window):
    rows = {}
    for name, frame in frames.items():
        value = frame.lambda_d0_sig.abs() if variable == "abs_lambda_d0_sig" else \
                frame.lambda_flight_xyz_sig
        chosen = frame.loc[frame.lb_mass.between(*mass_window) &
                           np.isfinite(value) & (value >= threshold)]
        count = len(chosen)
        rows[name] = {"candidate_rows": count,
                      "candidate_bearing_events": int(chosen[["source_id", "event_entry"]]
                                                       .drop_duplicates().shape[0]),
                      "expected_candidates": float(count * weights[name]),
                      "candidate_count_95pct_expected_interval": interval(count, weights[name]),
                      "conditional_retention": count / baseline[name] if baseline[name] else None}
        if name == "zss":
            rows[name]["truth_pair_origin_after_selection"] = {
                label: int(n) for label, n in chosen.pair_origin.value_counts().items()}
    s = rows["signal"]["expected_candidates"]
    b = sum(rows[name]["expected_candidates"] for name in INCLUSIVE)
    return {"stage": stage, "variable": variable, "threshold": threshold,
            "components": rows, "inclusive_S": s, "inclusive_B": b,
            "inclusive_purity": s / (s+b) if s+b else None,
            "inclusive_S_over_sqrt_S_plus_B": s / np.sqrt(s+b) if s+b else None,
            "forced_modes_are_separate": True}


def plot_retention(rows, output):
    fig, axes = plt.subplots(2, 2, figsize=(12.8, 8.2))
    for j, variable in enumerate(("abs_lambda_d0_sig", "lambda_flight_xyz_sig")):
        subset = [row for row in rows if row["stage"] == "post_bdt_armenteros_pi0_eta" and
                  row["variable"] == variable]
        xx = [row["threshold"] for row in subset]
        for name in ("signal", "zbb", "zcc", "zss"):
            axes[0, j].plot(xx, [row["components"][name]["conditional_retention"]
                                 for row in subset], marker="o", ms=3,
                            label=LABELS[name], color=COLORS[name])
        axes[1, j].plot(xx, [row["inclusive_S_over_sqrt_S_plus_B"]
                             for row in subset], marker="o", ms=3,
                        color="#2670a8", label=r"$S/\sqrt{S+B}$")
        axes[1, j].plot(xx, [1000*row["inclusive_purity"] for row in subset],
                        marker="s", ms=3, color="#aa4249", label="Purity ×1000")
        xlabel = (r"Minimum $|d_0(\Lambda)/\sigma|$" if j == 0 else
                  r"Minimum PV-to-$\Lambda$ 3D flight significance")
        axes[1, j].set_xlabel(xlabel)
        axes[0, j].set_title(xlabel)
    axes[0, 0].set_ylabel("Conditional peak candidate retention")
    axes[1, 0].set_ylabel("Central peak counting metric / purity ×1000")
    for ax in axes.flat:
        ax.grid(alpha=.2)
        ax.legend(frameon=False, fontsize=8)
    fig.suptitle(r"After fixed BDT + Armenteros + $\pi^0$ + $\eta$ proposals; "
                 "physically weighted inclusive backgrounds", fontsize=12)
    fig.tight_layout()
    fig.savefig(output, dpi=180)
    plt.close(fig)


def plot_mass_angle(frames, weights, outpath, threshold):
    fig, axes = plt.subplots(2, 2, figsize=(13.5, 8.2))
    edges = {"mass": np.linspace(4.7, 6.5, 73),
             "angle": np.linspace(-1, 1, 21)}
    for row, use_d0 in enumerate((False, True)):
        for col, axis in enumerate(("mass", "angle")):
            ax = axes[row, col]
            for name in COMPONENTS:
                frame = frames[name]
                if use_d0:
                    frame = frame.loc[frame.lambda_d0_sig.abs() >= threshold]
                values = frame.lb_mass if axis == "mass" else frame.cos_theta_p
                hist, _ = np.histogram(values, bins=edges[axis])
                ax.stairs(hist*weights[name], edges[axis], color=COLORS[name],
                          label=LABELS[name], linewidth=1.55)
            if axis == "mass":
                ax.axvspan(5.4, 5.9, alpha=.18, color="gray")
            ax.set_title(("Existing final sequence" if not use_d0 else
                          rf"Also $|d_0(\Lambda)/\sigma|\geq{threshold}$") +
                         (" — mass" if axis == "mass" else " — cos θp"))
            ax.grid(alpha=.2)
    for ax in axes[:, 0]:
        ax.set_ylabel("Expected candidate rows / 25 MeV")
    for ax in axes[:, 1]:
        ax.set_ylabel("Expected candidate rows / 0.1")
    for col in range(2):
        top = max(axes[0, col].get_ylim()[1], axes[1, col].get_ylim()[1])
        for ax in axes[:, col]:
            ax.set_ylim(0, top)
    axes[1, 0].set_xlabel(r"Reconstructed $m(\Lambda\gamma)$ [GeV]")
    axes[1, 1].set_xlabel(r"Reconstructed $\cos\theta_p$")
    handles, labels = axes[0, 0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="lower center", ncol=4, frameon=False,
               fontsize=8, bbox_to_anchor=(.5, -.02))
    fig.suptitle("Paired linear-scale expected candidate distributions", fontsize=13)
    fig.tight_layout(rect=(0, .055, 1, .96))
    fig.savefig(outpath, dpi=180, bbox_inches="tight")
    plt.close(fig)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    for name in ("signal", "zbb_scored_dir", "zbb_catalog", "zcc_summary",
                 "zss_summary", "eta", "pi0", "eta_summary", "pi0_summary",
                 "projection", "output_dir"):
        ap.add_argument("--" + name.replace("_", "-"), type=Path, required=True)
    ap.add_argument("--config", type=Path,
                    default=Path("config/v3_post_bdt_veto_sequence.json"))
    ap.add_argument("--workers", type=int, default=16)
    args = ap.parse_args()
    if args.workers < 1:
        ap.error("workers must be positive")
    cfg = json.loads(args.config.read_text())
    projection = json.loads(args.projection.read_text())
    score = float(projection["validation_choice"]["score"])
    catalog = json.loads(args.zbb_catalog.read_text())
    paths = sorted(args.zbb_scored_dir.glob("zbb_*_selected.parquet"))
    expected_names = {f"zbb_{item['chunk_id']}_selected.parquet" for item in catalog["chunks"]}
    if {p.name for p in paths} != expected_names:
        raise ValueError("Zbb shards differ from frozen catalog")
    signal = read_one(args.signal, score)
    zbb = read_many(paths, score, args.workers)
    frames = {"signal": signal.loc[signal.truth_matched == 1].copy(),
              "signal_wrong": signal.loc[signal.truth_matched != 1].copy(),
              "zbb": zbb.loc[zbb.truth_matched != 1].copy(),
              "eta": read_one(args.eta, score),
              "pi0": read_one(args.pi0, score)}
    input_meta = {"signal": str(args.signal), "zbb_catalog": str(args.zbb_catalog),
                  "zbb_catalog_sha256": digest(args.zbb_catalog),
                  "eta": str(args.eta), "pi0": str(args.pi0)}
    for name in ("zcc", "zss"):
        path = getattr(args, f"{name}_summary")
        summary = json.loads(path.read_text())
        if (summary["sample"] != name or not summary["complete_catalog"] or
                summary["run_identity"]["score_cut"] != score or
                summary["run_identity"]["model_sha256"] != projection["model_sha256"]):
            raise ValueError(f"{name} summary is not the frozen full sample")
        paths = sorted(path.parent.glob("chunks/chunk_*/bdt_selected.parquet"))
        if len(paths) != summary["input_chunks"]:
            raise ValueError(f"{name} chunk table count changed")
        all_rows = read_many(paths, score, args.workers)
        if len(all_rows) != summary["stage_counts"]["bdt_selected"]["candidate_rows"]:
            raise ValueError(f"{name} BDT row count changed")
        frames[name] = all_rows.loc[all_rows.truth_matched != 1].copy()
        if name == "zss":
            ancestry(frames[name])
        input_meta[name] = {"summary": str(path), "summary_sha256": digest(path),
                            "processed_input_events": summary["processed_input_events"]}
    for name, frame in frames.items():
        check_keys(frame, name)
    br = cfg["branching_fractions"]
    common = (cfg["N_Z"] * br["Zbb"] * 2 * cfg["f_Lambdab_per_b"] *
              br["Lb_to_Lambda_gamma"] * br["Lambda_to_p_pi"])
    signal_weight = common / cfg["signal_generated_direct_decays"]
    weights = {"signal": signal_weight, "signal_wrong": signal_weight,
               "zbb": cfg["N_Z"] * br["Zbb"] /
               catalog["total_processed_events_in_valid_chunks"],
               "zcc": cfg["N_Z"] * br["Zcc"] / input_meta["zcc"]["processed_input_events"],
               "zss": cfg["N_Z"] * br["Zss"] / input_meta["zss"]["processed_input_events"]}
    for name in ("eta", "pi0"):
        path = getattr(args, f"{name}_summary")
        summary = json.loads(path.read_text())
        if summary["bdt_score"] != score or summary["model_sha256"] != projection["model_sha256"]:
            raise ValueError(f"{name} uses another BDT")
        weights[name] = summary["projected_candidates"]["factor_before_selection"] / \
                        summary["generated_direct_decays"]
        input_meta[name + "_summary_sha256"] = digest(path)
    selected_frames = {}
    rows = []
    for stage in ("post_bdt", "post_bdt_armenteros_pi0_eta"):
        subset = {name: selected(frame, stage, cfg) for name, frame in frames.items()}
        selected_frames[stage] = subset
        baseline = {name: int(frame.lb_mass.between(*cfg["mass_window_gev"]).sum())
                    for name, frame in subset.items()}
        for variable, thresholds in (("abs_lambda_d0_sig", D0_THRESHOLDS),
                                     ("lambda_flight_xyz_sig", FLIGHT_THRESHOLDS)):
            for threshold in thresholds:
                rows.append(scan_row(subset, weights, variable, threshold,
                                     baseline, stage, cfg["mass_window_gev"]))
    args.output_dir.mkdir(parents=True, exist_ok=True)
    training_path = Path(projection["training_summary"])
    features = json.loads(training_path.read_text())["features"]
    result = {"question": "Does a reconstructed Lambda displacement cut suppress Zss?",
              "config": str(args.config), "config_sha256": digest(args.config),
              "projection": str(args.projection), "projection_sha256": digest(args.projection),
              "score": score, "mass_window_gev": cfg["mass_window_gev"],
              "training_summary": str(training_path),
              "training_summary_sha256": digest(training_path),
              "abs_lambda_d0_sig_in_bdt_features": "lambda_d0_sig" in features,
              "lambda_flight_xyz_sig_in_bdt_features": "lambda_flight_xyz_sig" in features,
              "input_meta": input_meta, "weights": weights,
              "forced_mode_note": "Shown separately; may overlap inclusive Zbb",
              "scan": rows}
    (args.output_dir / "displacement_scan.json").write_text(json.dumps(result, indent=2) + "\n")
    flat = pd.DataFrame([{"stage": row["stage"], "variable": row["variable"],
                          "threshold": row["threshold"], "inclusive_S": row["inclusive_S"],
                          "inclusive_B": row["inclusive_B"],
                          "inclusive_purity": row["inclusive_purity"],
                          "inclusive_S_over_sqrt_S_plus_B": row["inclusive_S_over_sqrt_S_plus_B"],
                          **{f"{name}_raw": item["candidate_rows"]
                             for name, item in row["components"].items()},
                          **{f"{name}_expected": item["expected_candidates"]
                             for name, item in row["components"].items()}}
                         for row in rows])
    flat.to_csv(args.output_dir / "displacement_scan.csv", index=False)
    plot_retention(rows, args.output_dir / "displacement_retention_linear.png")
    plot_mass_angle(selected_frames["post_bdt_armenteros_pi0_eta"], weights,
                    args.output_dir / "mass_angle_d0sig5_linear.png", 5)
    print(flat.loc[(flat.stage == "post_bdt_armenteros_pi0_eta") &
                   (flat.variable == "abs_lambda_d0_sig") &
                   flat.threshold.isin([0, 3, 5, 8]),
                   ["threshold", "signal_raw", "zbb_raw", "zcc_raw", "zss_raw",
                    "inclusive_purity", "inclusive_S_over_sqrt_S_plus_B"]].to_string(index=False))


if __name__ == "__main__":
    main()

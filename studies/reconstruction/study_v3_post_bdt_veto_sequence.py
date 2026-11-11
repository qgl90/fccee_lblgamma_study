#!/usr/bin/env python3
"""Compare four reconstructed post-BDT cuts with physical candidate weights.

Truth labels separate direct signal, signal wrong combinations and nonmatched
inclusive flavours; no truth field enters any cut. Forced meson modes are shown
separately from inclusive Zbb because their event overlap is not audited.
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

import v3_plot_style  # noqa: F401


COLUMNS = ("source_id", "event_entry", "candidate_slot", "lb_mass",
           "cos_theta_p", "truth_matched", "arm_alpha", "arm_qt",
           "pass_pi0", "pass_eta", "bdt_score")
STAGES = ("post_bdt", "post_bdt_armenteros", "post_bdt_armenteros_pi0",
          "post_bdt_armenteros_pi0_eta")
LABELS = {"signal": r"Direct $\Lambda_b\to\Lambda\gamma$",
          "signal_wrong": "Signal wrong combinations",
          "zbb": r"Nonmatched $Z\to b\bar b$",
          "eta": r"Forced $\Lambda\eta(\gamma\gamma)$",
          "pi0": r"Forced $\Lambda\pi^0(\gamma\gamma)$",
          "zcc": r"Nonmatched $Z\to c\bar c$",
          "zss": r"Nonmatched $Z\to s\bar s$"}
COLORS = {"signal": "#2670a8", "signal_wrong": "#8b8b8b",
          "zbb": "#252525", "eta": "#ba4148", "pi0": "#d89428",
          "zcc": "#6b4fa1", "zss": "#198466"}


def digest(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def read_scored(path, score):
    schema = set(pq.read_schema(path).names)
    if not set(COLUMNS) <= schema:
        raise ValueError(f"Missing post-BDT columns in {path}: {sorted(set(COLUMNS)-schema)}")
    frame = pq.read_table(path, columns=list(COLUMNS)).to_pandas()
    return frame.loc[frame.bdt_score >= score].copy()


def read_many(paths, score, workers):
    with ThreadPoolExecutor(max_workers=workers) as pool:
        frames = list(pool.map(lambda p: read_scored(p, score), paths))
    if not frames:
        raise ValueError("No scored candidate shards")
    return pd.concat(frames, ignore_index=True)


def stages(frame, box):
    alpha, qt = np.abs(frame.arm_alpha.to_numpy()), frame.arm_qt.to_numpy()
    reject = ((alpha >= box["abs_alpha_min"]) &
              (alpha <= box["abs_alpha_max"]) &
              (qt >= box["qt_min_gev"]) & (qt <= box["qt_max_gev"]))
    arm = ~reject
    pi0 = frame.pass_pi0.to_numpy(dtype=bool)
    eta = frame.pass_eta.to_numpy(dtype=bool)
    return dict(zip(STAGES, (np.ones(len(frame), dtype=bool), arm,
                             arm & pi0, arm & pi0 & eta)))


def interval(count, weight):
    return [(0.5 * chi2.ppf(.025, 2 * count) if count else 0.) * weight,
            0.5 * chi2.ppf(.975, 2 * (count + 1)) * weight]


def count_rows(frame, mask, weight, mass_window):
    selected = frame.loc[mask]
    peak = selected.lb_mass.between(*mass_window)
    n = int(peak.sum())
    return {"candidate_rows": len(selected),
            "candidate_bearing_events": int(selected[["source_id", "event_entry"]]
                                            .drop_duplicates().shape[0]),
            "peak_candidate_rows": n,
            "peak_candidate_bearing_events": int(selected.loc[peak, ["source_id", "event_entry"]]
                                                 .drop_duplicates().shape[0]),
            "expected_full_mass_candidates": len(selected) * weight,
            "expected_peak_candidates": n * weight,
            "expected_peak_mc_95pct_candidate_interval": interval(n, weight)}


def draw_sequence(frames, weights, config, outdir, axis, zoom=False, only_pi0=False):
    mass = axis == "mass"
    edges = np.linspace(4.7, 6.5, 73) if mass else np.linspace(-1., 1., 21)
    column = "lb_mass" if mass else "cos_theta_p"
    title = {"post_bdt": "Fixed BDT", "post_bdt_armenteros": "+ Armenteros box",
             "post_bdt_armenteros_pi0": r"+ $\pi^0$ veto",
             "post_bdt_armenteros_pi0_eta": r"+ $\eta$ veto"}
    order = [name for name in LABELS if name in frames]
    if only_pi0:
        order = ["pi0"]
    elif zoom:
        order = [name for name in order if name in ("eta", "pi0", "signal_wrong", "zcc", "zss")]
    fig, axes = plt.subplots(2, 2, figsize=(14.5, 8.7), sharex=True, sharey=True)
    ymax = 0.
    for ax, stage in zip(axes.flat, STAGES):
        for name in order:
            frame = frames[name]
            values = frame.loc[stages(frame, config["armenteros_reject_box"])[stage], column]
            hist, _ = np.histogram(values, bins=edges)
            expected = hist * weights[name]
            ymax = max(ymax, float(expected.max(initial=0.)))
            ax.stairs(expected, edges, label=LABELS[name], color=COLORS[name],
                      linewidth=1.6, linestyle="--" if name == "signal_wrong" else "-")
        if mass:
            ax.axvspan(*config["mass_window_gev"], color="0.88", alpha=.7)
        ax.set_title(title[stage])
        ax.grid(alpha=.2)
    for ax in axes.flat:
        ax.set_ylim(0, ymax * 1.10 if ymax else 1)
    for ax in axes[-1]:
        ax.set_xlabel(r"Reconstructed $m(\Lambda\gamma)$ [GeV]" if mass
                      else r"Reconstructed $\cos\theta_p$")
    for ax in axes[:, 0]:
        ax.set_ylabel("Expected candidate rows / 25 MeV" if mass
                      else "Expected candidate rows / 0.1")
    handles, labels = axes.flat[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="lower center", ncol=3, fontsize=9,
               bbox_to_anchor=(.5, -.02), frameon=False)
    fig.suptitle(("$\\Lambda\\pi^0$ detail" if only_pi0 else
                  "Feed-down / light-flavour detail" if zoom else "All components") +
                 ": linear expected-candidate scale", fontsize=13)
    fig.tight_layout(rect=(0, .055, 1, .965))
    suffix = "pi0_" if only_pi0 else "detail_" if zoom else ""
    path = outdir / f"sequence_{axis}_{suffix}linear.png"
    fig.savefig(path, dpi=180, bbox_inches="tight")
    plt.close(fig)
    return path


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--signal", type=Path, required=True)
    ap.add_argument("--zbb-scored-dir", type=Path, required=True)
    ap.add_argument("--zbb-catalog", type=Path, required=True)
    ap.add_argument("--eta", type=Path, required=True)
    ap.add_argument("--pi0", type=Path, required=True)
    ap.add_argument("--eta-summary", type=Path, required=True)
    ap.add_argument("--pi0-summary", type=Path, required=True)
    ap.add_argument("--projection", type=Path, required=True)
    ap.add_argument("--config", type=Path, default=Path("config/v3_post_bdt_veto_sequence.json"))
    ap.add_argument("--zcc-summary", type=Path)
    ap.add_argument("--zss-summary", type=Path)
    ap.add_argument("--workers", type=int, default=12)
    ap.add_argument("--output-dir", type=Path, required=True)
    args = ap.parse_args()
    cfg = json.loads(args.config.read_text())
    projection = json.loads(args.projection.read_text())
    score = float(projection["validation_choice"]["score"])
    catalog = json.loads(args.zbb_catalog.read_text())
    paths = sorted(args.zbb_scored_dir.glob("zbb_*_selected.parquet"))
    expected_names = {f"zbb_{item['chunk_id']}_selected.parquet" for item in catalog["chunks"]}
    if {p.name for p in paths} != expected_names:
        raise ValueError("Zbb scored shards differ from the frozen catalog")
    if len(catalog["chunks"]) != catalog["valid_chunks"] or catalog["invalid_chunks"]:
        raise ValueError("Zbb catalog is incomplete or invalid")
    frames = {}
    signal_all = read_scored(args.signal, score)
    frames["signal"] = signal_all.loc[signal_all.truth_matched == 1].copy()
    frames["signal_wrong"] = signal_all.loc[signal_all.truth_matched != 1].copy()
    zbb_all = read_many(paths, score, args.workers)
    frames["zbb"] = zbb_all.loc[zbb_all.truth_matched != 1].copy()
    frames["eta"] = read_scored(args.eta, score)
    frames["pi0"] = read_scored(args.pi0, score)
    br = cfg["branching_fractions"]
    common = (cfg["N_Z"] * br["Zbb"] * 2 * cfg["f_Lambdab_per_b"] *
              br["Lb_to_Lambda_gamma"] * br["Lambda_to_p_pi"])
    signal_weight = common / cfg["signal_generated_direct_decays"]
    weights = {"signal": signal_weight, "signal_wrong": signal_weight,
               "zbb": cfg["N_Z"] * br["Zbb"] / catalog["total_processed_events_in_valid_chunks"]}
    for name, summary_path in (("eta", args.eta_summary), ("pi0", args.pi0_summary)):
        summary = json.loads(summary_path.read_text())
        if summary["bdt_score"] != score or summary["model_sha256"] != projection["model_sha256"]:
            raise ValueError(f"{name} uses another BDT")
        weights[name] = (summary["projected_candidates"]["factor_before_selection"] /
                         summary["generated_direct_decays"])
    extras = {"zcc": args.zcc_summary, "zss": args.zss_summary}
    for name, path in extras.items():
        if path is None:
            continue
        summary = json.loads(path.read_text())
        if not summary["complete_catalog"] or summary["sample"] != name or \
                summary["run_identity"]["score_cut"] != score or \
                summary["run_identity"]["model_sha256"] != projection["model_sha256"]:
            raise ValueError(f"{name} summary is incomplete or has another model")
        root = path.parent
        shards = sorted(root.glob("chunks/chunk_*/bdt_selected.parquet"))
        if len(shards) != summary["input_chunks"]:
            raise ValueError(f"{name} has missing BDT tables")
        all_rows = read_many(shards, score, args.workers)
        frames[name] = all_rows.loc[all_rows.truth_matched != 1].copy()
        weights[name] = cfg["N_Z"] * br[{"zcc": "Zcc", "zss": "Zss"}[name]] / summary["processed_input_events"]
    result = {"config": str(args.config), "config_sha256": digest(args.config),
              "model_sha256": projection["model_sha256"], "bdt_score": score,
              "zbb_catalog": str(args.zbb_catalog),
              "zbb_catalog_sha256": digest(args.zbb_catalog),
              "input_files": {"signal": str(args.signal), "eta": str(args.eta),
                              "pi0": str(args.pi0), "zbb_scored_dir": str(args.zbb_scored_dir)},
              "scales_per_candidate": weights,
              "raw_diagnostics": {"zbb_direct_signal_after_bdt": int((zbb_all.truth_matched == 1).sum()),
                                  "signal_wrong_after_bdt": len(frames["signal_wrong"])},
              "stages": {}, "overlap_note": cfg["interpretation"]}
    for stage in STAGES:
        result["stages"][stage] = {}
        for name, frame in frames.items():
            mask = stages(frame, cfg["armenteros_reject_box"])[stage]
            counts = count_rows(frame, mask, weights[name], cfg["mass_window_gev"])
            result["stages"][stage][name] = counts
    for name in frames:
        previous = None
        baseline = result["stages"][STAGES[0]][name]["peak_candidate_rows"]
        for stage in STAGES:
            item = result["stages"][stage][name]
            count = item["peak_candidate_rows"]
            item["peak_conditional_retention"] = count / previous if previous else None
            item["peak_cumulative_retention"] = count / baseline if baseline else None
            previous = count
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "summary.json").write_text(json.dumps(result, indent=2) + "\n")
    table = pd.DataFrame([{"stage": stage, "component": name, **item}
                          for stage, values in result["stages"].items()
                          for name, item in values.items()])
    table.to_csv(args.output_dir / "stage_counts.csv", index=False)
    for axis in ("mass", "angle"):
        draw_sequence(frames, weights, cfg, args.output_dir, axis)
        draw_sequence(frames, weights, cfg, args.output_dir, axis, zoom=True)
        draw_sequence(frames, weights, cfg, args.output_dir, axis, only_pi0=True)
    print(json.dumps({stage: {name: round(item["expected_peak_candidates"], 2)
                              for name, item in values.items()}
                      for stage, values in result["stages"].items()}, indent=2))


if __name__ == "__main__":
    main()

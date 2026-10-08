#!/usr/bin/env python3
"""Stream v3 signal/Zbb/Zcc/Zss feature histograms before and after frozen BDT.

Truth labels are used only to report direct signal and nonmatched backgrounds.
All plotted observables and all selections are reconstructed quantities.
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
import pyarrow.parquet as pq

import v3_plot_style  # noqa: F401


BASE = Path("/eos/lhcb/lbdt3/user/rquaglia/fcc_ee/lblgamma/outputs")
FEATURES = {
    "lb_E": (10, 46, "Λb candidate energy [GeV]"),
    "gamma_E": (2, 42, "Photon energy [GeV]"),
    "lambda_p": (0, 43, "Λ momentum [GeV]"),
    "proton_d0sig": (0, 500, "Proton impact-parameter significance"),
    "pion_d0sig": (0, 1500, "Pion impact-parameter significance"),
    "lambda_flight_xyz_sig": (0, 4000, "PV-to-Λ-SV flight significance"),
    "abs_lambda_d0_sig": (0, 60, "|Λ trajectory impact-parameter significance|"),
    "lb_thrust_abs_cos": (.5, 1.0, "|cos(Λb, thrust axis)|"),
    "iso_R03_all_energy_over_gamma_E": (0, 8, "Photon R03 isolation ΣE/Eγ"),
    "iso_R05_charged_n": (0, 12, "Photon R05 charged multiplicity"),
    "lambda0_iso_R05_charged_n_d0": (0, 12, "Λ R05 displaced charged multiplicity"),
    "z_partial_deltaE": (-55, 5, "Partial Z energy residual [GeV]"),
    "z_partial_deltaP": (0, 40, "Partial Z momentum residual [GeV]"),
    "d_pi0": (0, .8, "Nearest π⁰ diphoton mass distance [GeV]"),
    "d_eta": (0, .6, "Nearest η diphoton mass distance [GeV]"),
    "min_pair": (0, 1.2, "Nearest photon-pair diagnostic [GeV]"),
    "abs_arm_alpha": (0, 1, "Armenteros |α|"),
    "arm_qt": (0, .2, "Armenteros qT [GeV]"),
}
PAGES = {
    "kinematics": ("lb_E", "gamma_E", "lambda_p", "lb_thrust_abs_cos", "z_partial_deltaE", "z_partial_deltaP"),
    "topology": ("proton_d0sig", "pion_d0sig", "lambda_flight_xyz_sig", "abs_lambda_d0_sig", "abs_arm_alpha", "arm_qt"),
    "activity": ("iso_R03_all_energy_over_gamma_E", "iso_R05_charged_n", "lambda0_iso_R05_charged_n_d0", "d_pi0", "d_eta", "min_pair"),
}
NAMES = ("signal", "zbb", "zcc", "zss")
LABEL = {"signal": "Direct Λb→Λγ", "zbb": "Z→bb", "zcc": "Z→cc", "zss": "Z→ss"}
COLOR = {"signal": "#2670a8", "zbb": "#252525", "zcc": "#6b4fa1", "zss": "#198466"}
STAGES = ("pre_bdt", "post_bdt", "post_bdt_vetoes")
STAGE_TITLE = ("before BDT", "after frozen BDT", "after BDT and veto proposals")
SCORE_EDGES = np.r_[np.linspace(0, .9, 46), np.linspace(.9, .99, 46)[1:],
                    np.linspace(.99, 1, 51)[1:]]
READ_COLS = tuple(dict.fromkeys(("truth_matched", "bdt_score", "lb_mass", "cos_theta_p",
                                  "arm_alpha", "arm_qt", "pass_pi0", "pass_eta",
                                  *("lambda_d0_sig" if k == "abs_lambda_d0_sig" else
                                    "arm_alpha" if k == "abs_arm_alpha" else k
                                    for k in FEATURES))))


def sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def values(table, name):
    source = "lambda_d0_sig" if name == "abs_lambda_d0_sig" else \
             "arm_alpha" if name == "abs_arm_alpha" else name
    arr = table[source].to_numpy(zero_copy_only=False).astype(float, copy=False)
    return np.where(arr > -998., np.abs(arr), np.nan) if name.startswith("abs_") else arr


def hist_array(x, mask, edges):
    picked = x[mask]
    valid = np.isfinite(picked) & (picked > -998.)
    core = np.histogram(picked[valid], bins=edges)[0].astype(np.int64)
    return np.r_[int((picked[valid] < edges[0]).sum()), core,
                 int((picked[valid] > edges[-1]).sum()), int((~valid).sum())]


def process(item, score, box, edges):
    name, path = item
    table = pq.read_table(path, columns=list(READ_COLS), use_threads=False)
    n = table.num_rows
    truth = table["truth_matched"].to_numpy(zero_copy_only=False)
    class_mask = truth == 1 if name == "signal" else truth != 1
    bdt = table["bdt_score"].to_numpy(zero_copy_only=False) >= score
    alpha = np.abs(table["arm_alpha"].to_numpy(zero_copy_only=False))
    qt = table["arm_qt"].to_numpy(zero_copy_only=False)
    reject = ((alpha >= box["abs_alpha_min"]) & (alpha <= box["abs_alpha_max"]) &
              (qt >= box["qt_min_gev"]) & (qt <= box["qt_max_gev"]))
    veto = (~reject & table["pass_pi0"].to_numpy(zero_copy_only=False).astype(bool) &
            table["pass_eta"].to_numpy(zero_copy_only=False).astype(bool))
    masks = (class_mask, class_mask & bdt, class_mask & bdt & veto)
    mass = table["lb_mass"].to_numpy(zero_copy_only=False)
    angle = table["cos_theta_p"].to_numpy(zero_copy_only=False)
    peak_masks = tuple(m & (mass >= 5.4) & (mass <= 5.9) for m in masks)
    out = {"name": name, "rows": n, "counts": [int(m.sum()) for m in masks],
           "peak": [int(m.sum()) for m in peak_masks],
           "hist": {}, "peak_hist": {}}
    for key in FEATURES:
        x = values(table, key)
        out["hist"][key] = [hist_array(x, mask, edges[key]) for mask in masks]
        out["peak_hist"][key] = [hist_array(x, mask, edges[key]) for mask in peak_masks]
    out["mass"] = [np.histogram(mass[m], bins=np.linspace(4.7, 6.5, 73))[0]
                   for m in masks]
    out["angle"] = [np.histogram(angle[m], bins=np.linspace(-1, 1, 21))[0]
                    for m in masks]
    out["score_hist"] = np.histogram(table["bdt_score"].to_numpy(zero_copy_only=False)[class_mask],
                                     bins=SCORE_EDGES)[0]
    return out


def make_plot(results, stage, page, output, peak=False):
    fig, axes = plt.subplots(2, 3, figsize=(14.2, 8.1))
    for ax, key in zip(axes.flat, PAGES[page]):
        low, high, title = FEATURES[key]
        edges = np.linspace(low, high, 41)
        for name in NAMES:
            hist = np.array(results[name]["peak_hist" if peak else "hist"][key][stage], dtype=float)
            total = results[name]["peak" if peak else "counts"][stage]
            ax.stairs(hist[1:-2] / total if total else hist[1:-2], edges,
                      label=f"{LABEL[name]} ({total:,})", color=COLOR[name], linewidth=1.5)
        ax.set_title(title, fontsize=10)
        ax.set_ylabel("Fraction of class / bin")
        ax.grid(alpha=.2)
    handles, labels = axes.flat[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="upper center", bbox_to_anchor=(.5, .94),
               ncol=4, frameon=False, fontsize=9)
    window = "5.4–5.9 GeV peak" if peak else "full 4.7–6.5 GeV fit interval"
    fig.suptitle(f"v3 candidate shapes {STAGE_TITLE[stage]} • {window}", y=.995)
    fig.text(.5, .018, "Each class normalized separately; overflow and missing values remain in denominator",
             ha="center", fontsize=9)
    fig.tight_layout(rect=(0, .04, 1, .88))
    fig.savefig(output, dpi=170)
    plt.close(fig)


def make_yields(results, weights, stage, output):
    fig, axes = plt.subplots(1, 2, figsize=(13.5, 4.5))
    for name in NAMES:
        for ax, axis, edges in ((axes[0], "mass", np.linspace(4.7, 6.5, 73)),
                                (axes[1], "angle", np.linspace(-1, 1, 21))):
            ax.stairs(np.array(results[name][axis][stage]) * weights[name], edges,
                      label=LABEL[name], color=COLOR[name], linewidth=1.6)
    axes[0].axvspan(5.4, 5.9, alpha=.15, color="gray")
    axes[0].set(xlabel="Reconstructed m(Λγ) [GeV]", ylabel="Expected candidates / 25 MeV")
    axes[1].set(xlabel="Reconstructed cos θp", ylabel="Expected candidates / 0.1")
    for ax in axes:
        ax.set_ylim(bottom=0)
        ax.grid(alpha=.2)
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="lower center", ncol=4, frameon=False,
               bbox_to_anchor=(.5, -.025))
    fig.suptitle(f"v3 {STAGE_TITLE[stage]} • linear physical projection, 6×10¹² Z", fontsize=13)
    fig.tight_layout(rect=(0, .07, 1, .91))
    fig.savefig(output, dpi=170, bbox_inches="tight")
    plt.close(fig)


def make_score(results, weights, score, output):
    fig, axes = plt.subplots(1, 2, figsize=(13.5, 4.6))
    widths = np.diff(SCORE_EDGES)
    for name in NAMES:
        hist = results[name]["score_hist"].astype(float)
        axes[0].stairs(hist / hist.sum() / widths, SCORE_EDGES, label=LABEL[name], color=COLOR[name])
        axes[1].stairs(hist * weights[name] / widths, SCORE_EDGES, label=LABEL[name], color=COLOR[name])
    for ax in axes:
        ax.axvline(score, color="#ba4148", linestyle="--", linewidth=1.2)
        ax.set(xlabel="Frozen Zbb-trained BDT score", xlim=(.9, 1), yscale="log")
        ax.grid(alpha=.2)
    axes[0].set_ylabel("Fraction of class / unit score")
    axes[1].set_ylabel("Expected candidate rows / unit score")
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="lower center", ncol=4, frameon=False,
               bbox_to_anchor=(.5, -.025))
    fig.suptitle("Offline-selected v3 candidates • score tail before veto proposals", fontsize=13)
    fig.tight_layout(rect=(0, .07, 1, .91))
    fig.savefig(output, dpi=170, bbox_inches="tight")
    plt.close(fig)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--base", type=Path, default=BASE)
    ap.add_argument("--config", type=Path, default=Path("config/v3_post_bdt_veto_sequence.json"))
    ap.add_argument("--catalog", type=Path, default=Path("docs/data/stage2_v3_bdt_1091_peak/20261003_1091chunks.json"))
    ap.add_argument("--projection", type=Path, default=BASE / "stage2_v3_incremental/projections/20261004_1091chunks_peak_5p4_5p9/projection.json")
    ap.add_argument("--workers", type=int, default=16)
    ap.add_argument("--output-dir", type=Path, required=True)
    args = ap.parse_args()
    if args.workers < 1:
        ap.error("workers must be positive")
    cfg = json.loads(args.config.read_text())
    projection = json.loads(args.projection.read_text())
    catalog = json.loads(args.catalog.read_text())
    preparation_path = args.base / "stage2_v3_incremental/prepared/summary.json"
    preparation = json.loads(preparation_path.read_text())
    score = float(projection["validation_choice"]["score"])
    scored = args.base / "stage2_v3_incremental/models/20261004_1091chunks/scored_selected"
    signal_path = scored / "signal_-1_selected.parquet"
    zbb_paths = sorted(scored.glob("zbb_*_selected.parquet"))
    ids = {int(item["chunk_id"]) for item in catalog["chunks"]}
    if {int(p.stem.split("_")[1]) for p in zbb_paths} != ids:
        raise ValueError("Zbb shards differ from frozen 1091-chunk catalog")
    paths = [("signal", signal_path)] + [("zbb", p) for p in zbb_paths]
    summaries = {}
    for name in ("zcc", "zss"):
        root = args.base / f"stage2_v3_zcc_zss_1200_bdt1091peak/v3_{name}_1200_bdt1091peak"
        summary_path = root / "summary.json"
        summary = json.loads(summary_path.read_text())
        if (summary["sample"] != name or not summary["complete_catalog"] or
                summary["input_chunks"] != 1200 or
                summary["run_identity"]["model_sha256"] != projection["model_sha256"] or
                summary["run_identity"]["score_cut"] != score):
            raise ValueError(f"Wrong {name} archive")
        shards = sorted(root.glob("chunks/chunk_*/offline_selected.parquet"))
        if len(shards) != 1200:
            raise ValueError(f"Incomplete {name} archive")
        paths.extend((name, path) for path in shards)
        summaries[name] = {"path": str(summary_path), "sha256": sha(summary_path),
                           "data": summary}
    edges = {key: np.linspace(spec[0], spec[1], 41) for key, spec in FEATURES.items()}
    results = {name: {"rows": 0, "counts": np.zeros(3, dtype=np.int64),
                      "peak": np.zeros(3, dtype=np.int64),
                      "hist": {key: np.zeros((3, 43), dtype=np.int64) for key in FEATURES},
                      "peak_hist": {key: np.zeros((3, 43), dtype=np.int64) for key in FEATURES},
                      "mass": np.zeros((3, 72), dtype=np.int64),
                      "angle": np.zeros((3, 20), dtype=np.int64),
                      "score_hist": np.zeros(len(SCORE_EDGES)-1, dtype=np.int64)} for name in NAMES}
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        for item in pool.map(lambda pair: process(pair, score, cfg["armenteros_reject_box"], edges), paths):
            acc = results[item["name"]]
            acc["rows"] += item["rows"]
            acc["counts"] += item["counts"]
            acc["peak"] += item["peak"]
            for key in FEATURES:
                acc["hist"][key] += item["hist"][key]
                acc["peak_hist"][key] += item["peak_hist"][key]
            acc["mass"] += item["mass"]
            acc["angle"] += item["angle"]
            acc["score_hist"] += item["score_hist"]
    for name in ("zcc", "zss"):
        ref = summaries[name]["data"]["stage_counts"]
        if (results[name]["rows"] != ref["offline_selected"]["candidate_rows"] or
                results[name]["counts"][0] != ref["offline_selected"]["nonmatched_rows"] or
                results[name]["counts"][1] != ref["bdt_selected"]["nonmatched_rows"] or
                results[name]["peak"][1] != ref["bdt_selected"]["peak_nonmatched_rows"]):
            raise ValueError(f"{name} aggregate disagrees with frozen summary")
    if (results["signal"]["rows"] != preparation["stage_counts"]["signal"]["selected"]["candidates"] or
            results["signal"]["counts"][0] != preparation["stage_counts"]["signal"]["selected"]["direct_candidates"] or
            results["zbb"]["rows"] != preparation["stage_counts"]["zbb"]["selected"]["candidates"] or
            results["zbb"]["counts"][0] != preparation["stage_counts"]["zbb"]["selected"]["background_candidates"]):
        raise ValueError("Signal/Zbb aggregate disagrees with frozen preparation")
    br = cfg["branching_fractions"]
    weights = {"signal": (cfg["N_Z"] * br["Zbb"] * 2 * cfg["f_Lambdab_per_b"] *
                          br["Lb_to_Lambda_gamma"] * br["Lambda_to_p_pi"] /
                          cfg["signal_generated_direct_decays"]),
               "zbb": cfg["N_Z"] * br["Zbb"] / catalog["total_processed_events_in_valid_chunks"]}
    for name in ("zcc", "zss"):
        weights[name] = cfg["N_Z"] * br["Z" + name[1:]] / \
                        summaries[name]["data"]["processed_input_events"]
    ranking = []
    for key in FEATURES:
        sig = np.array(results["signal"]["hist"][key][0], dtype=float)
        sig /= sig.sum()
        row = {"variable": key, "in_current_bdt": False}
        for name in ("zbb", "zcc", "zss"):
            bkg = np.array(results[name]["hist"][key][0], dtype=float)
            bkg /= bkg.sum()
            row[f"tv_signal_vs_{name}"] = float(.5 * np.abs(sig-bkg).sum())
            row[f"missing_{name}"] = float(bkg[-1])
        row["missing_signal"] = float(sig[-1])
        ranking.append(row)
    peak_ranking = []
    for key in FEATURES:
        sig = np.array(results["signal"]["peak_hist"][key][0], dtype=float)
        sig /= sig.sum()
        row = {"variable": key}
        for name in ("zbb", "zcc", "zss"):
            bkg = np.array(results[name]["peak_hist"][key][0], dtype=float)
            bkg /= bkg.sum()
            row[f"tv_signal_vs_{name}"] = float(.5 * np.abs(sig-bkg).sum())
        peak_ranking.append(row)
    training = json.loads(Path(projection["training_summary"]).read_text())
    used = set(training["features"])
    for row in ranking:
        source = row["variable"].replace("abs_lambda_d0_sig", "lambda_d0_sig").replace("abs_arm_alpha", "arm_alpha")
        row["in_current_bdt"] = source in used
    for row in peak_ranking:
        source = row["variable"].replace("abs_lambda_d0_sig", "lambda_d0_sig").replace("abs_arm_alpha", "arm_alpha")
        row["in_current_bdt"] = source in used
    args.output_dir.mkdir(parents=True, exist_ok=True)
    for stage in (0, 2):
        for page in PAGES:
            make_plot(results, stage, page, args.output_dir / f"{STAGES[stage]}_{page}.png")
        make_yields(results, weights, stage, args.output_dir / f"{STAGES[stage]}_mass_angle_linear.png")
    for page in PAGES:
        make_plot(results, 0, page, args.output_dir / f"pre_bdt_peak_{page}.png", peak=True)
    make_score(results, weights, score, args.output_dir / "pre_bdt_score_tail.png")
    output = {"question": "Should Zbb-only BDT training include Zcc and Zss?",
              "script_sha256": sha(Path(__file__)),
              "score": score, "configuration": str(args.config), "configuration_sha256": sha(args.config),
              "preparation_summary": str(preparation_path),
              "preparation_summary_sha256": sha(preparation_path),
              "fccanalyses_revision": preparation["fccanalyses_revision"],
              "catalog": str(args.catalog), "catalog_sha256": sha(args.catalog),
              "projection": str(args.projection), "projection_sha256": sha(args.projection),
              "training_summary": projection["training_summary"],
              "training_summary_sha256": sha(projection["training_summary"]),
              "source_summaries": {name: {k: v for k, v in entry.items() if k != "data"}
                                   for name, entry in summaries.items()},
              "scored_dir": str(scored), "input_shards": {"zbb": len(zbb_paths), "zcc": 1200, "zss": 1200},
              "processed_events": {"zbb": catalog["total_processed_events_in_valid_chunks"],
                                   **{name: summaries[name]["data"]["processed_input_events"]
                                      for name in ("zcc", "zss")}},
              "weights": weights, "stages": STAGES,
              "selection": "pre-BDT offline selected; frozen score; score plus Armenteros, pi0, eta proposals",
              "hist_bins": {key: edges[key].tolist() for key in FEATURES},
              "score_bins": SCORE_EDGES.tolist(),
              "hist_layout": "underflow, 40 plotted bins, overflow, missing/nonfinite; each class denominator includes all",
              "counts": {name: {"selected_rows_all_truth": int(item["rows"]),
                                "candidate_rows": item["counts"].tolist(),
                                "peak_candidate_rows": item["peak"].tolist(),
                                "expected_peak_candidates": (item["peak"] * weights[name]).tolist()}
                         for name, item in results.items()},
              "total_variation": ranking,
              "peak_total_variation": peak_ranking,
              "histograms": {name: {"features": {key: item["hist"][key].tolist() for key in FEATURES},
                                    "peak_features": {key: item["peak_hist"][key].tolist() for key in FEATURES},
                                    "mass": item["mass"].tolist(), "angle": item["angle"].tolist(),
                                    "score": item["score_hist"].tolist()}
                             for name, item in results.items()},
              "limitations": "Full-sample descriptive comparison; includes Zbb training chunks; TV is binned marginal separation and not multivariate gain."}
    (args.output_dir / "flavour_feature_comparison.json").write_text(json.dumps(output, indent=2) + "\n")
    print(json.dumps({"counts": output["counts"],
                      "top_zss_tv": sorted(ranking, key=lambda x: x["tv_signal_vs_zss"], reverse=True)[:10]}, indent=2))


if __name__ == "__main__":
    main()

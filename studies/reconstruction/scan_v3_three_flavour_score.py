#!/usr/bin/env python3
"""Exact peak-score scan with Zbb, Zcc and Zss after reconstructed veto scenarios."""

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
from scipy.stats import chi2

import v3_plot_style  # noqa: F401


BASE = Path("/eos/lhcb/lbdt3/user/rquaglia/fcc_ee/lblgamma/outputs")
STAGES = ("arm_only", "arm_eta", "arm_pi0", "arm_pi0_eta")
LABELS = {"arm_only": "Armenteros only", "arm_eta": "Armenteros + η veto",
          "arm_pi0": "Armenteros + π⁰ veto", "arm_pi0_eta": "Armenteros + π⁰ + η veto"}
COLORS = {"arm_only": "#2670a8", "arm_eta": "#ba4148",
          "arm_pi0": "#d89428", "arm_pi0_eta": "#198466"}
SAMPLES = ("signal", "zbb", "zcc", "zss")
PARTITIONS = ("all", "validation", "test")
COLUMNS = ("event_entry", "truth_matched", "bdt_score", "lb_mass",
           "arm_alpha", "arm_qt", "pass_pi0", "pass_eta")


def sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def split_signal(events):
    bucket = (events.astype(np.uint64) * np.uint64(11400714819323198485)) % np.uint64(10)
    return np.where(bucket < 7, "train", np.where(bucket == 7, "validation", "test"))


def read_one(item, box, window):
    name, chunk_id, path = item
    table = pq.read_table(path, columns=list(COLUMNS), use_threads=False)
    truth = table["truth_matched"].to_numpy(zero_copy_only=False)
    mass = table["lb_mass"].to_numpy(zero_copy_only=False)
    base = ((truth == 1) if name == "signal" else (truth != 1)) & \
           (mass >= window[0]) & (mass <= window[1])
    score = table["bdt_score"].to_numpy(zero_copy_only=False)
    if not np.isfinite(score[base]).all():
        raise ValueError(f"Nonfinite score: {path}")
    alpha = np.abs(table["arm_alpha"].to_numpy(zero_copy_only=False))
    qt = table["arm_qt"].to_numpy(zero_copy_only=False)
    reject = ((alpha >= box["abs_alpha_min"]) & (alpha <= box["abs_alpha_max"]) &
              (qt >= box["qt_min_gev"]) & (qt <= box["qt_max_gev"]))
    arm = ~reject
    pi0 = table["pass_pi0"].to_numpy(zero_copy_only=False).astype(bool)
    eta = table["pass_eta"].to_numpy(zero_copy_only=False).astype(bool)
    cuts = {"arm_only": arm, "arm_eta": arm & eta,
            "arm_pi0": arm & pi0, "arm_pi0_eta": arm & pi0 & eta}
    if name == "signal":
        partitions = split_signal(table["event_entry"].to_numpy(zero_copy_only=False))
    else:
        partitions = np.full(table.num_rows,
                             "train" if chunk_id % 10 < 7 else
                             "validation" if chunk_id % 10 == 7 else "test", dtype=object)
    return name, table.num_rows, {part: {stage: score[base & mask & ((partitions == part) if part != "all" else True)]
                                         for stage, mask in cuts.items()}
                                  for part in PARTITIONS}


def scan(scores, weights, thresholds):
    counts = {name: len(arr) - np.searchsorted(arr, thresholds, side="left")
              for name, arr in scores.items()}
    s = counts["signal"] * weights["signal"]
    b_components = {name: counts[name] * weights[name] for name in ("zbb", "zcc", "zss")}
    b = sum(b_components.values())
    with np.errstate(divide="ignore", invalid="ignore"):
        fom = np.divide(s, np.sqrt(s+b), out=np.zeros_like(s, dtype=float), where=(s+b) > 0)
        purity = np.divide(s, s+b, out=np.zeros_like(s, dtype=float), where=(s+b) > 0)
        significance = np.divide(s, np.sqrt(b), out=np.full_like(s, np.nan, dtype=float), where=b > 0)
    return {"thresholds": thresholds, "counts": counts, "signal": s,
            "background_components": b_components, "background": b,
            "fom": fom, "significance": significance, "purity": purity}


def point(result, idx, weights):
    counts = {name: int(result["counts"][name][idx]) for name in SAMPLES}
    b_intervals = {}
    for name in ("zbb", "zcc", "zss"):
        n = counts[name]
        low = .5 * chi2.ppf(.025, 2*n) if n else 0.
        high = .5 * chi2.ppf(.975, 2*(n+1))
        b_intervals[name] = [float(low * weights[name]), float(high * weights[name])]
    upper_b = sum(pair[1] for pair in b_intervals.values())
    return {"score": float(result["thresholds"][idx]),
            "peak_candidate_rows": counts,
            "expected_signal": float(result["signal"][idx]),
            "expected_backgrounds": {name: float(result["background_components"][name][idx])
                                     for name in ("zbb", "zcc", "zss")},
            "expected_background": float(result["background"][idx]),
            "central_purity": float(result["purity"][idx]),
            "S_over_sqrt_S_plus_B": float(result["fom"][idx]),
            "S_over_sqrt_B": float(result["significance"][idx]) if
                np.isfinite(result["significance"][idx]) else None,
            "background_candidate_poisson_95pct_intervals": b_intervals,
            "S_over_sqrt_S_plus_B_with_background_upper":
                float(result["signal"][idx] / np.sqrt(result["signal"][idx] + upper_b))
                if result["signal"][idx] + upper_b else 0.,
            "S_over_sqrt_B_with_background_upper":
                float(result["signal"][idx] / np.sqrt(upper_b)) if upper_b else None}


def plot_fom(curves, choices, fixed, objective, output):
    metric = "significance" if objective == "s_over_sqrt_b" else "fom"
    key = "S_over_sqrt_B" if objective == "s_over_sqrt_b" else "S_over_sqrt_S_plus_B"
    fig, axes = plt.subplots(1, 3, figsize=(17.2, 4.8))
    for part, ax in zip(PARTITIONS, axes):
        for stage in STAGES:
            row = curves[part][stage]
            ax.plot(row["thresholds"], row[metric], color=COLORS[stage],
                    label=LABELS[stage], linewidth=1.5)
            chosen = (choices[stage]["test_at_validation_choice"] if part == "test" else
                      choices[stage]["validation_maximum"] if part == "validation" else
                      choices[stage]["all_maximum"])
            ax.scatter(chosen["score"], chosen[key],
                       color=COLORS[stage], s=26, zorder=3)
        ax.axvline(fixed, color="#555555", linestyle="--", linewidth=1.1)
        ax.set(xlabel="Minimum frozen BDT score",
               ylabel=r"Peak $S/\sqrt{B}$" if objective == "s_over_sqrt_b" else r"Peak $S/\sqrt{S+B}$",
               title=("All archived candidates (descriptive)" if part == "all" else
                      "Validation partitions (choice sample)" if part == "validation" else
                      "Test at validation-selected score"), xlim=(.8, 1), ylim=(0, None))
        ax.grid(alpha=.2)
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="lower center", bbox_to_anchor=(.5, -.015),
               ncol=4, frameon=False)
    fig.suptitle("Signal peak 5.4–5.9 GeV • B = Zbb + Zcc + Zss", fontsize=13)
    fig.tight_layout(rect=(0, .10, 1, .92))
    fig.savefig(output, dpi=180, bbox_inches="tight")
    plt.close(fig)


def plot_yields(curves, fixed, output):
    fig, axes = plt.subplots(2, 2, figsize=(13.4, 8.1))
    for ax, stage in zip(axes.flat, STAGES):
        row = curves["all"][stage]
        ax.plot(row["thresholds"], row["signal"], color="#2670a8", label="Signal")
        for name, color in (("zbb", "#252525"), ("zcc", "#6b4fa1"), ("zss", "#198466")):
            ax.plot(row["thresholds"], row["background_components"][name],
                    color=color, label=name.upper())
        ax.axvline(fixed, color="#ba4148", linestyle="--", linewidth=1.0)
        ax.set(xlim=(.8, 1), ylim=(0, None), title=LABELS[stage],
               xlabel="Minimum frozen BDT score", ylabel="Expected peak candidate rows")
        ax.grid(alpha=.2)
    handles, labels = axes.flat[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="lower center", bbox_to_anchor=(.5, -.01),
               ncol=4, frameon=False)
    fig.tight_layout(rect=(0, .055, 1, .97))
    fig.savefig(output, dpi=180, bbox_inches="tight")
    plt.close(fig)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--base", type=Path, default=BASE)
    ap.add_argument("--config", type=Path, default=Path("config/v3_post_bdt_veto_sequence.json"))
    ap.add_argument("--zbb-catalog", type=Path, default=Path("docs/data/stage2_v3_bdt_1091_peak/20261003_1091chunks.json"))
    ap.add_argument("--zcc-catalog", type=Path, default=Path("docs/data/stage2_v3_zcc_zss_1200/zcc_1200_v3.json"))
    ap.add_argument("--zss-catalog", type=Path, default=Path("docs/data/stage2_v3_zcc_zss_1200/zss_1200_v3.json"))
    ap.add_argument("--projection", type=Path, default=BASE / "stage2_v3_incremental/projections/20261004_1091chunks_peak_5p4_5p9/projection.json")
    ap.add_argument("--workers", type=int, default=16)
    ap.add_argument("--objective", choices=("s_over_sqrt_s_plus_b", "s_over_sqrt_b"),
                    default="s_over_sqrt_s_plus_b")
    ap.add_argument("--output-dir", type=Path, required=True)
    args = ap.parse_args()
    if args.workers < 1:
        ap.error("workers must be positive")
    cfg = json.loads(args.config.read_text())
    projection = json.loads(args.projection.read_text())
    fixed = float(projection["validation_choice"]["score"])
    catalogs = {name: json.loads(getattr(args, f"{name}_catalog").read_text())
                for name in ("zbb", "zcc", "zss")}
    input_meta = {}
    paths = []
    scored = args.base / "stage2_v3_incremental/models/20261004_1091chunks/scored_selected"
    paths.append(("signal", -1, scored / "signal_-1_selected.parquet"))
    for name in ("zbb", "zcc", "zss"):
        catalog = catalogs[name]
        ids = {int(row["chunk_id"]) for row in catalog["chunks"]}
        if len(ids) != (1091 if name == "zbb" else 1200):
            raise ValueError(f"Wrong {name} catalog")
        if name == "zbb":
            shards = [(int(p.stem.split("_")[1]), p) for p in scored.glob("zbb_*_selected.parquet")]
        else:
            root = args.base / f"stage2_v3_zcc_zss_1200_bdt1091peak/v3_{name}_1200_bdt1091peak"
            summary = json.loads((root / "summary.json").read_text())
            if (not summary["complete_catalog"] or summary["input_chunks"] != 1200 or
                    summary["run_identity"]["model_sha256"] != projection["model_sha256"] or
                    summary["run_identity"]["score_cut"] != fixed):
                raise ValueError(f"Wrong {name} archive/model")
            shards = [(int(p.parent.name.split("_")[1]), p)
                      for p in root.glob("chunks/chunk_*/offline_selected.parquet")]
            input_meta[name + "_summary"] = {"path": str(root / "summary.json"),
                                               "sha256": sha(root / "summary.json")}
        if {id for id, _ in shards} != ids:
            raise ValueError(f"{name} archive shards differ from catalog")
        paths.extend((name, id, path) for id, path in sorted(shards))
    split_events = {"signal": {"all": cfg["signal_generated_direct_decays"],
                               **{part: projection["signal_generated_events_by_split"][part]
                                  for part in ("validation", "test")}}}
    for name in ("zbb", "zcc", "zss"):
        chunks = catalogs[name]["chunks"]
        split_events[name] = {"all": int(sum(row["events_processed"] for row in chunks))}
        for part, bucket in (("validation", 7), ("test", None)):
            split_events[name][part] = int(sum(row["events_processed"] for row in chunks
                                                if ((row["chunk_id"] % 10 == bucket) if bucket is not None
                                                    else row["chunk_id"] % 10 >= 8)))
    if split_events["zbb"]["validation"] != projection["zbb_processed_events_by_split"]["validation"]:
        raise ValueError("Zbb validation denominator changed")
    if split_events["zbb"]["test"] != projection["zbb_processed_events_by_split"]["test"]:
        raise ValueError("Zbb test denominator changed")
    weights = {}
    br = cfg["branching_fractions"]
    signal_factor = cfg["N_Z"] * br["Zbb"] * 2 * cfg["f_Lambdab_per_b"] * \
                    br["Lb_to_Lambda_gamma"] * br["Lambda_to_p_pi"]
    for part in PARTITIONS:
        weights[part] = {"signal": signal_factor / split_events["signal"][part]}
        for name in ("zbb", "zcc", "zss"):
            weights[part][name] = cfg["N_Z"] * br["Z" + name[1:]] / split_events[name][part]
    arrays = {part: {stage: {name: [] for name in SAMPLES} for stage in STAGES}
              for part in PARTITIONS}
    row_counts = {name: 0 for name in SAMPLES}
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        for name, nrows, data in pool.map(lambda item: read_one(item, cfg["armenteros_reject_box"],
                                                                 cfg["mass_window_gev"]), paths):
            row_counts[name] += nrows
            for part in PARTITIONS:
                for stage in STAGES:
                    arrays[part][stage][name].append(data[part][stage])
    prepared = json.loads((args.base / "stage2_v3_incremental/prepared/summary.json").read_text())
    if (row_counts["signal"] != prepared["stage_counts"]["signal"]["selected"]["candidates"] or
            row_counts["zbb"] != prepared["stage_counts"]["zbb"]["selected"]["candidates"]):
        raise ValueError("Signal/Zbb scored rows differ from preparation")
    for name in ("zcc", "zss"):
        path = Path(input_meta[name + "_summary"]["path"])
        summary = json.loads(path.read_text())
        if row_counts[name] != summary["stage_counts"]["offline_selected"]["candidate_rows"]:
            raise ValueError(f"{name} scored rows differ from archive")
    sorted_scores = {part: {stage: {name: np.sort(np.concatenate(arrays[part][stage][name]))
                                    for name in SAMPLES} for stage in STAGES}
                     for part in PARTITIONS}
    choices = {}
    plot_grid = np.unique(np.r_[np.linspace(0, .8, 81), np.linspace(.8, .9, 101),
                                np.linspace(.9, .99, 181), np.linspace(.99, .999, 181),
                                np.linspace(.999, 1, 201), fixed])
    curves = {part: {} for part in PARTITIONS}
    for stage in STAGES:
        choices[stage] = {}
        for part in PARTITIONS:
            scores = sorted_scores[part][stage]
            exact_grid = np.unique(np.concatenate(list(scores.values())))
            exact = scan(scores, weights[part], exact_grid)
            metric = exact["significance"] if args.objective == "s_over_sqrt_b" else exact["fom"]
            if not np.isfinite(metric).any():
                raise ValueError(f"No finite {args.objective} point for {stage}/{part}")
            idx = int(np.nanargmax(metric))
            choices[stage][part + "_maximum"] = point(exact, idx, weights[part])
            near = scan(scores, weights[part], np.array([fixed]))
            choices[stage][part + "_fixed"] = point(near, 0, weights[part])
            curves[part][stage] = scan(scores, weights[part], plot_grid)
        val_score = choices[stage]["validation_maximum"]["score"]
        for part in ("all", "test"):
            checked = scan(sorted_scores[part][stage], weights[part], np.array([val_score]))
            choices[stage][part + "_at_validation_choice"] = point(checked, 0, weights[part])
    args.output_dir.mkdir(parents=True, exist_ok=True)
    plot_fom(curves, choices, fixed, args.objective,
             args.output_dir / "three_flavour_fom_score_scan.png")
    plot_yields(curves, fixed, args.output_dir / "three_flavour_peak_yields_score_scan.png")
    output = {"question": f"Maximize peak {args.objective}, B=Zbb+Zcc+Zss, with reconstructed veto choices",
              "script_sha256": sha(Path(__file__)), "config": str(args.config), "config_sha256": sha(args.config),
              "projection": str(args.projection), "projection_sha256": sha(args.projection),
              "model_sha256": projection["model_sha256"], "fixed_previous_score": fixed,
              "catalogs": {name: {"path": str(getattr(args, f"{name}_catalog")),
                                   "sha256": sha(getattr(args, f"{name}_catalog"))}
                           for name in ("zbb", "zcc", "zss")},
              "input_meta": input_meta, "scored_dir": str(scored),
              "peak_window_gev": cfg["mass_window_gev"], "scenario_labels": LABELS,
              "processed_or_generated_denominators": split_events, "weights": weights,
              "selected_rows_all_truth": row_counts,
              "optimization": "exact unique observed score thresholds; central " + args.objective +
                              "; no minimum raw-background condition; B=0 has undefined S/sqrt(B) and is excluded",
              "objective": args.objective,
              "validation_split": "signal event hash as frozen training; whole chunk ID modulo 10 for each inclusive flavour; Zcc/Zss chunks were not used in model training",
              "candidate_count_95pct_intervals": "Garwood intervals per inclusive component; summed upper endpoints for conservative diagnostic",
              "choices": choices,
              "plot_grid": plot_grid.tolist(),
              "plot_curves": {part: {stage: {"fom": curves[part][stage]["fom"].tolist(),
                                               "significance": [float(v) if np.isfinite(v) else None
                                                                for v in curves[part][stage]["significance"]],
                                               "signal": curves[part][stage]["signal"].tolist(),
                                               "backgrounds": {name: curves[part][stage]["background_components"][name].tolist()
                                                               for name in ("zbb", "zcc", "zss")}}
                                    for stage in STAGES} for part in PARTITIONS},
              "limitations": "Existing Zbb model; all-sample maxima include its training chunks. Validation choice uses finite-sample score tails and post-hoc veto scenarios. Test check is not a fresh veto-blind study. Forced eta/pi0 and wrong signal combinations excluded from B."}
    (args.output_dir / "three_flavour_score_scan.json").write_text(
        json.dumps(output, indent=2, allow_nan=False) + "\n")
    for stage in STAGES:
        print(stage, "validation", choices[stage]["validation_maximum"],
              "test", choices[stage]["test_at_validation_choice"])


if __name__ == "__main__":
    main()

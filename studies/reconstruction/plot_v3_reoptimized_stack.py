#!/usr/bin/env python3
"""Physically scaled inclusive stack at the validation-selected Arm-only score."""

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
COLS = ("lb_mass", "cos_theta_p", "truth_matched", "bdt_score", "arm_alpha", "arm_qt")
MASS = np.linspace(4.7, 6.5, 73)
ANGLE = np.linspace(-1, 1, 21)
COLORS = {"signal": "#2670a8", "signal_wrong": "#8b8b8b", "zbb": "#333333",
          "zcc": "#6b4fa1", "zss": "#198466", "eta": "#ba4148", "pi0": "#d89428"}
LABELS = {"signal": "Direct Λb→Λγ", "signal_wrong": "Signal wrong combinations",
          "zbb": "Nonmatched Zbb", "zcc": "Nonmatched Zcc", "zss": "Nonmatched Zss",
          "eta": "Forced Λη (separate)", "pi0": "Forced Λπ⁰ (separate)"}
STACK = ("zss", "zcc", "zbb", "signal_wrong", "signal")


def sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def read_one(item, score, box):
    name, path = item
    table = pq.read_table(path, columns=list(COLS), use_threads=False)
    s = table["bdt_score"].to_numpy(zero_copy_only=False)
    alpha = np.abs(table["arm_alpha"].to_numpy(zero_copy_only=False))
    qt = table["arm_qt"].to_numpy(zero_copy_only=False)
    arm = ~((alpha >= box["abs_alpha_min"]) & (alpha <= box["abs_alpha_max"]) &
            (qt >= box["qt_min_gev"]) & (qt <= box["qt_max_gev"]))
    mass = table["lb_mass"].to_numpy(zero_copy_only=False)
    angle = table["cos_theta_p"].to_numpy(zero_copy_only=False)
    truth = table["truth_matched"].to_numpy(zero_copy_only=False)
    keep = (s >= score) & arm
    classes = {name: keep} if name in ("eta", "pi0") else \
              {"signal": keep & (truth == 1), "signal_wrong": keep & (truth != 1)} if name == "signal" else \
              {name: keep & (truth != 1)}
    return {key: {"rows": int(mask.sum()),
                  "peak_rows": int((mask & (mass >= 5.4) & (mass <= 5.9)).sum()),
                  "mass": np.histogram(mass[mask], bins=MASS)[0],
                  "angle_peak": np.histogram(angle[mask & (mass >= 5.4) & (mass <= 5.9)],
                                             bins=ANGLE)[0]}
            for key, mask in classes.items()}


def plot(results, weights, score, output):
    fig, axes = plt.subplots(2, 2, figsize=(13.8, 8.4))
    for col, (axis, edges, unit) in enumerate((('mass', MASS, '25 MeV'),
                                               ('angle_peak', ANGLE, '0.1'))):
        ax = axes[0, col]
        bottom = np.zeros(len(edges)-1)
        for name in STACK:
            value = results[name][axis] * weights[name]
            ax.stairs(bottom + value, edges, baseline=bottom, fill=True,
                      color=COLORS[name], alpha=.9, label=LABELS[name])
            bottom += value
        ax.set(ylabel=f"Expected candidates / {unit}", ylim=(0, None))
        if col == 0:
            ax.axvspan(5.4, 5.9, color="gray", alpha=.12)
            ax.set_title("Inclusive fit-candidate stack: mass")
        else:
            ax.set_title("Inclusive stack: cos θp within peak")
        ax.grid(alpha=.2)
        small = axes[1, col]
        for name in ("eta", "pi0", "signal_wrong"):
            small.stairs(results[name][axis] * weights[name], edges,
                         color=COLORS[name], linewidth=1.6, label=LABELS[name])
        small.set(ylabel=f"Expected candidates / {unit}", ylim=(0, None),
                  title="Forced-mode sensitivity (not stacked with inclusive Zbb)")
        small.grid(alpha=.2)
    axes[1, 0].set_xlabel("Reconstructed m(Λγ) [GeV]")
    axes[1, 1].set_xlabel("Reconstructed cos θp")
    handles0, labels0 = axes[0, 0].get_legend_handles_labels()
    handles1, labels1 = axes[1, 0].get_legend_handles_labels()
    fig.legend(handles0 + handles1[:2], labels0 + labels1[:2], loc="lower center",
               bbox_to_anchor=(.5, -.01), ncol=4, frameon=False, fontsize=8)
    fig.suptitle(f"v3 score ≥{score:.6f} + Armenteros; central expected yields at 6×10¹² Z",
                 fontsize=13)
    fig.tight_layout(rect=(0, .055, 1, .95))
    fig.savefig(output, dpi=180, bbox_inches="tight")
    plt.close(fig)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--base", type=Path, default=BASE)
    ap.add_argument("--scan", type=Path, required=True)
    ap.add_argument("--eta-summary", type=Path, default=Path("docs/data/stage2_v3_pseudoscalar_100k_bdt1091peak/eta_physics_summary.json"))
    ap.add_argument("--pi0-summary", type=Path, default=Path("docs/data/stage2_v3_pseudoscalar_100k_bdt1091peak/pi0_physics_summary.json"))
    ap.add_argument("--config", type=Path, default=Path("config/v3_post_bdt_veto_sequence.json"))
    ap.add_argument("--workers", type=int, default=16)
    ap.add_argument("--output-dir", type=Path, required=True)
    args = ap.parse_args()
    scan = json.loads(args.scan.read_text())
    cfg = json.loads(args.config.read_text())
    if scan["config_sha256"] != sha(args.config):
        raise ValueError("Scan and configuration differ")
    score = scan["choices"]["arm_only"]["validation_maximum"]["score"]
    scored = args.base / "stage2_v3_incremental/models/20261004_1091chunks/scored_selected"
    paths = [("signal", scored / "signal_-1_selected.parquet")]
    zbb = sorted(scored.glob("zbb_*_selected.parquet"))
    if len(zbb) != 1091:
        raise ValueError("Wrong Zbb scored shard count")
    paths.extend(("zbb", path) for path in zbb)
    for name in ("zcc", "zss"):
        root = args.base / f"stage2_v3_zcc_zss_1200_bdt1091peak/v3_{name}_1200_bdt1091peak"
        shards = sorted(root.glob("chunks/chunk_*/offline_selected.parquet"))
        if len(shards) != 1200:
            raise ValueError(f"Incomplete {name} archive")
        paths.extend((name, path) for path in shards)
    pseudoscalar = args.base / "stage2_v3_pseudoscalar_physics_100k_bdt1091peak"
    paths.extend((name, path) for name, path in (
        ("eta", pseudoscalar / "v3_eta_physics_100k_stage2_bdt1091peak/bdt_selected/lb_lambdaeta_physics_v3_-5.parquet"),
        ("pi0", pseudoscalar / "v3_pi0_physics_100k_stage2_bdt1091peak/bdt_selected/lb_lambdapi0_physics_v3_-4.parquet")))
    results = {name: {"rows": 0, "peak_rows": 0, "mass": np.zeros(72, dtype=np.int64),
                      "angle_peak": np.zeros(20, dtype=np.int64)} for name in COLORS}
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        for found in pool.map(lambda item: read_one(item, score, cfg["armenteros_reject_box"]), paths):
            for name, row in found.items():
                results[name]["rows"] += row["rows"]
                results[name]["peak_rows"] += row["peak_rows"]
                results[name]["mass"] += row["mass"]
                results[name]["angle_peak"] += row["angle_peak"]
    expected = scan["choices"]["arm_only"]["all_at_validation_choice"]["peak_candidate_rows"]
    if any(results[name]["peak_rows"] != expected[name] for name in ("signal", "zbb", "zcc", "zss")):
        raise ValueError("Stack peak counts differ from frozen score scan")
    weights = dict(scan["weights"]["all"])
    weights["signal_wrong"] = weights["signal"]
    input_meta = {}
    for name in ("eta", "pi0"):
        path = getattr(args, name + "_summary")
        summary = json.loads(path.read_text())
        if summary["bdt_score"] != scan["fixed_previous_score"] or \
           summary["model_sha256"] != scan["model_sha256"]:
            raise ValueError(f"Wrong {name} forced-mode model")
        weights[name] = summary["projected_candidates"]["factor_before_selection"] / \
                        summary["generated_direct_decays"]
        input_meta[name] = {"summary": str(path), "sha256": sha(path),
                            "generated_direct_decays": summary["generated_direct_decays"]}
    args.output_dir.mkdir(parents=True, exist_ok=True)
    plot(results, weights, score, args.output_dir / "reoptimized_arm_only_stack.png")
    output = {"script_sha256": sha(Path(__file__)), "scan": str(args.scan),
              "scan_sha256": sha(args.scan), "score": score,
              "selection": "Frozen BDT score plus Armenteros box; no pi0 or eta photon veto",
              "config_sha256": sha(args.config), "input_meta": input_meta,
              "weights": weights, "mass_edges": MASS.tolist(), "angle_edges": ANGLE.tolist(),
              "angle_window_gev": [5.4, 5.9],
              "stack": list(STACK),
              "forced_modes_are_separate": "Eta and pi0 may overlap inclusive Zbb; they are not added to inclusive stack",
              "components": {name: {"candidate_rows": row["rows"], "peak_candidate_rows": row["peak_rows"],
                                    "expected_peak_candidates": row["peak_rows"] * weights[name],
                                    "mass_hist": row["mass"].tolist(),
                                    "peak_angle_hist": row["angle_peak"].tolist()}
                             for name, row in results.items()}}
    (args.output_dir / "reoptimized_arm_only_stack.json").write_text(json.dumps(output, indent=2) + "\n")
    print(json.dumps({name: {"raw_peak": row["peak_rows"],
                             "expected_peak": round(row["peak_rows"]*weights[name])}
                      for name, row in results.items()}, indent=2))


if __name__ == "__main__":
    main()

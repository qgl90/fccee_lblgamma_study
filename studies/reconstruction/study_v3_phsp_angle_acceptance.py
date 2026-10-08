#!/usr/bin/env python3
"""Full 100k PHSP angular efficiency and resolution through v3 Stage 1/2/BDT.

The generator is the denominator, including decays with no candidate. Match
selected direct candidates to generated decays by truth angle and charge,
because the multithreaded Stage 1 snapshot does not preserve raw row order.
"""
import argparse
import hashlib
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import beta

from study_cos_theta_p import generated_angles
import v3_plot_style  # noqa: F401


COLS = ["source_id", "event_entry", "candidate_slot", "lb_mc_index",
        "lb_sign", "truth_matched", "truth_cos_theta_p", "cos_theta_p",
        "lb_mass", "bdt_score"]
BINS = np.linspace(-1, 1, 11)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def bounds(k, n):
    if not n:
        return [None, None]
    return [float(beta.ppf(.16, k, n-k+1)) if k else 0.,
            float(beta.ppf(.84, k+1, n-k)) if k < n else 1.]


def match_generated(frame, generated, tolerance=2e-4):
    frame = frame.loc[frame.truth_matched == 1].copy()
    frame = frame.loc[np.isfinite(frame.truth_cos_theta_p) &
                      frame.truth_cos_theta_p.between(-1, 1)].copy()
    if not len(frame):
        raise ValueError("No direct truth-matched candidates")
    lookup = {}
    for sign in (-1, 1):
        ids = np.where(generated.sign.to_numpy() == sign)[0]
        order = np.argsort(generated.iloc[ids].truth_angle.to_numpy())
        lookup[sign] = (generated.iloc[ids[order]].truth_angle.to_numpy(), ids[order])
    matched = np.empty(len(frame), dtype=np.int64)
    errors = np.empty(len(frame), dtype=float)
    for sign in (-1, 1):
        mask = frame.lb_sign.to_numpy() == sign
        values = frame.loc[mask, "truth_cos_theta_p"].to_numpy(dtype=float)
        angles, ids = lookup[sign]
        pos = np.searchsorted(angles, values)
        lo, hi = np.maximum(pos-1, 0), np.minimum(pos, len(angles)-1)
        choose_hi = np.abs(angles[hi]-values) < np.abs(angles[lo]-values)
        pick = np.where(choose_hi, hi, lo)
        matched[mask] = ids[pick]
        errors[mask] = np.abs(angles[pick]-values)
    if np.any(errors > tolerance):
        raise ValueError(f"{np.sum(errors > tolerance)} direct candidates have no generated angle/charge match; max {errors.max():.6g}")
    frame["generated_decay_id"] = matched
    frame["generated_truth_angle"] = generated.iloc[matched].truth_angle.to_numpy()
    return frame, float(errors.max())


def stage_result(frame, generated):
    unique = frame.drop_duplicates("generated_decay_id")
    g = generated.truth_angle.to_numpy()
    s = unique.generated_truth_angle.to_numpy()
    den = np.histogram(g, BINS)[0]
    num = np.histogram(s, BINS)[0]
    if np.any(num > den):
        raise ValueError("Selected decays exceed generated decays")
    by_charge = {}
    for sign in (-1, 1):
        gsign = generated.loc[generated.sign == sign]
        ssign = unique.loc[unique.lb_sign == sign]
        gd = np.histogram(gsign.truth_angle, BINS)[0]
        sn = np.histogram(ssign.generated_truth_angle, BINS)[0]
        by_charge[str(sign)] = {"generated_bin_counts": gd.tolist(),
                                "selected_bin_counts": sn.tolist(),
                                "efficiency": (sn/gd).tolist()}
    return {"candidate_rows": int(len(frame)), "unique_selected_decays": int(len(unique)),
            "duplicate_candidate_rows": int(len(frame)-len(unique)),
            "charge_counts": {str(sign): {"generated": int((generated.sign == sign).sum()),
                       "selected_unique": int((unique.lb_sign == sign).sum())}
                              for sign in (-1, 1)},
            "by_charge": by_charge, "generated_bin_counts": den.tolist(), "selected_bin_counts": num.tolist(),
            "efficiency": (num/den).tolist(),
            "binomial_68pct_interval": [bounds(int(k), int(n)) for k, n in zip(num, den)]}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--generator", type=Path, required=True)
    ap.add_argument("--generated-events", type=int, default=100000)
    ap.add_argument("--stage1", type=Path, required=True)
    ap.add_argument("--stage2-manifest", type=Path, required=True)
    ap.add_argument("--output-dir", type=Path, required=True)
    args = ap.parse_args()
    if args.generated_events != 100000:
        ap.error("This named full-sample study requires exactly 100,000 input events")
    manifest = json.loads(args.stage2_manifest.read_text())
    if manifest["max_output_events"] is not None or manifest["record"]["events_processed"] != args.generated_events:
        raise ValueError("Stage 2 manifest is not a complete 100k run")
    if Path(manifest["input"]).resolve() != args.stage1.resolve():
        raise ValueError("Stage 2 did not use the requested Stage 1 tuple")
    source = f"{manifest['sample']}_{manifest['source_id']}"
    root = args.stage2_manifest.parent
    paths = {"stage1": root / "audit" / f"{source}.parquet",
             "offline": root / "offline_selected" / f"{source}.parquet",
             "bdt": root / "bdt_selected" / f"{source}.parquet"}
    for path in paths.values():
        if not path.is_file():
            raise ValueError(f"Missing Stage 2/BDT table {path}")
    print("Extracting generated PHSP angles from all 100k EDM4hep events", flush=True)
    rows = generated_angles(args.generator, args.generated_events)
    generated = pd.DataFrame(rows, columns=["raw_event", "mc_lb_index", "sign", "truth_angle"])
    if generated.empty or not generated.truth_angle.between(-1, 1).all():
        raise ValueError("Invalid generated direct-decay content")
    output = {"generator": str(args.generator), "generator_bytes": args.generator.stat().st_size,
              "stage1": str(args.stage1), "stage1_bytes": args.stage1.stat().st_size,
              "stage2_manifest": str(args.stage2_manifest), "stage2_manifest_sha256": sha(args.stage2_manifest),
              "model_sha256": manifest["model_sha256"], "model_summary_sha256": manifest["model_summary_sha256"],
              "fixed_bdt_score": manifest["bdt_score_cut"], "generated_input_events": args.generated_events,
              "generated_direct_decays": int(len(generated)), "bin_edges": BINS.tolist(),
              "stages": {}, "matching": {}}
    stages = {}
    for name, path in paths.items():
        raw = pd.read_parquet(path, columns=COLS)
        selected, error = match_generated(raw, generated)
        if selected.duplicated(["source_id", "event_entry", "candidate_slot"]).any():
            raise ValueError(f"Duplicate candidate key at {name}")
        stages[name] = selected
        output["matching"][name] = {"maximum_truth_angle_difference": error,
                                      "matched_candidate_rows": int(len(selected))}
        output["stages"][name] = stage_result(selected, generated)
        print(name, output["stages"][name]["unique_selected_decays"], flush=True)
    for parent, child in (("stage1", "offline"), ("offline", "bdt")):
        a = set(stages[parent].generated_decay_id)
        b = set(stages[child].generated_decay_id)
        if not b <= a:
            raise ValueError(f"{child} has generated decays absent from {parent}")
        output["stages"][child]["conditional_retention_from_previous"] = len(b)/len(a)
        parent_bins = np.asarray(output["stages"][parent]["selected_bin_counts"])
        child_bins = np.asarray(output["stages"][child]["selected_bin_counts"])
        output["stages"][child]["conditional_retention_by_generated_bin"] = (child_bins/parent_bins).tolist()
    selected = stages["bdt"].sort_values("bdt_score", ascending=False).drop_duplicates("generated_decay_id")
    residual = selected.cos_theta_p.to_numpy(dtype=float) - selected.generated_truth_angle.to_numpy(dtype=float)
    if not np.isfinite(residual).all() or not selected.cos_theta_p.between(-1, 1).all():
        raise ValueError("Invalid reconstructed cos(theta_p)")
    stats = {"mean": float(residual.mean()), "median": float(np.median(residual)),
             "rms": float(np.sqrt(np.mean(residual**2))),
             "q16": float(np.quantile(residual, .16)), "q84": float(np.quantile(residual, .84)),
             "central_68pct_half_width": float((np.quantile(residual, .84)-np.quantile(residual, .16))/2),
             "absolute_95pct_quantile": float(np.quantile(np.abs(residual), .95)),
             "fraction_abs_gt_0p1": float(np.mean(np.abs(residual) > .1)),
             "fraction_abs_gt_0p4": float(np.mean(np.abs(residual) > .4))}
    per_bin = []
    truth = selected.generated_truth_angle.to_numpy(dtype=float)
    for lo, hi in zip(BINS[:-1], BINS[1:]):
        values = residual[(truth >= lo) & (truth < hi if hi < 1 else truth <= hi)]
        per_bin.append({"low": float(lo), "high": float(hi), "candidates": len(values),
                        "median": float(np.median(values)) if len(values) else None,
                        "central_68pct_half_width": float((np.quantile(values, .84)-np.quantile(values, .16))/2) if len(values) >= 8 else None})
    migration = np.histogram2d(truth, selected.cos_theta_p.to_numpy(dtype=float), bins=(BINS, BINS))[0].astype(int)
    generated_bins = np.asarray(output["stages"]["bdt"]["generated_bin_counts"], dtype=float)
    response = migration / generated_bins[:, None]
    output["resolution"] = {"selected_unique_decays": len(selected), "residual_reco_minus_truth": stats,
                            "by_generated_bin": per_bin,
                            "migration_truth_rows_reco_columns": migration.tolist(),
                            "response_per_generated_decay_truth_rows_reco_columns": response.tolist()}
    args.output_dir.mkdir(parents=True, exist_ok=True)
    fit_rows = []
    for i, (low, high) in enumerate(zip(BINS[:-1], BINS[1:])):
        row = {"cos_theta_true_low": float(low), "cos_theta_true_high": float(high),
               "generated_decays": output["stages"]["bdt"]["generated_bin_counts"][i]}
        for stage in ("stage1", "offline", "bdt"):
            data = output["stages"][stage]
            row[f"{stage}_selected_decays"] = data["selected_bin_counts"][i]
            row[f"{stage}_efficiency"] = data["efficiency"][i]
        row["bdt_efficiency_68pct_low"], row["bdt_efficiency_68pct_high"] = (
            output["stages"]["bdt"]["binomial_68pct_interval"][i])
        fit_rows.append(row)
    pd.DataFrame(fit_rows).to_csv(args.output_dir / "cos_theta_p_acceptance_for_fit.csv", index=False)
    generated.to_parquet(args.output_dir / "generated_direct_decays.parquet", index=False)
    selected[["source_id", "event_entry", "candidate_slot", "lb_sign", "bdt_score", "lb_mass",
              "generated_decay_id", "generated_truth_angle", "truth_cos_theta_p", "cos_theta_p"]].to_parquet(
                  args.output_dir / "selected_direct_resolution.parquet", index=False)
    (args.output_dir / "acceptance_resolution.json").write_text(json.dumps(output, indent=2) + "\n")
    centers = (BINS[:-1]+BINS[1:])/2
    fig, ax = plt.subplots(figsize=(9, 5.8))
    colors = {"stage1": "#4c78a8", "offline": "#e09836", "bdt": "#ba4148"}
    for name, label in (("stage1", "Stage 1 candidate"), ("offline", "Offline selected"), ("bdt", "BDT selected")):
        data = output["stages"][name]
        low, high = np.asarray(data["binomial_68pct_interval"]).T
        efficiency = np.asarray(data["efficiency"])
        ax.errorbar(centers, efficiency, yerr=[efficiency-low, high-efficiency], fmt="o-", capsize=2,
                    label=f"{label} ({data['unique_selected_decays']:,})", color=colors[name])
    ax.set(xlabel=r"Generated $\cos\theta_p$", ylabel="Selected direct decays / generated direct decays",
           xlim=(-1, 1), ylim=(0, 1), title="100k PHSP v3 angular acceptance")
    ax.grid(alpha=.2)
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(args.output_dir / "cos_theta_p_acceptance.png", dpi=180)
    plt.close(fig)
    fig, ax = plt.subplots(figsize=(9, 5.8))
    for sign, label, color in ((1, r"$\Lambda_b$", "#2670a8"),
                               (-1, r"$\overline{\Lambda}_b$", "#ba4148")):
        values = output["stages"]["bdt"]["by_charge"][str(sign)]["efficiency"]
        ax.plot(centers, values, "o-", label=label, color=color)
    ax.set(xlabel=r"Generated $\cos\theta_p$", ylabel="BDT-selected direct decays / generated direct decays",
           xlim=(-1, 1), ylim=(0, 1), title="Full-selection PHSP efficiency by charge")
    ax.legend(frameon=False)
    ax.grid(alpha=.2)
    fig.tight_layout()
    fig.savefig(args.output_dir / "cos_theta_p_acceptance_by_charge.png", dpi=180)
    plt.close(fig)
    fig, axes = plt.subplots(1, 2, figsize=(13, 4.8))
    axes[0].hist(residual, bins=np.linspace(-.4, .4, 101), histtype="step", color="#2670a8")
    axes[0].set(xlabel=r"Reco $\cos\theta_p$ − truth $\cos\theta_p$", ylabel="Selected direct decays / bin",
                title="Core shown within ±0.4; see full-tail plot")
    axes[1].plot(centers, [r["median"] for r in per_bin], "o-", label="Median bias")
    axes[1].plot(centers, [r["central_68pct_half_width"] for r in per_bin], "s-", label="Central 68% half-width")
    axes[1].set(xlabel=r"Generated $\cos\theta_p$", ylabel=r"Absolute $\cos\theta_p$ units")
    axes[1].legend(frameon=False)
    for ax in axes:
        ax.grid(alpha=.2)
    fig.suptitle("After offline selection and fixed BDT score")
    fig.tight_layout()
    fig.savefig(args.output_dir / "cos_theta_p_resolution.png", dpi=180)
    plt.close(fig)
    fig, ax = plt.subplots(figsize=(8.5, 5.5))
    ax.hist(residual, bins=np.linspace(-2, 2, 161), histtype="step", color="#2670a8")
    ax.set(xlabel=r"Reco $\cos\theta_p$ − truth $\cos\theta_p$",
           ylabel="Selected direct decays / 0.025", yscale="log",
           title="Full helicity-angle residual, including non-Gaussian tails")
    ax.grid(alpha=.2)
    fig.tight_layout()
    fig.savefig(args.output_dir / "cos_theta_p_residual_full.png", dpi=180)
    plt.close(fig)
    fig, ax = plt.subplots(figsize=(7.5, 6))
    image = ax.imshow(migration, origin="lower", extent=(-1, 1, -1, 1), aspect="auto", cmap="viridis")
    fig.colorbar(image, ax=ax, label="Selected direct decays / bin")
    ax.set(xlabel=r"Reconstructed $\cos\theta_p$", ylabel=r"Generated $\cos\theta_p$",
           title="Truth → reconstructed bin migration after fixed BDT")
    fig.tight_layout()
    fig.savefig(args.output_dir / "cos_theta_p_migration.png", dpi=180)
    plt.close(fig)
    print(json.dumps({"generated_decays": len(generated),
                      "stage_counts": {k: v["unique_selected_decays"] for k,v in output["stages"].items()},
                      "resolution": stats}, indent=2))


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Compare original reco pointing with a paired angular-resolution scan."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from photon_pointing import photon_impact_parameters
from smear_stage1_v4_pointing import augment

PREFIX = "lb_photon_pointing_"


def sha256(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--input", type=Path, required=True,
                    help="Candidate-level v4 signal Parquet after Stage 1 or BDT")
    ap.add_argument("--output-dir", type=Path, required=True)
    ap.add_argument("--namespace", required=True)
    ap.add_argument("--anchor", choices=("reco", "truth"), default="reco",
                    help="Use origin-projected reco hit or ideal generated truth-ray hit")
    ap.add_argument("--seed", type=int, default=20261005)
    ap.add_argument("--max-mrad", type=float, default=2.0)
    ap.add_argument("--step-mrad", type=float, default=0.1)
    ap.add_argument("--input-events", type=int,
                    help="Stage-0 events processed to produce this candidate sample")
    args = ap.parse_args()
    if args.max_mrad <= 0 or args.step_mrad <= 0:
        ap.error("max-mrad and step-mrad must be positive")
    nsteps = int(round(args.max_mrad / args.step_mrad))
    if not np.isclose(nsteps * args.step_mrad, args.max_mrad):
        ap.error("max-mrad must be an integer multiple of step-mrad")
    sigmas = tuple(round(args.step_mrad * i, 8) for i in range(1, nsteps + 1))

    table = pq.read_table(args.input)
    # This input is the frozen BDT-selected signal pilot. Keep the explicit
    # truth match as a diagnostic label and reject no rows on pointing values.
    input_candidate_rows = len(table)
    truth_matched = table["truth_matched"].to_numpy() == 1
    truth_matched_rows = int(truth_matched.sum())
    table = table.filter(pa.array(truth_matched))
    stale = [name for name in table.column_names
             if name == "pointing_valid" or
             name.startswith(("photon_ip3d_mm_", "photon_d0_abs_mm_",
                              "photon_px_", "photon_py_", "photon_pz_"))]
    if stale:
        table = table.drop(stale)
    scanned = augment(table, args.namespace, args.anchor, args.seed, sigmas)
    selection_stage = "post-BDT" if "bdt_score" in scanned.column_names else "after Stage 1"

    def cols(names):
        return np.column_stack([scanned[PREFIX + name].to_numpy() for name in names])

    hit = cols([f"reco_hit_{axis}" for axis in "xyz"])
    pv = cols([f"pv_{axis}" for axis in "xyz"])
    true_vertex = cols([f"truth_v{axis}" for axis in "xyz"])
    true_momentum = cols([f"truth_p{axis}" for axis in "xyz"])
    true_line_ip3d, true_line_d0 = photon_impact_parameters(
        true_vertex, true_momentum, pv)
    decay_displacement = true_vertex - pv
    decay_distance_3d = np.linalg.norm(decay_displacement, axis=1)
    decay_distance_xy = np.linalg.norm(decay_displacement[:, :2], axis=1)
    reco_names = [f"lb_photon_p{axis}" for axis in "xyz"]
    if not all(name in scanned.column_names for name in reco_names):
        reco_names = [f"photon_p{axis}" for axis in "xyz"]
    reco = np.column_stack([scanned[name].to_numpy() for name in reco_names])
    baseline_ip3d, baseline_d0 = photon_impact_parameters(hit, reco, pv)
    scanned = scanned.append_column("photon_ip3d_mm_reco_baseline", pa.array(baseline_ip3d))
    scanned = scanned.append_column("photon_d0_abs_mm_reco_baseline", pa.array(baseline_d0))
    scanned = scanned.append_column("photon_ip3d_mm_truth_line", pa.array(true_line_ip3d))
    scanned = scanned.append_column("photon_d0_abs_mm_truth_line", pa.array(true_line_d0))

    out = args.output_dir
    out.mkdir(parents=True, exist_ok=True)
    stage_tag = "post_bdt" if selection_stage == "post-BDT" else "stage1"
    parquet_path = out / f"signal_{stage_tag}_pointing_scan.parquet"
    pq.write_table(scanned, parquet_path, compression="zstd")

    values = {"reco baseline": baseline_ip3d, "truth line": true_line_ip3d}
    for sigma in sigmas:
        tag = str(sigma).replace(".", "p")
        values[f"{sigma:g} mrad"] = scanned[f"photon_ip3d_mm_{tag}mrad"].to_numpy()
    all_values = np.concatenate([v[np.isfinite(v)] for v in values.values()])
    xmax = max(10.0, float(np.quantile(all_values, 0.995)))
    bins = np.linspace(0, xmax, 36)

    fig, (ax_hist, ax_quant) = plt.subplots(1, 2, figsize=(12, 4.8))
    ax_hist.hist(baseline_ip3d, bins=bins, histtype="step", linewidth=2.2,
                 color="black", label="Original reco direction")
    ax_hist.hist(true_line_ip3d, bins=bins, histtype="step", linewidth=1.8,
                 color="black", linestyle="--", label="Generated photon line (truth control)")
    for sigma in (0.1, 0.5, 1.0, 1.5, 2.0):
        if sigma > args.max_mrad or not np.isclose(sigma / args.step_mrad,
                                                   round(sigma / args.step_mrad)):
            continue
        tag = str(round(sigma, 8)).replace(".", "p")
        ax_hist.hist(scanned[f"photon_ip3d_mm_{tag}mrad"].to_numpy(),
                     bins=bins, histtype="step", label=f"{sigma:g} mrad/component")
    ax_hist.set(xlabel="Photon IP$_{3D}$ to reconstructed PV [mm]",
                ylabel="Candidates / bin", xlim=(0, xmax))
    ax_hist.legend(fontsize=8)

    medians, q16, q84 = [], [], []
    for sigma in sigmas:
        tag = str(sigma).replace(".", "p")
        v = scanned[f"photon_ip3d_mm_{tag}mrad"].to_numpy()
        medians.append(np.nanmedian(v)); q16.append(np.nanquantile(v, .16)); q84.append(np.nanquantile(v, .84))
    ax_quant.fill_between(sigmas, q16, q84, alpha=.2, label="16th–84th percentile")
    ax_quant.plot(sigmas, medians, marker="o", markersize=3, label="Median smeared IP")
    baseline_median = float(np.nanmedian(baseline_ip3d))
    ax_quant.axhline(baseline_median, color="black", linestyle="--",
                     label=f"Reco baseline median: {baseline_median:.3g} mm")
    true_line_median = float(np.nanmedian(true_line_ip3d))
    ax_quant.axhline(true_line_median, color="black", linestyle=":",
                     label=f"Truth-line median: {true_line_median:.3g} mm")
    ax_quant.set(xlabel="Angular sigma [mrad/component]",
                 ylabel="Photon IP$_{3D}$ to reconstructed PV [mm]",
                 xlim=(min(sigmas), max(sigmas)))
    ax_quant.legend(fontsize=8)
    hit_anchor = "reco-projected hit" if args.anchor == "reco" else "ideal truth-ray hit"
    fig.suptitle(f"Direct signal {selection_stage} ({len(scanned)} candidates)\n"
                 f"Emulated direction with {hit_anchor}; paired draws across resolutions")
    fig.tight_layout()
    plot_path = out / "signal_pointing_resolution_scan.png"
    fig.savefig(plot_path, dpi=180)
    plt.close(fig)

    summary = {
        "input": str(args.input.resolve()), "output_parquet": str(parquet_path.resolve()),
        "plot": str(plot_path.resolve()), "namespace": args.namespace,
        "input_sha256": sha256(args.input),
        "scan_script_sha256": sha256(Path(__file__)),
        "smearing_module_sha256": sha256(HERE / "smear_stage1_v4_pointing.py"),
        "geometry_module_sha256": sha256(HERE / "photon_pointing.py"),
        "seed": args.seed, "anchor": args.anchor,
        "anchor_definition": "origin projection from reconstructed photon momentum" if args.anchor == "reco" else "ideal effective-surface hit projected from generated photon vertex and momentum",
        "smeared_direction": "matched truth momentum plus paired tangent-plane Gaussian smear",
        "sigma_mrad_per_component": list(sigmas), "candidate_rows": len(scanned),
        "input_events_processed": args.input_events,
        "selection_stage": selection_stage,
        "input_candidate_rows_before_truth_label_filter": input_candidate_rows,
        "truth_matched_candidate_rows": truth_matched_rows,
        "all_scanned_rows_truth_matched": bool(np.all(scanned["truth_matched"].to_numpy() == 1)),
        "valid_pointing_rows": int(scanned["pointing_valid"].to_numpy().sum()),
        "baseline_ip3d_median_mm": baseline_median,
        "baseline_ip3d_q16_q84_mm": [float(np.nanquantile(baseline_ip3d, .16)),
                                      float(np.nanquantile(baseline_ip3d, .84))],
        "truth_line_ip3d_median_mm": true_line_median,
        "truth_line_ip3d_q16_q84_mm": [float(np.nanquantile(true_line_ip3d, .16)),
                                        float(np.nanquantile(true_line_ip3d, .84))],
        "photon_production_displacement_3d_q16_median_q84_mm": [
            float(np.nanquantile(decay_distance_3d, .16)),
            float(np.nanmedian(decay_distance_3d)),
            float(np.nanquantile(decay_distance_3d, .84))],
        "photon_production_displacement_xy_q16_median_q84_mm": [
            float(np.nanquantile(decay_distance_xy, .16)),
            float(np.nanmedian(decay_distance_xy)),
            float(np.nanquantile(decay_distance_xy, .84))],
        "scan_ip3d_quantiles_mm": {
            str(s): {"q16": float(a), "median": float(b), "q84": float(c)}
            for s, a, b, c in zip(sigmas, q16, medians, q84)},
        "interpretation_limit": "Conditional distribution of reconstructed truth-matched signal candidates. Truth is used only for diagnostic grouping, generated-line closure, and emulated direction. The truth-ray anchor is an ideal geometry control, not a measurement. This is not an efficiency, background comparison, data observable, or detector significance.",
    }
    (out / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()

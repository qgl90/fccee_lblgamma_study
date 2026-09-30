#!/usr/bin/env python3
"""Compare inclusive charged tracks with displaced V0 daughters in percent."""

import argparse
import csv
from dataclasses import asdict
import json
from pathlib import Path
import re

import awkward as ak
import numpy as np
import uproot

from resolution_tools import (
    binned_gaussian_resolution, load_sample, plot_fit_distributions,
    plot_efficiency_comparison, plot_resolution_comparison,
)


ETA_EDGES = np.linspace(-3.2, 3.2, 33)
PT_EDGES = np.geomspace(0.1, 60, 15)
R_EDGES = np.geomspace(1e-6, 2e4, 27)
GROUPS = [
    ("Lambda proton", 3122, 2212),
    ("Lambda pion", 3122, 211),
    ("Kshort pion", 310, 211),
]


def _flat(array):
    return ak.to_numpy(ak.flatten(array, axis=1))


def _displaced(path):
    branches = ["parent_pdg", "pdg", "matched", "truth_pt", "truth_eta",
                "vertex_rxy",
                "dp_rel", "dpt_rel"]
    with uproot.open(str(path), handler=uproot.source.file.MemmapSource) as root:
        tree = root["events"]
        values = tree.arrays(["daughter_" + name for name in branches], library="ak")
        n_events = tree.num_entries
    return n_events, {name: _flat(values["daughter_" + name]) for name in branches}


def _csv(path, series):
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["sample", "low", "high",
            "center", "n", "mean", "sigma", "sigma_error", "chi2_ndf"])
        writer.writeheader()
        for label, rows in series.items():
            for row in rows:
                writer.writerow({"sample": label, **asdict(row)})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inclusive", type=Path, default=Path(
        "outputs/analysis/studies/Lb2LambdaGamma_resolutions_12000events_from500k.root"))
    parser.add_argument("--displaced", type=Path, default=Path(
        "outputs/analysis/studies/Lb2LambdaGamma_displaced_500000events.root"))
    parser.add_argument("--output-dir", type=Path, default=Path(
        "outputs/plots/resolutions/comparison"))
    parser.add_argument("--target-pairs", type=int, default=200_000)
    parser.add_argument("--min-fit-entries", type=int, default=100)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    inclusive = load_sample(args.inclusive, args.target_pairs)
    n_displaced_events, daughter = _displaced(args.displaced)
    samples = {
        "All charged tracks": {
            "pt": inclusive.track_pt,
            "eta": inclusive.track_eta,
            "dp": inclusive.track_dp_rel,
            "dpt": inclusive.track_dpt_rel,
        }
    }
    generated = {
        "All charged tracks": {
            "pt": inclusive.track_truth_pt,
            "eta": inclusive.track_truth_eta,
            "rxy": inclusive.track_truth_rxy,
            "matched": inclusive.track_truth_matched == 1,
        }
    }
    near_origin = inclusive.track_rxy < 1.0
    near_origin_truth = inclusive.track_truth_rxy < 1.0
    samples["Near-origin tracks (Rxy < 1 mm)"] = {
        "pt": inclusive.track_pt[near_origin],
        "eta": inclusive.track_eta[near_origin],
        "dp": inclusive.track_dp_rel[near_origin],
        "dpt": inclusive.track_dpt_rel[near_origin],
    }
    generated["Near-origin tracks (Rxy < 1 mm)"] = {
        "pt": inclusive.track_truth_pt[near_origin_truth],
        "eta": inclusive.track_truth_eta[near_origin_truth],
        "rxy": inclusive.track_truth_rxy[near_origin_truth],
        "matched": inclusive.track_truth_matched[near_origin_truth] == 1,
    }
    for label, parent, child in GROUPS:
        species = ((daughter["parent_pdg"] == parent) &
                   (np.abs(daughter["pdg"]) == child))
        generated[label] = {
            "pt": daughter["truth_pt"][species],
            "eta": daughter["truth_eta"][species],
            "rxy": daughter["vertex_rxy"][species],
            "matched": daughter["matched"][species] == 1,
        }
        mask = species & (daughter["matched"] == 1)
        samples[label] = {
            "pt": daughter["truth_pt"][mask],
            "eta": daughter["truth_eta"][mask],
            "dp": daughter["dp_rel"][mask],
            "dpt": daughter["dpt_rel"][mask],
        }

    comparisons = [
        ("dpt_vs_pt", "dpt", "pt", PT_EDGES, "Truth pT [GeV]", "log", None),
        ("dpt_vs_eta", "dpt", "eta", ETA_EDGES, r"Truth $\eta$", "linear", None),
        ("dp_vs_eta", "dp", "eta", ETA_EDGES, r"Truth $\eta$", "linear", None),
        ("dp_vs_eta_pt_1_5", "dp", "eta", ETA_EDGES,
         r"Truth $\eta$", "linear", (1., 5.)),
    ]
    summary = {
        "inclusive_input": str(args.inclusive),
        "inclusive_events": inclusive.events_read,
        "inclusive_matched_tracks_retained": len(inclusive.track_pt),
        "displaced_input": str(args.displaced),
        "displaced_events": n_displaced_events,
        "relative_resolution_unit": "percent (100 times the relative residual)",
        "comparison_fiducial": "matched, true pT >= 0.1 GeV and |eta| <= 2.56",
        "near_origin_definition": "MC production Rxy < 1 mm from detector origin; not a reconstructed PV association",
        "generated_counts": {label: int(len(data["pt"]))
                             for label, data in generated.items()},
        "comparisons": {},
    }
    for slug, metric, variable, edges, xlabel, scale, pt_slice in comparisons:
        series = {}
        counts = {}
        for label, data in samples.items():
            pt, eta = data["pt"], data["eta"]
            residual = data[metric]
            mask = ((pt >= 0.1) & (np.abs(eta) <= 2.56) & np.isfinite(pt) &
                    np.isfinite(eta) & np.isfinite(residual) & (residual > -900))
            if pt_slice is not None:
                mask &= (pt >= pt_slice[0]) & (pt < pt_slice[1])
            x = data[variable][mask]
            y = 100 * residual[mask]
            rows = binned_gaussian_resolution(x, y, edges,
                                              args.min_fit_entries, xscale=scale)
            series[label] = rows
            counts[label] = int(mask.sum())
            diagnostic = args.output_dir / (slug + "_" +
                re.sub(r"[^a-z0-9]+", "_", label.lower()).strip("_") +
                "_fit_distributions.png")
            plot_fit_distributions(x, y, rows, diagnostic, xlabel, label,
                                   args.min_fit_entries,
                                   residual_label=(r"$100\Delta p/p$ [%]" if metric == "dp"
                                                   else r"$100\Delta p_T/p_T$ [%]"))
        ylabel = (r"Gaussian $\sigma(\Delta p/p)$ [%]" if metric == "dp"
                  else r"Gaussian $\sigma(\Delta p_T/p_T)$ [%]")
        title = (r"Momentum resolution: all tracks vs displaced $V^0$ daughters"
                 if metric == "dp" else
                 r"Transverse-momentum resolution: all vs displaced")
        if pt_slice:
            title += f" ({pt_slice[0]:g} ≤ pT < {pt_slice[1]:g} GeV)"
        plot_resolution_comparison(series, args.output_dir / (slug + ".png"),
                                   xlabel, ylabel, title, xscale=scale,
                                   acceptance_boundary=(2.56 if variable == "eta" else None))
        _csv(args.output_dir / (slug + ".csv"), series)
        summary["comparisons"][slug] = counts

    for slug, variable, edges, xlabel, scale in [
        ("match_fraction_vs_pt", "pt", PT_EDGES, "Truth pT [GeV]", "log"),
        ("match_fraction_vs_eta", "eta", ETA_EDGES,
         r"Truth $\eta$", "linear"),
        ("match_fraction_vs_rxy", "rxy", R_EDGES,
         "MC production Rxy [mm]", "log"),
    ]:
        populations = {}
        for label, data in generated.items():
            denominator = ((np.abs(data["eta"]) <= 2.56) if variable == "pt"
                           else (data["pt"] >= 0.1))
            if variable == "rxy":
                denominator &= np.abs(data["eta"]) <= 2.56
            populations[label] = (data[variable][denominator],
                                  data["matched"][denominator])
        rows = plot_efficiency_comparison(
            populations, edges, args.output_dir / (slug + ".png"),
            xlabel, "All tracks versus displaced daughters: match fraction",
            xscale=scale,
            acceptance_boundary=(2.56 if variable == "eta" else None))
        with (args.output_dir / (slug + ".csv")).open("w", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)

    (args.output_dir / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(f"Wrote inclusive/displaced comparisons to {args.output_dir}")


if __name__ == "__main__":
    main()

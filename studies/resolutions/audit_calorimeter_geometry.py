#!/usr/bin/env python3
"""Inspect at most 200 Stage-0 EDM4hep events for an offline ECAL surface model.

Use the repository's synchronous MemmapSource convention to avoid the CERN
environment's asynchronous file-source stalls. No reconstruction is run.
"""

import argparse
import hashlib
import json
from pathlib import Path
import sys

import awkward as ak
import numpy as np
import uproot

import matplotlib
matplotlib.use("Agg")
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "reconstruction"))
import v3_plot_style  # noqa: F401  (shared v3 mplhep style)
import matplotlib.pyplot as plt


def branch_values(tree, name, events, dtype):
    values = tree[name].array(entry_stop=events, library="ak")
    if len(values) != events:
        raise ValueError(f"Only {len(values)}/{events} entries read for {name}")
    return (ak.to_numpy(ak.flatten(values)).astype(
        np.float64 if np.dtype(dtype).kind == "f" else np.int64),
        ak.to_numpy(ak.num(values)))


def digest(path):
    h = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(4 * 1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def rounded_mode(values, step_mm=10.0):
    rounded = np.rint(values / step_mm) * step_mm
    values, counts = np.unique(rounded, return_counts=True)
    return float(values[np.argmax(counts)])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--events", type=int, default=200)
    parser.add_argument("--card", type=Path, default=Path("cards/card_IDEA.tcl"))
    parser.add_argument("--output-json", required=True, type=Path)
    parser.add_argument("--output-figure", required=True, type=Path)
    args = parser.parse_args()
    if not 1 <= args.events <= 200:
        parser.error("--events must be in [1, 200] for this audit")

    tree = uproot.open(args.input, handler=uproot.source.file.MemmapSource)["events"]
    if tree.num_entries < args.events:
        parser.error("Input has fewer than requested events")
    hit_prefix = "CalorimeterHits/CalorimeterHits."
    photon_prefix = "EFlowPhoton/EFlowPhoton."
    hit = {}
    hit_counts = None
    for name, dtype in (("position.x", ">f4"), ("position.y", ">f4"),
                        ("position.z", ">f4"), ("energy", ">f4")):
        hit[name], counts = branch_values(tree, hit_prefix + name, args.events, dtype)
        if hit_counts is not None and not np.array_equal(counts, hit_counts):
            raise ValueError(f"Hit multiplicity mismatch for {name}")
        hit_counts = counts
    photon = {}
    photon_counts = None
    for name in ("position.x", "position.y", "position.z",
                 "directionError.x", "directionError.y", "directionError.z"):
        photon[name], counts = branch_values(tree, photon_prefix + name,
                                             args.events, ">f4")
        if photon_counts is not None and not np.array_equal(counts, photon_counts):
            raise ValueError(f"Photon multiplicity mismatch for {name}")
        photon_counts = counts

    radius = np.hypot(hit["position.x"], hit["position.y"])
    abs_z = np.abs(hit["position.z"])
    barrel_radius = rounded_mode(radius)
    endcap_abs_z = rounded_mode(abs_z)
    barrel = np.abs(radius - barrel_radius) < 1.0
    endcap = np.abs(abs_z - endcap_abs_z) < 1.0
    summary = {
        "study": "v3_photon_pointing_geometry_200events",
        "input": str(args.input.resolve()),
        "input_sha256": digest(args.input),
        "card": str(args.card.resolve()),
        "card_sha256": digest(args.card),
        "events_inspected": args.events,
        "calorimeter_hits": len(radius),
        "eflow_photons": len(photon["position.x"]),
        "surface_tolerance_mm": 1.0,
        "barrel_radius_mm": barrel_radius,
        "endcap_abs_z_mm": endcap_abs_z,
        "surface_estimator": "Most frequent 10 mm-rounded radius and absolute z; check all hit positions within 1 mm of either surface.",
        "hits_on_barrel": int(barrel.sum()),
        "hits_on_endcap": int(endcap.sum()),
        "hits_on_both_seam": int((barrel & endcap).sum()),
        "hits_on_neither": int((~(barrel | endcap)).sum()),
        "hits_with_nonzero_energy": int(np.count_nonzero(hit["energy"])),
        "eflow_photons_with_nonzero_position": int(np.count_nonzero(
            np.hypot(photon["position.x"], photon["position.y"]) +
            np.abs(photon["position.z"]))),
        "eflow_photons_with_nonzero_direction_error": int(np.count_nonzero(
            np.abs(photon["directionError.x"]) +
            np.abs(photon["directionError.y"]) +
            np.abs(photon["directionError.z"]))),
        "interpretation": "Hit positions support an idealized barrel/endcap surface; zero energy and EFlowPhoton direction/position fields do not provide measured pointing.",
    }
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(summary, indent=2) + "\n")

    fig, ax = plt.subplots(figsize=(7.0, 6.2))
    ax.scatter(abs_z[barrel], radius[barrel], s=5, alpha=.25,
               label=f"Barrel surface ({int(barrel.sum())} hits)")
    ax.scatter(abs_z[endcap & ~barrel], radius[endcap & ~barrel], s=5,
               alpha=.35, label=f"Endcap surface ({int((endcap & ~barrel).sum())} hits)")
    ax.axhline(barrel_radius, color="black", linestyle="--", linewidth=1)
    ax.axvline(endcap_abs_z, color="black", linestyle=":", linewidth=1)
    ax.set(xlabel="|z| of calorimeter hit [mm]", ylabel="Calorimeter hit radius [mm]",
           xlim=(0, 2700), ylim=(0, 2450),
           title=f"IDEA Stage 0 calorimeter positions, first {args.events} events")
    ax.set_aspect("equal", adjustable="box")
    ax.legend(loc="lower left")
    fig.tight_layout()
    args.output_figure.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(args.output_figure, dpi=180)
    plt.close(fig)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()

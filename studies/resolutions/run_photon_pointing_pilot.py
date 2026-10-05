#!/usr/bin/env python3
"""Validate offline photon pointing on at most 200 existing Stage 0 events.

This is an object-response diagnostic with PV fixed at the origin. It does
not process Stage 1, apply the BDT, or estimate analysis rejection.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import subprocess

import awkward as ak
import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq
import uproot
import matplotlib
matplotlib.use("Agg")
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "reconstruction"))
import v3_plot_style  # noqa: F401
import matplotlib.pyplot as plt

from photon_pointing import CalorimeterSurface, unit, smear_direction, photon_impact_parameters


def sha256(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--config", type=Path, default=Path("config/photon_pointing_idealized_v3.json"))
    parser.add_argument("--events", type=int, default=200)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    if not 1 <= args.events <= 200:
        parser.error("This pilot is capped at 200 events")
    cfg = json.loads(args.config.read_text())
    geom = CalorimeterSurface(**cfg["geometry"])
    tree = uproot.open(args.input, handler=uproot.source.file.MemmapSource)["events"]
    if tree.num_entries < args.events:
        parser.error("Input contains fewer than requested events")
    names = {
        "r_type": "ReconstructedParticles/ReconstructedParticles.type",
        "r_e": "ReconstructedParticles/ReconstructedParticles.energy",
        "m_pdg": "Particle/Particle.PDG", "m_status": "Particle/Particle.generatorStatus",
        "parent_begin": "Particle/Particle.parents_begin",
        "parent_end": "Particle/Particle.parents_end",
        "parents": "Particle#0/Particle#0.index",
        "assoc_reco": "MCRecoAssociations#0/MCRecoAssociations#0.index",
        "assoc_mc": "MCRecoAssociations#1/MCRecoAssociations#1.index",
    }
    for axis in "xyz":
        names[f"r_{axis}"] = f"ReconstructedParticles/ReconstructedParticles.momentum.{axis}"
        names[f"m_{axis}"] = f"Particle/Particle.momentum.{axis}"
        names[f"v_{axis}"] = f"Particle/Particle.vertex.{axis}"
    arrays = tree.arrays(list(names.values()), entry_stop=args.events, library="ak")
    records = []
    all_reco_photons = 0
    for event in range(args.events):
        a = {key: ak.to_numpy(arrays[name][event]) for key, name in names.items()}
        nr, nm = len(a["r_type"]), len(a["m_pdg"])
        ar, am = a["assoc_reco"], a["assoc_mc"]
        valid = (ar >= 0) & (ar < nr) & (am >= 0) & (am < nm)
        ar, am = ar[valid], am[valid]
        r_counts = np.bincount(ar, minlength=nr)
        m_counts = np.bincount(am, minlength=nm)
        mapping = np.full(nr, -1, dtype=int)
        mapping[ar] = am
        for r in np.flatnonzero(a["r_type"] == 22):
            all_reco_photons += 1
            m = mapping[r]
            if m < 0 or r_counts[r] != 1 or m_counts[m] != 1 or a["m_status"][m] != 1 or a["m_pdg"][m] != 22:
                continue
            parents = a["parents"][a["parent_begin"][m]:a["parent_end"][m]]
            parents = parents[(parents >= 0) & (parents < nm)]
            record = {"event_entry": event, "photon_reco_index": int(r),
                      "photon_mc_index": int(m), "reco_energy_gev": float(a["r_e"][r]),
                      "direct_lb_photon": bool(np.any(np.abs(a["m_pdg"][parents]) == 5122))}
            for axis in "xyz":
                record[f"reco_p{axis}"] = float(a[f"r_{axis}"][r])
                record[f"true_p{axis}"] = float(a[f"m_{axis}"][m])
                record[f"true_vertex_{axis}_mm"] = float(a[f"v_{axis}"][m])
            records.append(record)
    if not records:
        raise ValueError("No uniquely associated stable MC photons in the pilot")
    rows = {key: np.array([r[key] for r in records]) for key in records[0]}
    reco = np.column_stack([rows[f"reco_p{axis}"] for axis in "xyz"])
    truth = np.column_stack([rows[f"true_p{axis}"] for axis in "xyz"])
    vertex = np.column_stack([rows[f"true_vertex_{axis}_mm"] for axis in "xyz"])
    hit, region = geom.intersect_from_origin(reco)
    rows["surface_region"] = region
    for i, axis in enumerate("xyz"):
        rows[f"predicted_hit_{axis}_mm"] = hit[:, i]
    rows["truth_ip3d_mm"], rows["truth_ipxy_mm"] = photon_impact_parameters(vertex, truth, [0, 0, 0])
    rows["reco_true_angle_mrad"] = 1000 * np.arccos(np.clip(np.sum(unit(reco) * unit(truth), axis=1), -1, 1))
    normals = np.random.default_rng(cfg["seed"]).normal(size=(len(records), 2))
    scenarios = {}
    for sigma in cfg["pointing_sigma_mrad"]:
        tag = f"sigma_{sigma:g}mrad".replace(".", "p")
        direction = smear_direction(truth, sigma / 1000, normals)
        ip3d, ipxy = photon_impact_parameters(hit, direction, [0, 0, 0])
        rows[f"{tag}_ip3d_mm"], rows[f"{tag}_ipxy_mm"] = ip3d, ipxy
        for i, axis in enumerate("xyz"):
            rows[f"{tag}_p{axis}"] = rows["reco_energy_gev"] * direction[:, i]
        result = {}
        for label, mask in (("direct_lb_photons", rows["direct_lb_photon"]),
                            ("other_matched_photons", ~rows["direct_lb_photon"])):
            good = mask & (region != 0) & np.isfinite(ip3d)
            result[label] = {"photons": int(good.sum()),
                "ip3d_quantiles_mm": dict(zip(["q16", "q50", "q84", "q95"],
                    np.quantile(ip3d[good], [.16, .5, .84, .95]).tolist())) if good.any() else {},
                "truth_ip3d_median_mm": float(np.median(rows["truth_ip3d_mm"][good])) if good.any() else None}
        scenarios[tag] = result
    args.output_dir.mkdir(parents=True, exist_ok=True)
    pq.write_table(pa.table(rows), args.output_dir / "photon_pointing_pilot.parquet", compression="zstd")
    summary = {"input": str(args.input.resolve()), "input_bytes": args.input.stat().st_size,
               "input_sha256": sha256(args.input),
               "script_sha256": sha256(__file__),
               "geometry_module_sha256": sha256(Path(__file__).with_name("photon_pointing.py")),
               "command_arguments": sys.argv,
               "repository_head_at_run": subprocess.check_output(
                   ["git", "rev-parse", "HEAD"], text=True).strip(),
               "config": cfg, "config_sha256": hashlib.sha256(args.config.read_bytes()).hexdigest(),
               "events": args.events, "all_reco_type22_photons": all_reco_photons,
               "unique_stable_mc_photons": len(records),
               "unmatched_or_nonunique_or_nonphoton": all_reco_photons - len(records),
               "geometry_invalid_or_outside_aperture": int((region == 0).sum()),
               "pv_assumption_mm": [0, 0, 0],
               "scope": "200-event Stage 0 object diagnostic; no Stage 1, BDT, or Zss rejection estimate",
               "scenarios": scenarios}
    (args.output_dir / "pointing_pilot.json").write_text(json.dumps(summary, indent=2) + "\n")

    fig, axes = plt.subplots(1, 2, figsize=(11, 4.5))
    for ax, label, mask in zip(axes, ["Direct Λb photon", "Other matched photons"],
                               [rows["direct_lb_photon"], ~rows["direct_lb_photon"]]):
        good = mask & (region != 0)
        if not good.any():
            ax.text(.5, .5, "No photons", transform=ax.transAxes)
            continue
        tags = list(scenarios)
        xmax = max(5, np.quantile(rows[f"{tags[-1]}_ip3d_mm"][good], .99))
        bins = np.linspace(0, xmax, 60)
        # Normalize by all eligible photons, retaining a meaningful overflow.
        weights = np.ones(int(good.sum())) / good.sum()
        ax.hist(rows["truth_ip3d_mm"][good], bins=bins, weights=weights, histtype="step",
                color="black", linestyle="--", label="Truth photon line")
        for sigma, tag in zip(cfg["pointing_sigma_mrad"], tags):
            ax.hist(rows[f"{tag}_ip3d_mm"][good], bins=bins, weights=weights,
                    histtype="step", label=f"{sigma:g} mrad/component")
        ax.set(xlabel="Photon line IP to origin [mm]", ylabel="Fraction of photons / bin",
               title=f"{label}: {int(good.sum())} photons")
        ax.legend(fontsize=7)
    fig.suptitle("Offline pointing pilot: 200 Stage 0 events, reconstructed-direction hit proxy")
    fig.tight_layout()
    fig.savefig(args.output_dir / "pointing_pilot.png", dpi=180)
    plt.close(fig)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()

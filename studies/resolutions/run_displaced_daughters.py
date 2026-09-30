#!/usr/bin/env python3
"""Study IDEA tracking of direct Lambda0 and K0S charged decay daughters."""

import argparse
import csv
from dataclasses import asdict
import json
from pathlib import Path

import awkward as ak
import numpy as np
import uproot

from resolution_tools import (
    binned_gaussian_resolution, plot_efficiency, plot_efficiency_map,
    plot_resolution, plot_scatter,
)


FIELDS = [
    "parent_pdg", "pdg", "matched", "n_links", "truth_p", "truth_pt",
    "truth_eta", "vertex_rxy", "vertex_z", "reco_p", "reco_pt",
    "dp_rel", "dpt_rel", "dqoverpt",
]

GROUPS = [
    ("lambda_proton", 3122, 2212, r"$\Lambda^0 \to p$"),
    ("lambda_pion", 3122, 211, r"$\Lambda^0 \to \pi$"),
    ("kshort_pion", 310, 211, r"$K^0_S \to \pi$"),
]

PT_EDGES = np.geomspace(0.1, 60, 15)
P_EDGES = np.geomspace(0.1, 100, 16)
ETA_EDGES = np.linspace(-3.2, 3.2, 33)
R_EDGES = np.array([0.1, 1, 2, 5, 10, 20, 50, 100, 200, 400,
                    800, 1200, 1800, 2400, 5000, 10000, 20000.], dtype=float)
Z_EDGES = np.array([0.1, 2, 5, 10, 20, 50, 100, 200, 400,
                    800, 1200, 1800, 2400, 3000, 5000, 10000, 20000.], dtype=float)


def _write_csv(path, rows):
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(asdict(rows[0])))
        writer.writeheader()
        writer.writerows(asdict(row) for row in rows)


def _load(path):
    with uproot.open(str(path), handler=uproot.source.file.MemmapSource) as root:
        tree = root["events"]
        data = tree.arrays(["daughter_" + field for field in FIELDS], library="ak")
        events = tree.num_entries
    return events, {field: ak.to_numpy(ak.flatten(data["daughter_" + field], axis=1))
                    for field in FIELDS}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=Path(
        "outputs/analysis/studies/Lb2LambdaGamma_displaced_500000events.root"))
    parser.add_argument("--output-dir", type=Path, default=Path(
        "outputs/plots/resolutions/displaced_daughters"))
    parser.add_argument("--min-fit-entries", type=int, default=100)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    events, data = _load(args.input)
    summary = {"input": str(args.input), "events": events, "groups": {},
               "match_definition": "exactly one MCRecoAssociation to a charged reco particle with a track",
               "fiducial": "truth pT >= 0.1 GeV and |eta| <= 2.56 for vertex scans",
               "relative_resolution_unit": "percent (100 times the relative residual)"}

    for slug, parent, daughter, title in GROUPS:
        species = (data["parent_pdg"] == parent) & (np.abs(data["pdg"]) == daughter)
        group = {name: values[species] for name, values in data.items()}
        pt = group["truth_pt"]
        eta = group["truth_eta"]
        abs_eta = np.abs(eta)
        radius = group["vertex_rxy"]
        abs_z = np.abs(group["vertex_z"])
        matched = group["matched"] == 1
        fiducial = (pt >= 0.1) & (abs_eta <= 2.56)
        good = fiducial & matched & np.isfinite(group["dpt_rel"]) & (group["dpt_rel"] > -900)
        dpt_percent = 100 * group["dpt_rel"]
        dp_percent = 100 * group["dp_rel"]

        destination = args.output_dir / slug
        destination.mkdir(parents=True, exist_ok=True)
        summary["groups"][slug] = {
            "generated": int(species.sum()),
            "matched": int(matched.sum()),
            "fiducial_generated": int(fiducial.sum()),
            "fiducial_matched": int((fiducial & matched).sum()),
            "ambiguous_links": int((group["n_links"] > 1).sum()),
        }

        # pT and eta scans apply the complementary card acceptance requirement.
        # Vertex scans apply both pT and eta requirements so their denominator
        # measures tracking as a function of the daughter production point.
        variables = [
            ("pt", pt, PT_EDGES, "Truth pT [GeV]", "log", abs_eta <= 2.56),
            ("eta", eta, ETA_EDGES, r"Truth $\eta$", "linear", pt >= 0.1),
            ("rxy", radius, R_EDGES, "Production radius Rxy [mm]", "log", fiducial),
            ("abs_z", abs_z, Z_EDGES, "Production |z| [mm]", "log", fiducial),
        ]
        for name, x, edges, label, scale, denominator in variables:
            mask = denominator & np.isfinite(x)
            plot_efficiency(x[mask], {"Reco track matched": matched[mask]}, edges,
                            destination / f"match_fraction_vs_{name}.png",
                            label, f"{title}: track match fraction", xscale=scale,
                            acceptance_boundary=(2.56 if name == "eta" else None))
            fit_mask = good & np.isfinite(x)
            rows = binned_gaussian_resolution(
                x[fit_mask], dpt_percent[fit_mask], edges,
                args.min_fit_entries, xscale=scale)
            _write_csv(destination / f"dpt_resolution_vs_{name}.csv", rows)
            plot_resolution(rows, destination / f"dpt_resolution_vs_{name}.png",
                            label, r"Gaussian $\sigma(\Delta p_T/p_T)$ [%]",
                            f"{title}: pT core resolution",
                            xscale=scale, raw_x=x[fit_mask],
                            raw_residual=dpt_percent[fit_mask],
                            min_fit_entries=args.min_fit_entries,
                            residual_label=r"$100\Delta p_T/p_T$ [%]",
                            acceptance_boundary=(2.56 if name == "eta" else None))

        # Momentum slices make vertex trends easier to interpret: a change in
        # the daughter pT spectrum with decay radius otherwise changes the fit.
        for low_pt, high_pt in [(0.1, 1.), (1., 5.), (5., 60.)]:
            tag = f"pt_{low_pt:g}_{high_pt:g}"
            pt_slice = fiducial & (pt >= low_pt) & (pt < high_pt)
            for name, x, edges, label in [
                ("rxy", radius, R_EDGES, "Production radius Rxy [mm]"),
                ("abs_z", abs_z, Z_EDGES, "Production |z| [mm]"),
            ]:
                mask = pt_slice & np.isfinite(x)
                plot_efficiency(x[mask], {"Reco track matched": matched[mask]},
                                edges, destination / f"match_fraction_vs_{name}_{tag}.png",
                                label, f"{title}: {low_pt:g} ≤ pT < {high_pt:g} GeV")
                fit_mask = mask & matched & np.isfinite(group["dpt_rel"]) & (
                    group["dpt_rel"] > -900)
                rows = binned_gaussian_resolution(x[fit_mask],
                                                   dpt_percent[fit_mask],
                                                   edges, args.min_fit_entries)
                _write_csv(destination / f"dpt_resolution_vs_{name}_{tag}.csv", rows)
                plot_resolution(rows, destination / f"dpt_resolution_vs_{name}_{tag}.png",
                                label, r"Gaussian $\sigma(\Delta p_T/p_T)$ [%]",
                                f"{title}: {low_pt:g} ≤ pT < {high_pt:g} GeV",
                                raw_x=x[fit_mask],
                                raw_residual=dpt_percent[fit_mask],
                                min_fit_entries=args.min_fit_entries,
                                residual_label=r"$100\Delta p_T/p_T$ [%]")

        # Curvature response is sensitive to the track fit in a solenoid.
        qmask = good & np.isfinite(group["dqoverpt"]) & (group["dqoverpt"] > -900)
        qrows = binned_gaussian_resolution(pt[qmask], group["dqoverpt"][qmask],
                                           PT_EDGES, args.min_fit_entries)
        _write_csv(destination / "dqoverpt_resolution_vs_pt.csv", qrows)
        plot_resolution(qrows, destination / "dqoverpt_resolution_vs_pt.png",
                        "Truth pT [GeV]", r"Gaussian $\sigma$ of $\Delta(q/p_T)$ [1/GeV]",
                        f"{title}: curvature core resolution",
                        raw_x=pt[qmask], raw_residual=group["dqoverpt"][qmask],
                        min_fit_entries=args.min_fit_entries,
                        residual_label=r"$\Delta(q/p_T)$ [1/GeV]")

        pmask = good & np.isfinite(group["truth_p"]) & np.isfinite(group["dp_rel"])
        prows = binned_gaussian_resolution(group["truth_p"][pmask],
                                           dp_percent[pmask], P_EDGES,
                                           args.min_fit_entries)
        _write_csv(destination / "dp_resolution_vs_p.csv", prows)
        plot_resolution(prows, destination / "dp_resolution_vs_p.png",
                        "Truth p [GeV]", r"Gaussian $\sigma(\Delta p/p)$ [%]",
                        f"{title}: momentum core resolution",
                        raw_x=group["truth_p"][pmask],
                        raw_residual=dp_percent[pmask],
                        min_fit_entries=args.min_fit_entries,
                        residual_label=r"$100\Delta p/p$ [%]")

        eta_dp_mask = pmask
        eta_dp_rows = binned_gaussian_resolution(
            eta[eta_dp_mask], dp_percent[eta_dp_mask], ETA_EDGES,
            args.min_fit_entries, xscale="linear")
        _write_csv(destination / "dp_resolution_vs_eta.csv", eta_dp_rows)
        plot_resolution(eta_dp_rows, destination / "dp_resolution_vs_eta.png",
                        r"Truth $\eta$", r"Gaussian $\sigma(\Delta p/p)$ [%]",
                        f"{title}: momentum resolution versus angle", xscale="linear",
                        raw_x=eta[eta_dp_mask],
                        raw_residual=dp_percent[eta_dp_mask],
                        min_fit_entries=args.min_fit_entries,
                        residual_label=r"$100\Delta p/p$ [%]",
                        acceptance_boundary=2.56)

        map_mask = fiducial & np.isfinite(radius) & np.isfinite(eta)
        plot_efficiency_map(radius[map_mask], eta[map_mask], matched[map_mask],
                            R_EDGES, ETA_EDGES, destination / "match_fraction_rxy_eta.png",
                            "Production radius Rxy [mm]", r"Truth $\eta$",
                            f"{title}: match fraction by origin and angle")
        plot_scatter(group["vertex_z"], radius,
                     destination / "production_z_rxy.png", "Production z [mm]",
                     "Production Rxy [mm]", f"{title}: truth production points")

    (args.output_dir / "summary.json").write_text(
        json.dumps(summary, indent=2) + "\n")
    print(f"Read {events} events; wrote displaced-daughter plots to {args.output_dir}")
    for slug, counts in summary["groups"].items():
        print(f"  {slug}: {counts['generated']} generated, {counts['matched']} matched")


if __name__ == "__main__":
    main()

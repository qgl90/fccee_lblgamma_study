#!/usr/bin/env python3
"""Selection, matching, and energy response of Lambda_b -> Lambda0 gamma photons."""

import argparse
import csv
from dataclasses import asdict
import json
from pathlib import Path

import awkward as ak
import numpy as np
import uproot

from resolution_tools import binned_gaussian_resolution, plot_efficiency, plot_resolution
from run_study import _ecal_relative


BRANCHES = [
    "gamma_signal", "gamma_truth_e", "gamma_truth_eta", "gamma_matched",
    "gamma_selected", "gamma_dE_rel",
]
E_EDGES = np.geomspace(0.2, 60, 17)
ETA_EDGES = np.linspace(-3.5, 3.5, 29)


def _flat(array):
    return ak.to_numpy(ak.flatten(array, axis=1))


def _load(path, chunk_events):
    pieces = {name: [] for name in BRANCHES}
    events = no_signal = multi_signal = 0
    with uproot.open(str(path), handler=uproot.source.file.MemmapSource) as root:
        tree = root["events"]
        for chunk in tree.iterate(BRANCHES, library="ak", step_size=chunk_events):
            events += len(chunk)
            counts = ak.sum(chunk["gamma_signal"] == 1, axis=1)
            no_signal += int(ak.sum(counts == 0))
            multi_signal += int(ak.sum(counts > 1))
            signal = chunk["gamma_signal"] == 1
            for name in BRANCHES:
                pieces[name].append(_flat(chunk[name][signal]))
    data = {name: np.concatenate(parts) if parts else np.array([])
            for name, parts in pieces.items()}
    return events, no_signal, multi_signal, data


def _csv(path, rows):
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(asdict(rows[0])))
        writer.writeheader()
        writer.writerows(asdict(row) for row in rows)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=Path(
        "outputs/analysis/studies/Lb2LambdaGamma_resolutions_500000events.root"))
    parser.add_argument("--output-dir", type=Path, default=Path(
        "outputs/plots/resolutions/signal_photons"))
    parser.add_argument("--chunk-events", type=int, default=10_000)
    parser.add_argument("--min-fit-entries", type=int, default=100)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    events, no_signal, multi_signal, data = _load(args.input, args.chunk_events)
    energy = data["gamma_truth_e"]
    eta = data["gamma_truth_eta"]
    matched = data["gamma_matched"] == 1
    selected = data["gamma_selected"] == 1
    residual = 100 * data["gamma_dE_rel"]
    fiducial = (energy >= 2.0) & (np.abs(eta) <= 3.0)
    out = args.output_dir

    # Both curves use every generated signal photon in the stated truth bin.
    # The selected flag is set only for a uniquely matched photon in Photon#0.
    for slug, x, edges, denominator, xlabel, scale, boundary in [
        ("energy", energy, E_EDGES, np.abs(eta) <= 3.0,
         "Signal-photon truth E [GeV]", "log", None),
        ("eta", eta, ETA_EDGES, energy >= 2.0,
         r"Signal-photon truth $\eta$", "linear", 3.0),
    ]:
        plot_efficiency(x[denominator],
                        {"Raw unique match": matched[denominator],
                         "PhotonEfficiency selected": selected[denominator]},
                        edges, out / f"signal_match_fraction_vs_{slug}.png",
                        xlabel, r"$\Lambda_b\to\Lambda^0\gamma$ photon acceptance",
                        xscale=scale, acceptance_boundary=boundary)

    valid = matched & np.isfinite(residual) & (residual > -900) & (
        energy > 0) & (np.abs(eta) <= 3.0)
    for slug, x, edges, xlabel, scale, reference, boundary in [
        ("energy", energy, E_EDGES, "Signal-photon truth E [GeV]", "log",
         _ecal_relative, None),
        ("eta", eta, ETA_EDGES, r"Signal-photon truth $\eta$", "linear",
         None, 3.0),
    ]:
        for label, mask in [("raw", valid), ("selected", valid & selected)]:
            rows = binned_gaussian_resolution(
                x[mask], residual[mask], edges, args.min_fit_entries,
                xscale=scale)
            filename = f"signal_{label}_resolution_vs_{slug}"
            _csv(out / (filename + ".csv"), rows)
            plot_resolution(rows, out / (filename + ".png"), xlabel,
                            r"Gaussian $\sigma(\Delta E/E)$ [%]",
                            f"Signal photon: {label} reconstructed response",
                            reference=reference, xscale=scale,
                            raw_x=x[mask], raw_residual=residual[mask],
                            min_fit_entries=args.min_fit_entries,
                            residual_label=r"$100\Delta E/E$ [%]",
                            acceptance_boundary=boundary)

    summary = {
        "input": str(args.input), "events": events,
        "signal_definition": "stable direct photon of |PDG|=5122 parent with direct |PDG|=3122 daughter",
        "events_without_signal": no_signal,
        "events_with_multiple_signal_photons": multi_signal,
        "generated_signal_photons": int(len(energy)),
        "raw_matched": int(matched.sum()),
        "selected": int(selected.sum()),
        "fiducial_generated": int(fiducial.sum()),
        "fiducial_raw_matched": int((fiducial & matched).sum()),
        "fiducial_selected": int((fiducial & selected).sum()),
        "relative_resolution_unit": "percent (100 times relative residual)",
    }
    (out / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()

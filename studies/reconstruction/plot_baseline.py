#!/usr/bin/env python3
"""Inspect Lambda_b -> Lambda0 gamma or Lambda0 eta candidate trees with uproot."""

import argparse
import csv
import json
from pathlib import Path

import awkward as ak
import numpy as np
import uproot

from plotting import (candidate_multiplicity, flight_overlay, mass_overlay,
                      matched_mass_scatter)


MASS_EDGES = np.linspace(4.9, 6.3, 71)
MASS_ZOOM_EDGES = np.linspace(4.9, 6.3, 141)
LAMBDA_EDGES = np.linspace(1.0, 3.0, 121)

BRANCHES = [
    "event_entry", "n_tracks", "n_photons", "n_lambdas", "n_lb",
    "n_lambdas_mass_window", "n_lambdas_fit_valid", "n_lambdas_fit_good",
    "n_lb_before_mass_window",
    "n_lambdas_nonprimary_tracks", "n_lambdas_track_displaced", "n_neutrals",
    "pv_valid", "pv_x", "pv_y", "pv_z",
    "n_truth_matched_lb", "lb_mass", "lb_lambda_mass", "lb_truth_matched",
    "lb_lambda_slot", "lb_proton_index", "lb_pion_index",
    "lb_photon_index", "lb_photon2_index", "lb_sign",
    "lb_truth_lb_mc_index", "lb_truth_neutral_mc_index",
    "lb_neutral_mass", "lambda_vertex_chi2", "lambda_vertex_primary",
    "lambda_flight_rxy", "lambda_flight_xyz", "lambda_truth_matched",
    "lambda_proton_d0sig", "lambda_pion_d0sig",
    "lambda_flight_rxy_sigma", "lambda_flight_rxy_sig",
    "lb_mass_hypothesis_correct", "reco_mc_index", "reco_mc_pdg",
    "reco_mc_n_parents", "reco_mc_parent_index", "reco_mc_parent_pdg",
    "reco_mc_grandparent_index", "reco_mc_grandparent_pdg",
    "reco_mc_greatgrandparent_index", "reco_mc_greatgrandparent_pdg",
    "reco_mc_greatgreatgrandparent_index", "reco_mc_greatgreatgrandparent_pdg",
    "reco_p", "reco_energy", "reco_mc_p",
    "reco_mc_energy", "reco_mc_pt", "reco_mc_eta", "reco_mc_vertex_rxy",
    "reco_mc_cos_opening",
]
OPTIONAL_ANCESTRY_BRANCHES = (
    "reco_mc_greatgrandparent_index", "reco_mc_greatgrandparent_pdg",
    "reco_mc_greatgreatgrandparent_index", "reco_mc_greatgreatgrandparent_pdg",
)

TRUTH_COLUMNS = [
    "event_entry", "candidate_slot", "lb_mass", "lambda_mass", "lb_sign",
    "neutral_mass", "lb_mc_index", "neutral_mc_index",
    "mass_hypothesis_correct", "lambda_vertex_chi2",
    "lambda_flight_rxy", "lambda_flight_xyz",
    "lambda_flight_rxy_sigma", "lambda_flight_rxy_sig",
    "lambda_proton_d0sig", "lambda_pion_d0sig",
]
for leg in ("proton", "pion", "photon", "photon2"):
    TRUTH_COLUMNS += [
        f"{leg}_reco_index", f"{leg}_mc_index", f"{leg}_mc_pdg",
        f"{leg}_mc_n_parents", f"{leg}_mc_parent_index",
        f"{leg}_mc_parent_pdg", f"{leg}_mc_grandparent_index",
        f"{leg}_mc_grandparent_pdg",
        f"{leg}_mc_greatgrandparent_index", f"{leg}_mc_greatgrandparent_pdg",
        f"{leg}_mc_greatgreatgrandparent_index",
        f"{leg}_mc_greatgreatgrandparent_pdg",
        f"{leg}_reco_p", f"{leg}_reco_energy", f"{leg}_mc_p",
        f"{leg}_mc_energy", f"{leg}_mc_pt", f"{leg}_mc_eta",
        f"{leg}_mc_vertex_rxy", f"{leg}_mc_cos_opening",
    ]


def _flat(array):
    return ak.to_numpy(ak.flatten(array, axis=1))


def _truth_rows(block, matched, mode):
    columns = {
        "event_entry": _flat(ak.broadcast_arrays(
            block["event_entry"], block["lb_mass"])[0][matched]),
        "candidate_slot": _flat(ak.local_index(block["lb_mass"])[matched]),
        "lb_mass": _flat(block["lb_mass"][matched]),
        "lambda_mass": _flat(block["lb_lambda_mass"][matched]),
        "lb_sign": _flat(block["lb_sign"][matched]),
        "neutral_mass": _flat(block["lb_neutral_mass"][matched]),
        "lb_mc_index": _flat(block["lb_truth_lb_mc_index"][matched]),
        "neutral_mc_index": _flat(block["lb_truth_neutral_mc_index"][matched]),
        "mass_hypothesis_correct": _flat(
            block["lb_mass_hypothesis_correct"][matched]),
    }
    lambda_slots = block["lb_lambda_slot"][matched]
    for name in ("lambda_vertex_chi2", "lambda_flight_rxy",
                 "lambda_flight_xyz", "lambda_flight_rxy_sigma",
                 "lambda_flight_rxy_sig", "lambda_proton_d0sig",
                 "lambda_pion_d0sig"):
        columns[name] = _flat(block[name][lambda_slots])
    for leg in ("proton", "pion", "photon", "photon2"):
        reco_branch = "lb_photon2_index" if leg == "photon2" else f"lb_{leg}_index"
        reco = block[reco_branch][matched]
        columns[f"{leg}_reco_index"] = _flat(reco)
        if leg == "photon2" and mode == "gamma":
            for field in ("mc_index", "mc_pdg", "mc_n_parents",
                          "mc_parent_index", "mc_parent_pdg",
                          "mc_grandparent_index", "mc_grandparent_pdg",
                          "mc_greatgrandparent_index", "mc_greatgrandparent_pdg",
                          "mc_greatgreatgrandparent_index",
                          "mc_greatgreatgrandparent_pdg",
                          "reco_p", "reco_energy", "mc_p", "mc_energy",
                          "mc_pt", "mc_eta", "mc_vertex_rxy",
                          "mc_cos_opening"):
                columns[f"{leg}_{field}"] = np.full(
                    len(columns["lb_mass"]), -999. if field in (
                        "reco_p", "reco_energy", "mc_p", "mc_energy",
                        "mc_pt", "mc_eta", "mc_vertex_rxy",
                        "mc_cos_opening") else -1)
            continue
        for field, branch in [
            ("mc_index", "reco_mc_index"),
            ("mc_pdg", "reco_mc_pdg"),
            ("mc_n_parents", "reco_mc_n_parents"),
            ("mc_parent_index", "reco_mc_parent_index"),
            ("mc_parent_pdg", "reco_mc_parent_pdg"),
            ("mc_grandparent_index", "reco_mc_grandparent_index"),
            ("mc_grandparent_pdg", "reco_mc_grandparent_pdg"),
            ("mc_greatgrandparent_index", "reco_mc_greatgrandparent_index"),
            ("mc_greatgrandparent_pdg", "reco_mc_greatgrandparent_pdg"),
            ("mc_greatgreatgrandparent_index",
             "reco_mc_greatgreatgrandparent_index"),
            ("mc_greatgreatgrandparent_pdg",
             "reco_mc_greatgreatgrandparent_pdg"),
            ("reco_p", "reco_p"),
            ("reco_energy", "reco_energy"),
            ("mc_p", "reco_mc_p"),
            ("mc_energy", "reco_mc_energy"),
            ("mc_pt", "reco_mc_pt"),
            ("mc_eta", "reco_mc_eta"),
            ("mc_vertex_rxy", "reco_mc_vertex_rxy"),
            ("mc_cos_opening", "reco_mc_cos_opening"),
        ]:
            columns[f"{leg}_{field}"] = (_flat(block[branch][reco])
                                         if branch in block.fields else
                                         np.full(len(columns["lb_mass"]),
                                                 0 if field.endswith("_pdg") else -1))
    size = len(columns["lb_mass"])
    if not all(len(v) == size for v in columns.values()):
        raise ValueError("Truth-component columns have unequal lengths")
    for row in zip(*(columns[name] for name in TRUTH_COLUMNS)):
        yield dict(zip(TRUTH_COLUMNS, (v.item() if hasattr(v, "item") else v
                                       for v in row)))


def _check_truth_components(csv_path, mode):
    """Validate labelled daughter identities and summarize their truth phase space."""
    sign_counts = {"Lambda_b": 0, "anti_Lambda_b": 0}
    legs = ("proton", "pion", "photon", "photon2") if mode == "eta" else (
        "proton", "pion", "photon")
    phase_space = {f"{leg}_mc_{field}": []
                   for leg in legs
                   for field in ("pt", "eta", "vertex_rxy")}
    masses = {"lb": [], "lambda": []}
    response = {leg: [] for leg in legs}
    opening = {leg: [] for leg in legs}
    seen = set()
    with csv_path.open(newline="") as handle:
        for row in csv.DictReader(handle):
            sign = int(row["lb_sign"])
            expected = (sign * 2212, -sign * 211, 22,
                        sign * 3122, sign * 3122,
                        221 if mode == "eta" else sign * 5122)
            actual = tuple(int(row[key]) for key in (
                "proton_mc_pdg", "pion_mc_pdg", "photon_mc_pdg",
                "proton_mc_parent_pdg", "pion_mc_parent_pdg",
                "photon_mc_parent_pdg"))
            if actual != expected:
                raise ValueError(f"Unexpected matched daughter identities: {actual}")
            if mode == "eta" and (
                    int(row["photon2_mc_pdg"]) != 22 or
                    int(row["photon2_mc_parent_pdg"]) != 221):
                raise ValueError("Eta photon pair has unexpected MC identities")
            if int(row["mass_hypothesis_correct"]) != 1:
                raise ValueError("Truth-matched candidate has wrong mass hypothesis")
            lb = int(row["lb_mc_index"])
            neutral = int(row["neutral_mc_index"])
            if (int(row["proton_mc_parent_index"]) !=
                    int(row["pion_mc_parent_index"]) or
                    int(row["proton_mc_grandparent_index"]) != lb or
                    int(row["pion_mc_grandparent_index"]) != lb):
                raise ValueError("Lambda daughters have inconsistent MC ancestors")
            if mode == "eta":
                if (int(row["photon_mc_parent_index"]) != neutral or
                        int(row["photon2_mc_parent_index"]) != neutral or
                        int(row["photon_mc_grandparent_index"]) != lb or
                        int(row["photon2_mc_grandparent_index"]) != lb):
                    raise ValueError("Eta photons have inconsistent MC ancestors")
            elif (int(row["photon_mc_index"]) != neutral or
                  int(row["photon_mc_parent_index"]) != lb):
                raise ValueError("Direct photon has inconsistent MC ancestors")
            triplet = tuple(row[key] for key in (
                "event_entry", "proton_mc_index", "pion_mc_index",
                "photon_mc_index", "photon2_mc_index"))
            if triplet in seen:
                raise ValueError(f"Duplicate matched MC triplet: {triplet}")
            seen.add(triplet)
            if not np.isclose(float(row["proton_mc_vertex_rxy"]),
                              float(row["pion_mc_vertex_rxy"]), atol=1e-4):
                raise ValueError("Matched Lambda daughters have different truth vertices")
            sign_counts["Lambda_b" if sign > 0 else "anti_Lambda_b"] += 1
            masses["lb"].append(float(row["lb_mass"]))
            masses["lambda"].append(float(row["lambda_mass"]))
            for leg in response:
                reco_key = f"{leg}_reco_energy" if leg.startswith("photon") else f"{leg}_reco_p"
                mc_key = f"{leg}_mc_energy" if leg.startswith("photon") else f"{leg}_mc_p"
                response[leg].append(float(row[reco_key]) / float(row[mc_key]))
                opening[leg].append(float(row[f"{leg}_mc_cos_opening"]))
            for key in phase_space:
                phase_space[key].append(float(row[key]))
    high = np.asarray(masses["lb"]) > 6.0
    summary = {
        "matched_charge_counts": sign_counts,
        "truth_phase_space_units": {"pt": "GeV", "eta": "unitless", "vertex_rxy": "mm"},
        "truth_phase_space_median": {key: float(np.median(values)) if values else None
                                     for key, values in phase_space.items()},
        "component_identity_and_vertex_checks_passed": True,
        "diagnostic_high_mass_threshold_gev": 6.0,
        "matched_high_mass_count": int(np.count_nonzero(high)),
        "matched_lambda_mass_median_by_lb_region_gev": {
            "lb_le_6gev": float(np.median(np.asarray(masses["lambda"])[~high]))
            if np.any(~high) else None,
            "lb_gt_6gev": float(np.median(np.asarray(masses["lambda"])[high]))
            if np.any(high) else None,
        },
        "matched_response_median_by_lb_region": {
            leg: {
                "lb_le_6gev": float(np.median(np.asarray(values)[~high]))
                if np.any(~high) else None,
                "lb_gt_6gev": float(np.median(np.asarray(values)[high]))
                if np.any(high) else None,
            } for leg, values in response.items()
        },
        "matched_direction_cosine_median_by_lb_region": {
            leg: {
                "lb_le_6gev": float(np.median(np.asarray(values)[~high]))
                if np.any(~high) else None,
                "lb_gt_6gev": float(np.median(np.asarray(values)[high]))
                if np.any(high) else None,
            } for leg, values in opening.items()
        },
    }
    return summary, masses


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=Path(
        "outputs/analysis/studies/Lb2LambdaGamma_baseline_1000events.root"))
    parser.add_argument("--output-dir", type=Path, default=Path(
        "outputs/plots/reconstruction/baseline"))
    parser.add_argument("--chunk-events", type=int, default=50)
    parser.add_argument("--selection-config", type=Path,
                        help="JSON config used for a selected reconstruction run")
    parser.add_argument("--mode", choices=("gamma", "eta"), default="gamma")
    parser.add_argument("--neutral-selection-config", type=Path,
                        help="JSON eta mass-window config, for eta mode")
    parser.add_argument("--efficiency-summary", type=Path,
                        help="Event-level signal cutflow JSON to annotate mass plots")
    args = parser.parse_args()
    config = json.loads(args.selection_config.read_text()) if args.selection_config else None
    neutral_config = (json.loads(args.neutral_selection_config.read_text())
                      if args.neutral_selection_config else None)
    if args.mode == "eta" and (config is None or neutral_config is None):
        parser.error("eta mode needs both --selection-config and --neutral-selection-config")
    label = "Configured" if config else "Uncut"
    decay_label = (r"$\Lambda_b\to\Lambda^0\eta(\gamma\gamma)$" if args.mode == "eta"
                   else r"$\Lambda_b\to\Lambda^0\gamma$")
    lambda_edges = (np.linspace(config["lambda_mass_min_gev"] - 0.05,
                                config["lambda_mass_max_gev"] + 0.05, 141)
                    if config else LAMBDA_EDGES)
    flight_edges = np.geomspace(0.1, 1000., 61)
    neutral_edges = (np.linspace(neutral_config["eta_mass_min_gev"] - 0.05,
                                 neutral_config["eta_mass_max_gev"] + 0.05, 121)
                     if neutral_config else None)
    args.output_dir.mkdir(parents=True, exist_ok=True)

    counts = {
        "all_mass": np.zeros(len(MASS_EDGES) - 1, dtype=np.int64),
        "truth_mass": np.zeros(len(MASS_EDGES) - 1, dtype=np.int64),
        "all_zoom": np.zeros(len(MASS_ZOOM_EDGES) - 1, dtype=np.int64),
        "truth_zoom": np.zeros(len(MASS_ZOOM_EDGES) - 1, dtype=np.int64),
        "all_lambda": np.zeros(len(lambda_edges) - 1, dtype=np.int64),
        "truth_lambda": np.zeros(len(lambda_edges) - 1, dtype=np.int64),
        "all_flight": np.zeros(len(flight_edges) - 1, dtype=np.int64),
        "truth_flight": np.zeros(len(flight_edges) - 1, dtype=np.int64),
    }
    if neutral_edges is not None:
        counts["all_neutral"] = np.zeros(len(neutral_edges) - 1, dtype=np.int64)
        counts["truth_neutral"] = np.zeros(len(neutral_edges) - 1, dtype=np.int64)
    events = candidates = truth_candidates = events_with_truth = 0
    before_lb_window = 0
    correct_hypotheses = 0
    mass_window_lambdas = nonprimary_lambdas = displaced_lambdas = 0
    fitted_lambdas = good_lambdas = valid_pvs = neutrals = 0
    multiplicities = []
    output_csv = args.output_dir / "truth_matched_components.csv"
    with output_csv.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=TRUTH_COLUMNS)
        writer.writeheader()
        with uproot.open(str(args.input),
                         handler=uproot.source.file.MemmapSource) as root:
            tree = root["events"]
            read_branches = [name for name in BRANCHES
                             if name not in OPTIONAL_ANCESTRY_BRANCHES or
                             name in tree.keys()]
            for block in tree.iterate(read_branches, library="ak",
                                      step_size=args.chunk_events):
                events += len(block)
                candidates += int(ak.sum(block["n_lb"]))
                before_lb_window += int(ak.sum(block["n_lb_before_mass_window"]))
                truth_candidates += int(ak.sum(block["n_truth_matched_lb"]))
                mass_window_lambdas += int(ak.sum(block["n_lambdas_mass_window"]))
                nonprimary_lambdas += int(ak.sum(block["n_lambdas_nonprimary_tracks"]))
                displaced_lambdas += int(ak.sum(block["n_lambdas_track_displaced"]))
                fitted_lambdas += int(ak.sum(block["n_lambdas_fit_valid"]))
                good_lambdas += int(ak.sum(block["n_lambdas_fit_good"]))
                valid_pvs += int(ak.sum(block["pv_valid"]))
                neutrals += int(ak.sum(block["n_neutrals"]))
                correct_hypotheses += int(ak.sum(
                    ak.sum(block["lb_mass_hypothesis_correct"], axis=1)))
                events_with_truth += int(ak.sum(block["n_truth_matched_lb"] > 0))
                multiplicities.extend(ak.to_list(block["n_lb"]))
                if not ak.all(block["n_lb"] == ak.num(block["lb_mass"])):
                    raise ValueError("Candidate count and mass-vector length differ")
                matched = block["lb_truth_matched"] == 1
                if int(ak.sum(ak.sum(matched, axis=1))) != int(
                        ak.sum(block["n_truth_matched_lb"])):
                    raise ValueError("Truth-label counts are inconsistent")

                all_mass = _flat(block["lb_mass"])
                truth_mass = _flat(block["lb_mass"][matched])
                all_lambda = _flat(block["lb_lambda_mass"])
                truth_lambda = _flat(block["lb_lambda_mass"][matched])
                for key, values, edges in [
                    ("all_mass", all_mass, MASS_EDGES),
                    ("truth_mass", truth_mass, MASS_EDGES),
                    ("all_zoom", all_mass, MASS_ZOOM_EDGES),
                    ("truth_zoom", truth_mass, MASS_ZOOM_EDGES),
                    ("all_lambda", all_lambda, lambda_edges),
                    ("truth_lambda", truth_lambda, lambda_edges),
                ]:
                    counts[key] += np.histogram(values[np.isfinite(values)],
                                                bins=edges)[0]
                if config:
                    flight = _flat(block["lambda_flight_rxy"])
                    truth_flight = _flat(block["lambda_flight_rxy"][
                        block["lambda_truth_matched"] == 1])
                    counts["all_flight"] += np.histogram(flight, flight_edges)[0]
                    counts["truth_flight"] += np.histogram(truth_flight,
                                                           flight_edges)[0]
                if neutral_edges is not None:
                    counts["all_neutral"] += np.histogram(
                        _flat(block["lb_neutral_mass"]), neutral_edges)[0]
                    counts["truth_neutral"] += np.histogram(
                        _flat(block["lb_neutral_mass"][matched]), neutral_edges)[0]
                writer.writerows(_truth_rows(block, matched, args.mode))

    efficiency_note = None
    if args.efficiency_summary:
        cutflow = json.loads(args.efficiency_summary.read_text())
        if cutflow["stages"][-1]["events"] != events_with_truth:
            raise ValueError("Signal efficiency and mass-plot truth event counts disagree")
        efficiency_note = (
            f"Signal efficiency: {100 * cutflow['acceptance_times_reconstruction_times_selection']:.1f}% "
            f"({events_with_truth}/{cutflow['generated_events']} events)\n"
            f"Reco matched: {100 * cutflow['acceptance_times_reconstruction']:.1f}%  ·  "
            f"selection given reco: {100 * cutflow['selection_given_reco']:.1f}%")
    mass_overlay(MASS_EDGES, counts["all_mass"], counts["truth_mass"],
                 args.output_dir / "lb_mass_all.png",
                 r"Reconstructed $m(p\pi\gamma)$ [GeV]",
                 f"{label} {decay_label} combinations",
                 annotation=efficiency_note)
    mass_overlay(MASS_ZOOM_EDGES, counts["all_zoom"], counts["truth_zoom"],
                 args.output_dir / "lb_mass_zoom.png",
                 r"Reconstructed $m(p\pi\gamma)$ [GeV]",
                 rf"{label} $\Lambda_b$ mass: 4.9–6.3 GeV fit range",
                 annotation=efficiency_note)
    mass_overlay(lambda_edges, counts["all_lambda"], counts["truth_lambda"],
                 args.output_dir / "lambda_mass.png",
                 r"Reconstructed $m(p\pi)$ [GeV]",
                 f"{label} proton–pion mass hypotheses")
    candidate_multiplicity(multiplicities,
                           args.output_dir / "candidates_per_event.png", label)
    if config:
        flight_overlay(flight_edges, counts["all_flight"],
                       counts["truth_flight"], config["min_flight_rxy_mm"],
                       args.output_dir / "lambda_flight_rxy.png")
    if neutral_edges is not None:
        mass_overlay(neutral_edges, counts["all_neutral"],
                     counts["truth_neutral"],
                     args.output_dir / "eta_mass.png",
                     r"Reconstructed $m(\gamma\gamma)$ [GeV]",
                     r"Configured $\eta\to\gamma\gamma$ candidate masses")
    summary = {
        "input": str(args.input), "events": events,
        "candidate_definition": ("opposite-charge non-PV tracks pass d0 and two-track vertex cuts; both proton/pion assignments use the fitted-vertex momenta, with the in-window assignment closest in absolute Lambda0 mass retained; crossed with selected photons, then Lambda_b fit-range and optional same-thrust-hemisphere cuts"
                                 if config else "both p/pi mass assignments for each opposite-sign track pair, crossed with every type-22 reconstructed photon; no candidate cuts"),
        "mode": args.mode,
        "selection_config": config,
        "neutral_selection_config": neutral_config,
        "all_candidates": candidates,
        "candidates_before_lb_mass_window": before_lb_window,
        "lambda_mass_window_candidates": mass_window_lambdas,
        "lambda_nonprimary_track_pairs": nonprimary_lambdas,
        "lambda_displaced_track_candidates": displaced_lambdas,
        "lambda_valid_vertex_fits": fitted_lambdas,
        "lambda_good_vertices": good_lambdas,
        "events_with_valid_pv": valid_pvs,
        "neutral_candidates": neutrals,
        "correct_mass_hypothesis_candidates": correct_hypotheses,
        "truth_matched_candidates": truth_candidates,
        "events_with_truth_matched_candidate": events_with_truth,
        "mean_candidates_per_event": candidates / events if events else 0,
        "max_candidates_in_event": max(multiplicities, default=0),
        "truth_definition": ("unique bidirectional associations; p and pi share Lambda0; both photons share eta; Lambda0 and eta share direct Lambda_b parent"
                             if args.mode == "eta" else "unique bidirectional associations; p and pi share Lambda0; photon and Lambda0 share direct Lambda_b parent"),
    }
    truth_checks, matched_masses = _check_truth_components(output_csv, args.mode)
    summary.update(truth_checks)
    matched_mass_scatter(matched_masses["lb"], matched_masses["lambda"],
                         args.output_dir / "matched_lb_vs_lambda_mass.png",
                         f"{label} truth-matched masses",
                         xlim=(4.9, 6.3),
                         ylim=(config["lambda_mass_min_gev"] - 0.05,
                               config["lambda_mass_max_gev"] + 0.05)
                         if config else (0.9, 4.5))
    if sum(summary["matched_charge_counts"].values()) != truth_candidates:
        raise ValueError("Truth-component CSV and candidate count differ")
    (args.output_dir / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()

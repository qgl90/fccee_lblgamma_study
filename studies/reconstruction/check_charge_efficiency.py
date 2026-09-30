#!/usr/bin/env python3
"""Audit Λb and anti-Λb generated denominators and reconstruction cutflow."""

import argparse
import csv
import json
from pathlib import Path

import awkward as ak
import numpy as np
import pyarrow.parquet as pq
import uproot


def generated_chains(path, n_events):
    with uproot.open(str(path),
                     handler=uproot.source.file.MemmapSource) as root:
        arrays = root["events"].arrays(
            ["Particle/Particle.PDG", "Particle/Particle.daughters_begin",
             "Particle/Particle.daughters_end", "Particle#1/Particle#1.index"],
            entry_stop=n_events, library="ak")
    chains = []
    for pdg_ak, first_ak, last_ak, daughters_ak in zip(
            arrays["Particle/Particle.PDG"],
            arrays["Particle/Particle.daughters_begin"],
            arrays["Particle/Particle.daughters_end"],
            arrays["Particle#1/Particle#1.index"]):
        pdg = ak.to_list(pdg_ak)
        first = ak.to_list(first_ak)
        last = ak.to_list(last_ak)
        daughters = ak.to_list(daughters_ak)

        def children(index):
            return [daughters[k] for k in range(first[index], last[index])]

        event_chains = []
        for i, code in enumerate(pdg):
            if abs(code) != 5122:
                continue
            sign = 1 if code > 0 else -1
            daughters_lb = children(i)
            lambdas = [j for j in daughters_lb if pdg[j] == sign * 3122]
            photons = [j for j in daughters_lb if pdg[j] == 22]
            if not photons:
                continue
            for lambda_index in lambdas:
                lambda_children = children(lambda_index)
                protons = [j for j in lambda_children if pdg[j] == sign * 2212]
                pions = [j for j in lambda_children if pdg[j] == -sign * 211]
                for proton in protons:
                    for pion in pions:
                        event_chains.append({"sign": sign, "lb": i,
                                             "lambda": lambda_index,
                                             "proton": proton, "pion": pion,
                                             "photons": photons})
        chains.append(event_chains)
    return chains


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mc", type=Path, required=True)
    parser.add_argument("--cutflow", type=Path, required=True)
    parser.add_argument("--selected-parquet", type=Path, required=True)
    parser.add_argument("--baseline-truth-csv", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    with uproot.open(str(args.cutflow),
                     handler=uproot.source.file.MemmapSource) as root:
        tree = root["events"]
        n_events = tree.num_entries
        flags = tree.arrays(["event_entry", "raw_truth_candidate",
                             "selected_photon", "valid_pv", "event_tracks",
                             "nonprimary_tracks", "daughter_d0",
                             "vertex_fit_valid", "vertex_chi2",
                             "flight_significance", "lambda_mass_window",
                             "lb_mass_window", "same_hemisphere"], library="np")
    chains = generated_chains(args.mc, n_events)
    signs = [[item["sign"] for item in event] for event in chains]
    if len(signs) != n_events or any(len(item) == 0 for item in signs):
        raise ValueError("At least one input event has no generated direct signal decay")
    entries = flags["event_entry"].astype(np.int64)
    if not np.array_equal(np.sort(entries), np.arange(n_events)):
        raise ValueError("Cutflow event entries do not cover the first N MC events")
    selected = pq.read_table(args.selected_parquet,
                             columns=["event_entry", "truth_matched", "lb_sign"])
    selected_entry = selected["event_entry"].to_numpy().astype(np.int64)
    selected_truth = selected["truth_matched"].to_numpy().astype(bool)
    selected_sign = selected["lb_sign"].to_numpy().astype(np.int8)
    if np.count_nonzero(flags["same_hemisphere"]) != len(
            np.unique(selected_entry[selected_truth])):
        raise ValueError("Selected candidate events disagree with event cutflow")
    if any(int(sign) not in signs[int(entry)] for entry, sign in
           zip(selected_entry[selected_truth], selected_sign[selected_truth])):
        raise ValueError("Selected truth-matched candidate charge disagrees with generated decay")
    raw_by_sign = {1: set(), -1: set()}
    with args.baseline_truth_csv.open(newline="") as handle:
        for row in csv.DictReader(handle):
            sign = int(row["lb_sign"])
            raw_by_sign[sign].add(int(row["event_entry"]))
    result = {"generated_events": n_events,
              "generated_signal_decays": sum(len(item) for item in signs),
              "events_with_two_signal_decays": sum(len(item) == 2 for item in signs),
              "charge_counts": {},
              "definition": "direct generated Λb/anti-Λb→Λ0(pπ)γ decay; charges counted separately"}
    for sign, label in ((1, "Lambda_b"), (-1, "anti_Lambda_b")):
        denominator = sum(sign in item for item in signs)
        raw_count = len(raw_by_sign[sign])
        selected_count = int(np.count_nonzero(selected_truth & (selected_sign == sign)))
        if any(sign not in signs[entry] for entry in raw_by_sign[sign]):
            raise ValueError(f"Baseline truth match has wrong generated charge for {label}")
        result["charge_counts"][label] = {
            "generated": denominator,
            "raw_truth_matched_events": raw_count,
            "raw_reconstruction_efficiency": raw_count / denominator,
            "selected_truth_matched": selected_count,
            "efficiency": selected_count / denominator,
        }
    if sum(result["charge_counts"][label]["selected_truth_matched"] for
           label in result["charge_counts"]) != int(np.count_nonzero(selected_truth)):
        raise ValueError("Charge-split selected counts do not sum to total")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Measure a candidate-photon pi0/eta veto after Lambda0 mass selection.

Pair the selected photon of each Lambda_b candidate with every *other* photon
in its thrust hemisphere from the same reconstructed Photon collection.
Store the nearest pi0 and eta
mass distances, then scan veto windows. The candidate and companion photons
use their measured EDM4hep four-vectors. MC ancestry is used only for the
reported signal/eta/background categories, never for the veto decision.
"""

import argparse
import json
import os
from collections import defaultdict
from pathlib import Path
import tempfile

import awkward as ak
import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq
import uproot

PHOTON_BRANCHES = [
    "Photon#0/Photon#0.index",
    "ReconstructedParticles/ReconstructedParticles.energy",
    "ReconstructedParticles/ReconstructedParticles.momentum.x",
    "ReconstructedParticles/ReconstructedParticles.momentum.y",
    "ReconstructedParticles/ReconstructedParticles.momentum.z",
]
MASSES = {"pi0": 0.1349768, "eta": 0.547862}
WINDOWS = [(0, 0), (20, 0), (0, 50), (30, 0), (0, 75),
           (20, 30), (20, 50), (30, 50), (30, 75),
           (40, 75), (50, 100)]  # MeV half-windows


def diphoton_mass(e1, x1, y1, z1, e2, x2, y2, z2):
    e = e1 + e2
    mass2 = e * e - (x1 + x2) ** 2 - (y1 + y2) ** 2 - (z1 + z2) ** 2
    return np.sqrt(mass2) if mass2 > 0 else np.nan


def photon_key(index, energy):
    """Use the persisted float32 EDM energy bits to identify a photon."""
    return int(index), np.float32(energy).tobytes()


def add_distances(table, edm_path, max_events, match_by_photon=False):
    rows = table.to_pydict()
    event_rows = defaultdict(list)
    photon_rows = defaultdict(list)
    for row, entry in enumerate(rows["event_entry"]):
        if match_by_photon:
            photon_rows[photon_key(rows["photon_reco_index"][row],
                                   rows["photon_reco_energy"][row])].append(row)
        else:
            event_rows[int(entry)].append(row)
    n = len(rows["event_entry"])
    nearest_pi0 = np.full(n, np.nan)
    nearest_eta = np.full(n, np.nan)
    n_other_photons = np.zeros(n, dtype=np.int32)
    original_entry = np.full(n, -1, dtype=np.int64)
    print(f"Opening {edm_path} for {n} candidate rows", flush=True)
    # MultithreadedFileSource avoids a stalled mmap read observed for these
    # large local EDM4hep files in the managed workspace.
    with uproot.open(str(edm_path),
                     handler=uproot.source.file.MultithreadedFileSource) as root:
        tree = root["events"]
        print(f"Opened {edm_path}: {tree.num_entries} events", flush=True)
        if max_events > tree.num_entries:
            raise ValueError(f"Requested {max_events} events from {tree.num_entries}")
        for block_start in range(0, max_events, 1000):
            block_end = min(block_start + 1000, max_events)
            if not match_by_photon and not any(block_start <= k < block_end for k in event_rows):
                continue
            if block_start % 10000 == 0:
                print(f"  reading events {block_start}:{block_end}", flush=True)
            block = tree.arrays(PHOTON_BRANCHES, entry_start=block_start,
                                entry_stop=block_end, library="ak")
            indices = block[PHOTON_BRANCHES[0]]
            energy = block[PHOTON_BRANCHES[1]]
            px, py, pz = (block[key] for key in PHOTON_BRANCHES[2:])
            for entry in range(block_start, block_end):
                loc = entry - block_start
                photon_indices = ak.to_list(indices[loc])
                if match_by_photon:
                    candidate_rows = []
                    for photon in photon_indices:
                        candidate_rows.extend(photon_rows.get(
                            photon_key(photon, energy[loc][photon]), []))
                else:
                    candidate_rows = event_rows.get(entry)
                if not candidate_rows:
                    continue
                es, xs, ys, zs = (ak.to_numpy(v[loc]) for v in
                                  (energy, px, py, pz))
                for row in candidate_rows:
                    selected = int(rows["photon_reco_index"][row])
                    if selected not in photon_indices:
                        raise ValueError(f"Candidate photon {selected} missing in event {entry}")
                    if original_entry[row] != -1:
                        raise ValueError(f"Photon key matched multiple original events for row {row}")
                    original_entry[row] = entry
                    axis = np.array([rows["thrust_x"][row],
                                     rows["thrust_y"][row],
                                     rows["thrust_z"][row]])
                    selected_side = np.dot(axis, [xs[selected], ys[selected], zs[selected]])
                    pairs = []
                    for partner in photon_indices:
                        if partner == selected:
                            continue
                        partner_side = np.dot(axis, [xs[partner], ys[partner], zs[partner]])
                        if selected_side * partner_side <= 0:
                            continue
                        n_other_photons[row] += 1
                        m = diphoton_mass(es[selected], xs[selected],
                                          ys[selected], zs[selected],
                                          es[partner], xs[partner],
                                          ys[partner], zs[partner])
                        if np.isfinite(m):
                            pairs.append(m)
                    if pairs:
                        nearest_pi0[row] = min(abs(m - MASSES["pi0"]) for m in pairs)
                        nearest_eta[row] = min(abs(m - MASSES["eta"]) for m in pairs)
    if np.any(original_entry < 0):
        raise ValueError(f"No original event found for {np.count_nonzero(original_entry < 0)} candidate rows")
    return (table.append_column("nearest_pi0_mass_distance_gev", pa.array(nearest_pi0))
                 .append_column("nearest_eta_mass_distance_gev", pa.array(nearest_eta))
                 .append_column("n_other_same_hemisphere_photons", pa.array(n_other_photons))
                 .append_column("original_event_entry", pa.array(original_entry)))


def category_counts(table, category):
    cols = table.to_pydict()
    pi0 = np.asarray(cols["nearest_pi0_mass_distance_gev"])
    eta = np.asarray(cols["nearest_eta_mass_distance_gev"])
    signal = np.asarray(cols["truth_matched"]) == 1
    # A true partially reconstructed Lb -> Lambda eta candidate must use the
    # signed, correctly mass-assigned Lambda daughters and an eta photon from
    # the same Lb. Merely having an eta photon is not sufficient.
    p_parent = np.asarray(cols["proton_mc_parent_index"])
    eta_chain = (
        (p_parent >= 0) & (p_parent == np.asarray(cols["pion_mc_parent_index"])) &
        (np.abs(np.asarray(cols["proton_mc_parent_pdg"])) == 3122) &
        (np.asarray(cols["mass_hypothesis_correct"]) == 1) &
        (np.abs(np.asarray(cols["photon_mc_parent_pdg"])) == 221) &
        (np.asarray(cols["proton_mc_grandparent_index"]) >= 0) &
        (np.asarray(cols["proton_mc_grandparent_index"]) ==
         np.asarray(cols["photon_mc_grandparent_index"])) &
        (np.abs(np.asarray(cols["proton_mc_grandparent_pdg"])) == 5122))
    entries = np.asarray(cols["original_event_entry"])
    selection = signal if category == "signal" else eta_chain if category == "eta" else np.ones(len(pi0), bool)
    out = {"candidates": int(selection.sum()),
           "events": int(np.unique(entries[selection]).size),
           "with_other_same_hemisphere_photon": int(np.count_nonzero(selection & (np.asarray(cols["n_other_same_hemisphere_photons"]) > 0))),
           "scan": []}
    for p_mev, e_mev in WINDOWS:
        veto = ((pi0 < p_mev / 1000) | (eta < e_mev / 1000))
        kept = selection & ~veto
        out["scan"].append({"pi0_half_window_mev": p_mev,
                            "eta_half_window_mev": e_mev,
                            "retained_candidates": int(kept.sum()),
                            "retained_events": int(np.unique(entries[kept]).size),
                            "candidate_retention": float(kept.sum() / selection.sum()) if selection.any() else None})
    return out


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--signal-edm", type=Path, required=True)
    parser.add_argument("--signal", type=Path, required=True)
    parser.add_argument("--eta-edm", type=Path, required=True)
    parser.add_argument("--eta", type=Path, required=True)
    parser.add_argument("--zbb-edm", type=Path, required=True)
    parser.add_argument("--zbb", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--lambda-half-window-mev", type=float, default=10)
    parser.add_argument("--zbb-events", type=int, default=1000,
                        help="Number of original Zbb entries processed; use a single-thread candidate snapshot")
    parser.add_argument("--zbb-match-by-photon", action="store_true",
                        help="Recover event identity from photon index and energy for an MT snapshot")
    parser.add_argument("--reuse-features", action="store_true",
                        help="Read previously written *_veto_features.parquet tables")
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    summary = {"lambda_half_window_mev": args.lambda_half_window_mev,
               "diphoton_masses_gev": MASSES, "samples": {}}
    for name, edm, parquet, limit, category in (
        ("signal", args.signal_edm, args.signal, 1000, "signal"),
        ("eta_as_gamma", args.eta_edm, args.eta, 1000, "eta"),
        ("zbb", args.zbb_edm, args.zbb, args.zbb_events, "zbb"),
    ):
        feature_path = args.output_dir / f"{name}_veto_features.parquet"
        if args.reuse_features:
            table = pq.read_table(feature_path)
        else:
            table = pq.read_table(parquet)
            dm = np.abs(table["lambda_mass"].to_numpy() - 1.115683) * 1000
            table = table.filter(pa.array(dm <= args.lambda_half_window_mev))
            print(f"{name}: {table.num_rows} mass-selected candidate rows", flush=True)
            table = add_distances(table, edm, limit,
                                  match_by_photon=name == "zbb" and args.zbb_match_by_photon)
            pq.write_table(table, feature_path, compression="zstd")
        summary["samples"][name] = category_counts(table, category)
        summary["samples"][name]["all_mass_selected_candidates"] = table.num_rows
    path = args.output_dir / "veto_scan.json"
    path.write_text(json.dumps(summary, indent=2) + "\n")
    plot_scan(summary, args.output_dir)
    print(json.dumps(summary, indent=2))


def plot_scan(summary, output_dir):
    """Show the retained candidate fractions for the tested veto settings."""
    os.environ.setdefault("MPLCONFIGDIR", str(Path(tempfile.gettempdir()) / "lblgamma-mplconfig"))
    os.environ.setdefault("XDG_CACHE_HOME", str(Path(tempfile.gettempdir()) / "lblgamma-cache"))
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import mplhep as hep

    plt.style.use(hep.style.LHCb2)
    plt.rcParams.update({"font.size": 11, "axes.labelsize": 12,
                         "axes.titlesize": 13, "legend.fontsize": 10,
                         "xtick.labelsize": 10, "ytick.labelsize": 10})
    fig, ax = plt.subplots(figsize=(11.5, 6.2))
    labels = [f"π0 ±{p} / η ±{e}" if p and e else
              f"π0 ±{p}" if p else f"η ±{e}" if e else "No veto"
              for p, e in WINDOWS]
    x = np.arange(len(WINDOWS))
    for name, label, marker in (("signal", "Truth matched signal", "o"),
                                ("eta_as_gamma", "η feed-down", "s"),
                                ("zbb", "Generic Zbb", "^")):
        y = [v["candidate_retention"] for v in summary["samples"][name]["scan"]]
        ax.plot(x, y, marker=marker, label=label)
    ax.set_xticks(x, labels, rotation=38, ha="right")
    ax.set(xlabel="Same-hemisphere diphoton veto half-windows [MeV]",
           ylabel="Fraction of candidates retained", ylim=(0, 1.05),
           title="Veto after ±10 MeV fitted Λ mass cut")
    ax.legend(frameon=False, loc="lower left")
    fig.tight_layout()
    fig.savefig(output_dir / "veto_retention.png", dpi=160)
    plt.close(fig)


if __name__ == "__main__":
    main()

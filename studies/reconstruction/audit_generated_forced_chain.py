#!/usr/bin/env python3
"""Count generated forced Lambda_b chains, independent of reconstruction."""

# Author: Renato Quagliani (rquaglia@cern.ch)

from __future__ import annotations

import argparse
from collections import Counter
import csv
import json
from pathlib import Path

import awkward as ak
import numpy as np
import uproot


def _four(px: float, py: float, pz: float, mass: float) -> np.ndarray:
    return np.array([np.sqrt(px * px + py * py + pz * pz + mass * mass),
                     px, py, pz], dtype=float)


def _boost(vector: np.ndarray, beta: np.ndarray) -> np.ndarray:
    beta2 = float(np.dot(beta, beta))
    gamma = 1.0 / np.sqrt(1.0 - beta2)
    dot = float(np.dot(beta, vector[1:]))
    spatial = vector[1:] + ((gamma - 1.0) * dot / beta2 + gamma * vector[0]) * beta
    return np.r_[gamma * (vector[0] + dot), spatial]


def audit(path: Path, mode: str, max_events: int | None = None,
          plot: Path | None = None, expected_alpha: float | None = None,
          angles_output: Path | None = None) -> dict:
    boson_pdg = {"gamma": 22, "eta": 221, "pi0": 111}[mode]
    # The default mmap source stalls on some AFS-hosted EDM4hep files here.
    with uproot.open(path, handler=uproot.source.file.MultithreadedFileSource) as root:
        tree = root["events"]
        total_events = tree.num_entries
        arrays = tree.arrays(
            ["Particle/Particle.PDG", "Particle/Particle.daughters_begin",
             "Particle/Particle.daughters_end", "Particle#1/Particle#1.index",
             "Particle/Particle.momentum.x", "Particle/Particle.momentum.y",
             "Particle/Particle.momentum.z", "Particle/Particle.mass"],
            entry_stop=max_events, library="ak",
        )
    counts = Counter()
    angles = []
    angle_rows = []
    for event in range(len(arrays["Particle/Particle.PDG"])):
        pdg = ak.to_list(arrays["Particle/Particle.PDG"][event])
        first = ak.to_list(arrays["Particle/Particle.daughters_begin"][event])
        last = ak.to_list(arrays["Particle/Particle.daughters_end"][event])
        indices = ak.to_list(arrays["Particle#1/Particle#1.index"][event])
        px, py, pz, mass = (
            ak.to_numpy(arrays[f"Particle/Particle.{field}"][event])
            for field in ("momentum.x", "momentum.y", "momentum.z", "mass")
        )

        def four(index: int) -> np.ndarray:
            return _four(px[index], py[index], pz[index], mass[index])

        def children(parent: int) -> list[int]:
            return [indices[i] for i in range(first[parent], last[parent])]

        complete_in_event = 0
        for parent, code in enumerate(pdg):
            if abs(code) != 5122:
                continue
            sign = 1 if code > 0 else -1
            counts["lambda_b_parents"] += 1
            daughters = children(parent)
            lambdas = [i for i in daughters if pdg[i] == sign * 3122]
            bosons = [i for i in daughters if pdg[i] == boson_pdg]
            for lam in lambdas:
                lambda_daughters = children(lam)
                protons = [i for i in lambda_daughters if pdg[i] == sign * 2212]
                pions = [i for i in lambda_daughters if pdg[i] == -sign * 211]
                if not protons or not pions:
                    continue
                for boson in bosons:
                    has_diphoton = mode == "gamma" or sum(
                        pdg[i] == 22 for i in children(boson)) == 2
                    if not has_diphoton:
                        continue
                    counts["complete_lambda_b" if sign > 0 else "complete_anti_lambda_b"] += 1
                    complete_in_event += 1
                    parent_four = four(parent)
                    lambda_four = four(lam)
                    proton_four = four(protons[0])
                    beta = -lambda_four[1:] / lambda_four[0]
                    parent_rest = _boost(parent_four, beta)[1:]
                    proton_rest = _boost(proton_four, beta)[1:]
                    denominator = np.linalg.norm(parent_rest) * np.linalg.norm(proton_rest)
                    if denominator > 0:
                        angle = float(np.clip(
                            -np.dot(parent_rest, proton_rest) / denominator, -1.0, 1.0))
                        angles.append(angle)
                        angle_rows.append((event, sign, angle))
        if complete_in_event:
            counts["events_with_complete_chain"] += 1
        if complete_in_event > 1:
            counts["events_with_multiple_complete_chains"] += 1
    processed = len(arrays["Particle/Particle.PDG"])
    if angles_output is not None:
        angles_output.parent.mkdir(parents=True, exist_ok=True)
        with angles_output.open("w", newline="") as handle:
            writer = csv.writer(handle)
            writer.writerow(("event_entry", "lb_sign", "generated_cos_theta_p"))
            writer.writerows(angle_rows)
    if plot is not None and angles:
        import matplotlib.pyplot as plt

        values = np.asarray(angles)
        bins = np.linspace(-1.0, 1.0, 11)
        hist_counts, edges = np.histogram(values, bins=bins)
        centers = (edges[:-1] + edges[1:]) / 2.0
        fig, ax = plt.subplots(figsize=(7.4, 5.2), layout="constrained")
        ax.errorbar(centers, hist_counts, yerr=np.sqrt(hist_counts), fmt="o", capsize=3,
                    color="#174a72", label="Generated complete chains")
        if expected_alpha is not None:
            alpha_lambda = (.906**2 - .423**2) / (.906**2 + .423**2)
            expected_slope = expected_alpha * alpha_lambda
            x = np.linspace(-1, 1, 200)
            expected = len(values) * (edges[1] - edges[0]) * (1 + expected_slope * x) / 2
            ax.plot(x, expected, color="#c65c28", linewidth=2,
                    label=f"HELAMP benchmark: αbαΛ = {expected_slope:+.3f}")
        channel = {"gamma": r"$\Lambda_b\to\Lambda\gamma$",
                   "eta": r"$\Lambda_b\to\Lambda\eta$",
                   "pi0": r"$\Lambda_b\to\Lambda\pi^0$"}[mode]
        ax.set(xlabel=r"Generated $\cos\theta_p$",
               ylabel="Complete generated chains / bin",
               title=f"{channel}: generated helicity angle")
        ax.text(.02, .98,
                f"{len(values)} direct decays; {counts['complete_lambda_b']} Λb, "
                f"{counts['complete_anti_lambda_b']} anti-Λb\n"
                f"Mean = {np.mean(values):+.3f} ± "
                f"{np.std(values, ddof=1) / np.sqrt(len(values)):.3f}",
                transform=ax.transAxes, va="top", fontsize=9,
                bbox={"facecolor": "white", "edgecolor": "#dddddd", "alpha": .9})
        ax.legend(loc="lower right", frameon=False)
        ax.grid(alpha=.18)
        plot.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(plot, dpi=180)
        plt.close(fig)
    return {
        "input": str(path),
        "mode": mode,
        "input_events": total_events,
        "processed_events": processed,
        "generated_direct_decays": counts["complete_lambda_b"] + counts["complete_anti_lambda_b"],
        "generated_lambda_b": counts["complete_lambda_b"],
        "generated_anti_lambda_b": counts["complete_anti_lambda_b"],
        "events_with_complete_chain": counts["events_with_complete_chain"],
        "events_with_multiple_complete_chains": counts["events_with_multiple_complete_chains"],
        "lambda_b_parents": counts["lambda_b_parents"],
        "generated_cos_theta_p_mean": float(np.mean(angles)) if angles else None,
        "generated_cos_theta_p_mean_se": (
            float(np.std(angles, ddof=1) / np.sqrt(len(angles))) if len(angles) > 1 else None
        ),
        "expected_parent_alpha": expected_alpha,
        "angle_definition": "(anti)proton versus negative Lambda_b momentum in Lambda rest frame",
        "definition": (
            "Direct Lambda_b/anti-Lambda_b -> Lambda0(p pi) + "
            + mode + ("(gamma gamma)" if mode in {"eta", "pi0"} else "")
            + "; both charges; MC truth only"
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--mode", choices=("gamma", "eta", "pi0"), required=True)
    parser.add_argument("--max-events", type=int)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--plot", type=Path, help="Optional generated-angle PNG")
    parser.add_argument("--expected-alpha", type=float,
                        help="Expected Lambda_b asymmetry for an optional plot curve")
    parser.add_argument("--angles-output", type=Path,
                        help="Optional per-decay generated angle CSV")
    args = parser.parse_args()
    if args.max_events is not None and args.max_events <= 0:
        parser.error("--max-events must be positive")
    if args.expected_alpha is not None and not -1 <= args.expected_alpha <= 1:
        parser.error("--expected-alpha must be between -1 and 1")
    result = audit(args.input, args.mode, args.max_events,
                   args.plot, args.expected_alpha, args.angles_output)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()

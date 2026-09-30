#!/usr/bin/env python3
"""Count selected signal and Eta-as-Gamma candidates in Λb mass intervals.

These are raw yields per generated sample. No branching fraction, Z→bb rate,
or sample-luminosity normalization is applied.
"""

import argparse
import json
import os
from pathlib import Path
import tempfile

os.environ.setdefault("MPLCONFIGDIR", str(Path(tempfile.gettempdir()) / "lblgamma-mplconfig"))
os.environ.setdefault("XDG_CACHE_HOME", str(Path(tempfile.gettempdir()) / "lblgamma-cache"))
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import mplhep as hep
import numpy as np

from compare_signal_eta_as_gamma import (
    ETA_ANCESTRY_COLUMNS, columns, true_partial_eta_mask)

plt.style.use(hep.style.LHCb2)


def count(values, event_ids, mask, low, high):
    selected = mask & (values >= low) & (values <= high)
    return {"candidates": int(np.count_nonzero(selected)),
            "events": int(np.unique(event_ids[selected]).size)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--signal", type=Path, required=True)
    parser.add_argument("--eta-as-gamma", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--generated-events", type=int, default=1000)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    signal = columns(args.signal,
                     ["lb_mass", "truth_matched", "event_entry"])
    eta = columns(args.eta_as_gamma,
                  ["lb_mass", "event_entry"] + ETA_ANCESTRY_COLUMNS)
    signal_truth = signal["truth_matched"] == 1
    eta_partial = true_partial_eta_mask(eta)
    if not np.any(signal_truth):
        raise ValueError("No truth-matched signal to locate the mass peak")
    center = float(np.median(signal["lb_mass"][signal_truth]))
    windows = [{"name": "fit_range", "low_gev": 4.9, "high_gev": 6.3}]
    for width in (0.2, 0.1, 0.05, 0.025):
        windows.append({"name": f"peak_pm_{int(width * 1000)}MeV",
                        "low_gev": center - width,
                        "high_gev": center + width})
    for window in windows:
        lo, hi = window["low_gev"], window["high_gev"]
        window["signal_truth"] = count(
            signal["lb_mass"], signal["event_entry"], signal_truth, lo, hi)
        window["signal_other"] = count(
            signal["lb_mass"], signal["event_entry"], ~signal_truth, lo, hi)
        window["eta_partial"] = count(
            eta["lb_mass"], eta["event_entry"], eta_partial, lo, hi)
        window["eta_other"] = count(
            eta["lb_mass"], eta["event_entry"], ~eta_partial, lo, hi)
        window["signal_efficiency_per_generated_event"] = (
            window["signal_truth"]["events"] / args.generated_events)

    edges = np.linspace(4.9, 6.3, 141)
    fig, ax = plt.subplots(figsize=(10, 6))
    for values, mask, label, color in (
        (signal["lb_mass"], signal_truth, "True Λb→Λ⁰γ", "C0"),
        (signal["lb_mass"], ~signal_truth, "Signal-sample other", "C2"),
        (eta["lb_mass"], eta_partial, "True partial Λb→Λ⁰η", "C1"),
        (eta["lb_mass"], ~eta_partial, "Eta-sample other", "C3"),
    ):
        ax.stairs(np.histogram(values[mask], edges)[0], edges,
                  label=label, color=color, linewidth=1.5)
    ax.axvspan(center - 0.05, center + 0.05, color="C0", alpha=0.10,
               label="Peak ±50 MeV")
    ax.set(xlabel=r"Fitted-vertex $m(p\pi\gamma)$ [GeV]",
           ylabel="Candidates / 10 MeV",
           title="Mass windows after vertex and thrust-hemisphere selection",
           xlim=(4.9, 6.3))
    ax.set_ylim(bottom=0)
    ax.grid(alpha=0.25)
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(args.output_dir / "lb_mass_window_scan.png", dpi=160)
    plt.close(fig)

    result = {
        "signal_file": str(args.signal),
        "eta_as_gamma_file": str(args.eta_as_gamma),
        "generated_events_per_sample": args.generated_events,
        "reference_peak_gev": center,
        "reference_peak_definition": "median truth-matched signal candidate mass in this diagnostic sample; windows are illustrative, not optimized",
        "windows": windows,
        "normalization": "Raw yields from separate forced-decay samples; no physical signal-to-background ratio or expected Z→bb yield",
    }
    (args.output_dir / "lb_mass_window_scan.json").write_text(
        json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Measure the thrust-hemisphere cut on pre-cut Lambda_b candidates.

Read the configured reconstruction with require_same_hemisphere=false, so
both accepted and rejected photon combinations remain available. Truth labels
are used only to report signal retention and combinatorial rejection.
"""

import argparse
import json
import os
from pathlib import Path
import tempfile

os.environ.setdefault("MPLCONFIGDIR", str(Path(tempfile.gettempdir()) / "lblgamma-mplconfig"))
os.environ.setdefault("XDG_CACHE_HOME", str(Path(tempfile.gettempdir()) / "lblgamma-cache"))
import awkward as ak
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import mplhep as hep
import numpy as np
import uproot

plt.style.use(hep.style.LHCb2)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--signal-label", default="Fully truth matched signal")
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    with uproot.open(str(args.input),
                     handler=uproot.source.file.MemmapSource) as root:
        tree = root["events"]
        arrays = tree.arrays(["lb_truth_matched", "lb_same_hemisphere",
                              "lb_lambda_thrust_cos", "lb_neutral_thrust_cos",
                              "event_entry"], library="ak")
    matched = ak.to_numpy(ak.flatten(arrays["lb_truth_matched"])) == 1
    same = ak.to_numpy(ak.flatten(arrays["lb_same_hemisphere"])) == 1
    lambda_cos = ak.to_numpy(ak.flatten(arrays["lb_lambda_thrust_cos"]))
    neutral_cos = ak.to_numpy(ak.flatten(arrays["lb_neutral_thrust_cos"]))
    if len(same) != len(matched):
        raise ValueError("Candidate-level truth and hemisphere fields differ in length")
    other = ~matched
    counts = {
        "candidates_before": int(len(same)),
        "candidates_after": int(np.count_nonzero(same)),
        "signal_before": int(np.count_nonzero(matched)),
        "signal_after": int(np.count_nonzero(matched & same)),
        "other_before": int(np.count_nonzero(other)),
        "other_after": int(np.count_nonzero(other & same)),
    }
    for kind in ("signal", "other"):
        denominator = counts[f"{kind}_before"]
        counts[f"{kind}_retention"] = (
            counts[f"{kind}_after"] / denominator if denominator else None)

    labels = [args.signal_label, "Other combinations"]
    before = [counts["signal_before"], counts["other_before"]]
    after = [counts["signal_after"], counts["other_after"]]
    x = np.arange(2)
    fig, ax = plt.subplots(figsize=(9, 5.6))
    ax.bar(x - 0.18, before, width=0.35, label="Before hemisphere cut")
    ax.bar(x + 0.18, after, width=0.35, label="Same hemisphere")
    ax.set(xticks=x, xticklabels=labels, ylabel="Candidates / 1,000 input events",
           title="Thrust hemisphere selection")
    ax.set_ylim(bottom=0)
    ax.legend(frameon=False)
    for i, (b, a) in enumerate(zip(before, after)):
        ax.text(i + 0.18, a, f"{a}/{b}", ha="center", va="bottom")
    fig.tight_layout()
    fig.savefig(args.output_dir / "thrust_hemisphere_yields.png", dpi=160)
    plt.close(fig)

    fig, axs = plt.subplots(1, 2, figsize=(11, 5.2), sharex=True, sharey=True)
    for ax, mask, title in zip(axs, (matched, other), labels):
        hist = ax.hist2d(lambda_cos[mask], neutral_cos[mask],
                         bins=[np.linspace(-1, 1, 51)] * 2, cmap="viridis")
        ax.axhline(0, color="white", linewidth=1)
        ax.axvline(0, color="white", linewidth=1)
        ax.set(xlabel=r"cos($\Lambda^0$, thrust)", title=title,
               xlim=(-1, 1), ylim=(-1, 1))
        fig.colorbar(hist[3], ax=ax, label="Candidates / bin")
    axs[0].set_ylabel(r"cos($\gamma$, thrust)")
    fig.tight_layout()
    fig.savefig(args.output_dir / "thrust_hemisphere_cosines.png", dpi=160)
    plt.close(fig)

    (args.output_dir / "thrust_hemisphere_summary.json").write_text(
        json.dumps(counts, indent=2) + "\n")
    print(json.dumps(counts, indent=2))


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Apply a reconstructed-mass preselection to a flattened candidate table.

Both selected and rejected rows retain all original columns, including truth
labels for later diagnostics. No truth quantity enters the selection.
"""

import argparse
import json
from pathlib import Path

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output-prefix", type=Path, required=True)
    parser.add_argument("--lambda-pdg", type=float, default=1.115683)
    parser.add_argument("--lambda-half-window-mev", type=float, default=15.)
    parser.add_argument("--lb-mass-min", type=float, default=4.5)
    parser.add_argument("--lb-mass-max", type=float, default=6.5)
    args = parser.parse_args()
    if not (0 < args.lambda_half_window_mev < 300 and
            0 < args.lb_mass_min < args.lb_mass_max):
        parser.error("Invalid mass window")
    table = pq.read_table(args.input)
    mass = table["lambda_mass"].to_numpy().astype(float)
    lbmass = table["lb_mass"].to_numpy().astype(float)
    lambda_pass = np.isfinite(mass) & (np.abs(mass-args.lambda_pdg) <
                                      args.lambda_half_window_mev/1000.)
    lb_pass = np.isfinite(lbmass) & (args.lb_mass_min <= lbmass) & (
        lbmass <= args.lb_mass_max)
    selected = lambda_pass & lb_pass
    args.output_prefix.parent.mkdir(parents=True, exist_ok=True)
    for suffix, mask in (("selected", selected), ("rejected", ~selected)):
        pq.write_table(table.filter(pa.array(mask)),
                       args.output_prefix.with_name(args.output_prefix.name +
                                                    f"_{suffix}.parquet"),
                       compression="zstd")
    summary = {
        "input": str(args.input), "input_candidate_rows": table.num_rows,
        "cut": {"lambda_pdg_gev": args.lambda_pdg,
                "lambda_half_window_mev": args.lambda_half_window_mev,
                "lb_mass_range_gev": [args.lb_mass_min, args.lb_mass_max]},
        "lambda_mass_pass": int(lambda_pass.sum()),
        "lb_mass_pass": int(lb_pass.sum()),
        "selected_candidates": int(selected.sum()),
        "rejected_candidates": int((~selected).sum()),
    }
    if "event_entry" in table.column_names:
        event = table["event_entry"].to_numpy()
        summary["candidate_bearing_events"] = int(np.unique(event).size)
        summary["selected_events"] = int(np.unique(event[selected]).size)
    if "truth_matched" in table.column_names:
        truth = table["truth_matched"].to_numpy() == 1
        summary["truth_matched_candidates"] = int(truth.sum())
        summary["selected_truth_matched_candidates"] = int((selected & truth).sum())
        summary["wrong_or_unmatched_candidates"] = int((~truth).sum())
        summary["selected_wrong_or_unmatched_candidates"] = int((selected & ~truth).sum())
    summary_path = args.output_prefix.with_name(args.output_prefix.name + "_summary.json")
    summary_path.write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()

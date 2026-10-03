#!/usr/bin/env python3
"""Validate v3 ROOT counters and candidate-vector lengths for one tuple."""

import argparse
import hashlib
import json
from pathlib import Path

import awkward as ak
import numpy as np
import uproot


REQUIRED = {
    "event_entry", "n_lb", "lb_mass", "lb_truth_matched", "lb_cos_theta_p",
    "lb_energy", "lb_sign", "iso_R20_all_n", "lambda0_iso_R20_all_n",
    "gamma_combo_same_hemi_all_mass", "arm_alpha", "arm_qt",
    "reco_mc_greatgreatgrandparent_pdg",
}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--input", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--max-output-events", type=int,
                    help="Bounded schema trial; omitted for complete validation")
    ap.add_argument("--all-vectors", action="store_true",
                    help="Also stream every lb/isolation candidate-vector branch")
    args = ap.parse_args()
    if args.max_output_events is not None and args.max_output_events <= 0:
        ap.error("--max-output-events must be positive")
    events = candidates = direct = 0
    with uproot.open(args.input) as root:
        processed = int(root["eventsProcessed"].value)
        selected = int(root["eventsSelected"].value)
        tree = root["events"]
        if selected != tree.num_entries or processed < selected:
            raise ValueError("ROOT counters disagree with the events tree")
        names = set(tree.keys())
        schema_sha256 = hashlib.sha256("\n".join(
            f"{name}:{tree[name].typename}" for name in sorted(names)
        ).encode()).hexdigest()
        missing = REQUIRED - names
        if missing:
            raise ValueError(f"Missing v3 branches: {sorted(missing)}")
        if args.all_vectors:
            vector_names = sorted(name for name in names
                                  if name.startswith(("lb_", "iso_", "lambda0_iso_")))
            vector_names += ["gamma_combo_same_hemi_all_mass", "arm_alpha", "arm_qt"]
        else:
            vector_names = sorted(REQUIRED - {"event_entry", "n_lb",
                                              "reco_mc_greatgreatgrandparent_pdg"})
        read_names = ["n_lb"] + vector_names
        stop = min(selected, args.max_output_events) if args.max_output_events else selected
        for block in tree.iterate(read_names, step_size=1500, entry_stop=stop,
                                  library="ak", how=dict):
            sizes = ak.to_numpy(block["n_lb"])
            for name in vector_names:
                if not np.array_equal(sizes, ak.to_numpy(ak.num(block[name]))):
                    raise ValueError(f"Candidate-vector length mismatch: {name}")
            events += len(sizes)
            candidates += int(sizes.sum())
            direct += int(ak.sum(ak.flatten(block["lb_truth_matched"])))
    result = {
        "stage1_scenario": "v3", "input": str(args.input),
        "root_bytes": args.input.stat().st_size,
        "processed_input_events": processed,
        "candidate_bearing_output_events": selected,
        "validated_output_events": events,
        "complete_validation": events == selected,
        "candidate_rows_validated": candidates,
        "direct_truth_matched_candidates_validated": direct,
        "checked_candidate_vector_branches": len(vector_names),
        "validation_scope": "all_candidate_vectors" if args.all_vectors
                            else "required_v3_vectors",
        "branch_schema_sha256": schema_sha256,
        "candidate_vector_lengths": "passed",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()

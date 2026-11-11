#!/usr/bin/env python3
"""Count true Lambda eta/pi0 partial chains inside the inclusive Zbb BDT set.

This truth-only composition audit does not alter the reconstructed veto cuts.
It tests whether forced-mode shape estimates overlap the inclusive component.
"""

import argparse
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path

import numpy as np
import pandas as pd

from study_v3_pseudoscalar_backgrounds import direct_partial


COLS = ("source_id", "event_entry", "candidate_slot", "lb_sign", "lb_mass",
        "truth_matched", "bdt_score", "arm_alpha", "arm_qt", "pass_pi0",
        "pass_eta", "proton_mc_parent_index", "pion_mc_parent_index",
        "proton_mc_parent_pdg", "pion_mc_parent_pdg",
        "proton_mc_grandparent_index", "pion_mc_grandparent_index",
        "proton_mc_grandparent_pdg", "pion_mc_grandparent_pdg",
        "photon_mc_parent_pdg", "photon_mc_grandparent_index",
        "photon_mc_grandparent_pdg")


def read_one(path, threshold):
    frame = pd.read_parquet(path, columns=list(COLS))
    return frame.loc[frame.bdt_score >= threshold].copy()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--scored-dir", type=Path, required=True)
    ap.add_argument("--catalog", type=Path, required=True)
    ap.add_argument("--projection", type=Path, required=True)
    ap.add_argument("--config", type=Path, default=Path("config/v3_post_bdt_veto_sequence.json"))
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--workers", type=int, default=12)
    args = ap.parse_args()
    catalog = json.loads(args.catalog.read_text())
    config = json.loads(args.config.read_text())
    projection = json.loads(args.projection.read_text())
    score = float(projection["validation_choice"]["score"])
    expected = {f"zbb_{item['chunk_id']}_selected.parquet" for item in catalog["chunks"]}
    paths = sorted(args.scored_dir.glob("zbb_*_selected.parquet"))
    if {path.name for path in paths} != expected:
        raise ValueError("Scored Zbb shards differ from frozen catalog")
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        frame = pd.concat(pool.map(lambda path: read_one(path, score), paths),
                          ignore_index=True)
    if frame.duplicated(["source_id", "event_entry", "candidate_slot"]).any():
        raise ValueError("Repeated post-BDT candidate key")
    box = config["armenteros_reject_box"]
    alpha = frame.arm_alpha.abs()
    rejected = (alpha.between(box["abs_alpha_min"], box["abs_alpha_max"]) &
                frame.arm_qt.between(box["qt_min_gev"], box["qt_max_gev"]))
    masks = {"post_bdt": np.ones(len(frame), dtype=bool),
             "post_bdt_armenteros": ~rejected}
    masks["post_bdt_armenteros_pi0"] = masks["post_bdt_armenteros"] & frame.pass_pi0
    masks["post_bdt_armenteros_pi0_eta"] = masks["post_bdt_armenteros_pi0"] & frame.pass_eta
    # The compact inclusive Parquet stores the candidate charge in int8;
    # promote before the PDG-id products used by direct_partial.
    frame["lb_sign"] = frame.lb_sign.astype("int32")
    eta = direct_partial(frame, 221)
    pi0 = direct_partial(frame, 111)
    direct = frame.truth_matched == 1
    if (eta & pi0).any() or (direct & (eta | pi0)).any():
        raise ValueError("Truth categories overlap")
    peak = frame.lb_mass.between(*config["mass_window_gev"])
    weight = config["N_Z"] * config["branching_fractions"]["Zbb"] / \
        catalog["total_processed_events_in_valid_chunks"]
    counts = {}
    for stage, selection in masks.items():
        counts[stage] = {}
        for label, category in (("direct_signal", direct), ("eta_direct_partial", eta),
                                ("pi0_direct_partial", pi0),
                                ("other_nonmatched", ~(direct | eta | pi0))):
            chosen = selection & category
            npeak = int((chosen & peak).sum())
            counts[stage][label] = {"candidate_rows": int(chosen.sum()),
                                    "peak_candidate_rows": npeak,
                                    "projected_peak_candidates_at_zbb_weight": npeak * weight}
    output = {"catalog": str(args.catalog), "scored_dir": str(args.scored_dir),
              "score_cut": score, "processed_input_events": catalog[
                  "total_processed_events_in_valid_chunks"],
              "candidate_weight": weight, "stages": counts,
              "scope": "Post-selection truth composition only; no truth field used by the BDT or vetoes"}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, indent=2) + "\n")
    print(json.dumps(counts, indent=2))


if __name__ == "__main__":
    main()

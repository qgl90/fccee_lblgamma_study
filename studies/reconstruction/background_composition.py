#!/usr/bin/env python3
"""Summarize MC ancestry of all flattened Lambda_b candidates, including fakes."""

import argparse
from collections import Counter
import json
from pathlib import Path

import numpy as np
import pyarrow.parquet as pq


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--mode", choices=("gamma", "eta"), required=True)
    args = parser.parse_args()
    table = pq.read_table(args.input)
    cache = {}

    def col(name):
        if name not in cache:
            cache[name] = table[name].to_numpy(zero_copy_only=False)
        return cache[name]

    sign = col("lb_sign")
    p = col("proton_mc_index")
    pi = col("pion_mc_index")
    g1 = col("photon_mc_index")
    g2 = col("photon2_mc_index")
    linked = (p >= 0) & (pi >= 0) & (g1 >= 0)
    if args.mode == "eta":
        linked &= g2 >= 0

    true_lambda = (
        (col("proton_mc_pdg") == sign * 2212) &
        (col("pion_mc_pdg") == -sign * 211) &
        (col("proton_mc_parent_index") >= 0) &
        (col("proton_mc_parent_index") == col("pion_mc_parent_index")) &
        (col("proton_mc_parent_pdg") == sign * 3122) &
        (col("proton_mc_grandparent_index") >= 0) &
        (col("proton_mc_grandparent_index") ==
         col("pion_mc_grandparent_index")) &
        (col("proton_mc_grandparent_pdg") == sign * 5122))
    if args.mode == "eta":
        true_neutral = (
            (col("photon_mc_pdg") == 22) &
            (col("photon2_mc_pdg") == 22) &
            (col("photon_mc_parent_index") >= 0) &
            (col("photon_mc_parent_index") ==
             col("photon2_mc_parent_index")) &
            (col("photon_mc_parent_pdg") == 221) &
            (col("photon_mc_grandparent_index") >= 0) &
            (col("photon_mc_grandparent_index") ==
             col("photon2_mc_grandparent_index")) &
            (np.abs(col("photon_mc_grandparent_pdg")) == 5122))
        neutral_lb = col("photon_mc_grandparent_index")
    else:
        true_neutral = ((col("photon_mc_pdg") == 22) &
                        (col("photon_mc_parent_index") >= 0) &
                        (np.abs(col("photon_mc_parent_pdg")) == 5122))
        neutral_lb = col("photon_mc_parent_index")
    same_lb = col("proton_mc_grandparent_index") == neutral_lb
    full = true_lambda & true_neutral & same_lb
    truth_flag = col("truth_matched") == 1
    if not np.array_equal(full, truth_flag):
        raise ValueError("Ancestry classification disagrees with C++ full truth label")

    categories = {
        "full_truth_match": full,
        "missing_or_ambiguous_mc_link": ~full & ~linked,
        "true_lambda_and_neutral_different_lb": ~full & linked &
            true_lambda & true_neutral,
        "true_lambda_only": ~full & linked & true_lambda & ~true_neutral,
        "true_neutral_only": ~full & linked & ~true_lambda & true_neutral,
        "other_linked_combinations": ~full & linked & ~true_lambda & ~true_neutral,
    }
    counts = {name: int(np.count_nonzero(mask))
              for name, mask in categories.items()}
    if sum(counts.values()) != len(table):
        raise ValueError("Background categories do not partition candidates")

    fake_linked = linked & ~full
    mother_pairs = Counter(zip(
        col("proton_mc_parent_pdg")[fake_linked].tolist(),
        col("pion_mc_parent_pdg")[fake_linked].tolist()))
    result = {
        "input": str(args.input), "mode": args.mode,
        "candidate_count": len(table), "categories": counts,
        "top_fake_proton_pion_mother_pdg_pairs": [
            {"proton_mother_pdg": pair[0], "pion_mother_pdg": pair[1],
             "candidates": count}
            for pair, count in mother_pairs.most_common(10)],
    }
    if args.mode == "eta":
        photon_mothers = Counter(zip(
            col("photon_mc_parent_pdg")[fake_linked].tolist(),
            col("photon2_mc_parent_pdg")[fake_linked].tolist()))
        result["top_fake_photon_mother_pdg_pairs"] = [
            {"photon1_mother_pdg": pair[0], "photon2_mother_pdg": pair[1],
             "candidates": count}
            for pair, count in photon_mothers.most_common(10)]
    else:
        photon_mothers = Counter(
            col("photon_mc_parent_pdg")[fake_linked].tolist())
        result["top_fake_photon_mother_pdgs"] = [
            {"photon_mother_pdg": pdg, "candidates": count}
            for pdg, count in photon_mothers.most_common(10)]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Compare v5 opposite-jet flavour scores in a bounded Zqq file pilot."""

import argparse
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score


CLASSES = ("zbb", "zcc", "zss")
TAGS = ("B", "C", "S")
ALL_TAGS = ("B", "C", "S", "Q", "G")
BRANCH = {
    tag: f"lb_flavtag_v5_recojet_is{tag}_flavtag_v5_otherjet_max"
    for tag in ALL_TAGS
}
REGION = "E(Lb) >= 10.5 GeV and |m(Lambda)-mPDG| <= 12.5 MeV"


def read_backgrounds(pilot_dir):
    frames = []
    for sample in CLASSES:
        paths = sorted(pilot_dir.glob(f"{sample}_*_1000_candidates.parquet"))
        if len(paths) != 6:
            raise ValueError(f"Expected 6 {sample} candidate tables; found {len(paths)}")
        for path in paths:
            frame = pd.read_parquet(path)
            frame["sample"] = sample
            frame["input_file"] = path.name.removesuffix("_1000_candidates.parquet")
            frames.append(frame)
    return pd.concat(frames, ignore_index=True)


def representative_per_event(frame):
    keys = ["source_id", "event_entry"]
    return (frame.sort_values(["lb_energy", "candidate_slot"],
                              ascending=[False, True])
            .drop_duplicates(keys, keep="first"))


def auc_or_none(labels, scores):
    labels = np.asarray(labels, dtype=int)
    scores = np.asarray(scores, dtype=float)
    if len(np.unique(labels)) < 2:
        return None
    return float(roc_auc_score(labels, scores))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pilot-dir", type=Path, required=True)
    parser.add_argument("--signal-parquet", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    background = read_backgrounds(args.pilot_dir)
    signal = pd.read_parquet(args.signal_parquet)
    signal = signal[signal["truth_matched"] == 1].copy()
    signal["sample"] = "signal_direct"
    signal["source_id"] = 0
    all_rows = pd.concat([background, signal], ignore_index=True)
    required = {"lb_energy", "lambda_slot_mass", "event_entry", "candidate_slot",
                "truth_matched", *BRANCH.values()}
    missing = sorted(required - set(all_rows.columns))
    if missing:
        raise ValueError(f"Missing v5 columns: {missing}")

    region = ((all_rows["lb_energy"] >= 10.5) &
              ((all_rows["lambda_slot_mass"] - 1.115683).abs() <= 0.0125))
    in_region = all_rows.loc[region].copy()
    invalid_scores = np.zeros(len(in_region), dtype=bool)
    for column in BRANCH.values():
        invalid_scores |= (~np.isfinite(in_region[column])) | (in_region[column] < 0)
    selected = in_region.loc[~invalid_scores].copy()

    event_frames = {}
    for sample in (*CLASSES, "signal_direct"):
        frame = selected[selected["sample"] == sample].copy()
        # Choose one candidate per event without using any flavour score.
        event_frames[sample] = representative_per_event(frame)

    rows = {}
    for sample in (*CLASSES, "signal_direct"):
        before = all_rows[all_rows["sample"] == sample]
        after = selected[selected["sample"] == sample]
        events = event_frames[sample]
        rows[sample] = {
            "input_events": 6000 if sample in CLASSES else None,
            "files": 6 if sample in CLASSES else 1,
            "candidate_rows_before_common_region": int(len(before)),
            "candidate_bearing_events_before_common_region": int(
                before[["source_id", "event_entry"]].drop_duplicates().shape[0]),
            "candidate_rows_in_common_region": int(len(after)),
            "candidate_rows_missing_or_invalid_any_flavour_score": int(
                sum((in_region["sample"] == sample) & invalid_scores)),
            "events_in_common_region": int(
                after[["source_id", "event_entry"]].drop_duplicates().shape[0]),
            "matched_signal_rows": int(after["truth_matched"].sum()),
            "score_medians_candidate_rows": {
                tag: float(after[BRANCH[tag]].median()) if len(after) else None
                for tag in TAGS},
            "score_10_90_percentile_candidate_rows": {
                tag: ([float(after[BRANCH[tag]].quantile(.1)),
                       float(after[BRANCH[tag]].quantile(.9))] if len(after) else None)
                for tag in TAGS},
        }

    # Ensure winner categories with zero entries are still explicit.
    for sample in (*CLASSES, "signal_direct"):
        counts = {tag: 0 for tag in TAGS}
        for _, row in event_frames[sample].iterrows():
            winner = TAGS[int(np.argmax([row[BRANCH[tag]] for tag in TAGS]))]
            counts[winner] += 1
        rows[sample]["other_jet_winner_by_event"] = counts

    # One row per event for class identification; use the model's B/C/S score
    # ordering on the candidate's opposite jet, without truth-based selection.
    confusion = {sample: {tag: 0 for tag in TAGS} for sample in CLASSES}
    for sample in CLASSES:
        for _, row in event_frames[sample].iterrows():
            winner = TAGS[int(np.argmax([row[BRANCH[tag]] for tag in TAGS]))]
            confusion[sample][winner] += 1

    pairwise_auc = {}
    comparisons = (
        ("zss", "zbb", "S"), ("zss", "zcc", "S"),
        ("zbb", "zss", "B"), ("zbb", "zcc", "B"),
        ("zcc", "zbb", "C"), ("zcc", "zss", "C"),
    )
    for positive, negative, tag in comparisons:
        pair = selected[selected["sample"].isin([positive, negative])].copy()
        labels = pair["sample"].eq(positive).astype(int)
        pairwise_auc[f"{positive}_vs_{negative}_using_otherjet_{tag}"] = {
            "positive_events": int(len(event_frames[positive])),
            "negative_events": int(len(event_frames[negative])),
            "candidate_row_auc": auc_or_none(
                labels, pair[BRANCH[tag]]),
            "event_row_auc": auc_or_none(
                event_frames[positive].assign(label=1)["label"].tolist() +
                event_frames[negative].assign(label=0)["label"].tolist(),
                event_frames[positive][BRANCH[tag]].tolist() +
                event_frames[negative][BRANCH[tag]].tolist()),
        }

    # Direct matched signal versus Zss: scan a simple other-jet b-score cut.
    signal_events = event_frames["signal_direct"]
    zss_events = event_frames["zss"]
    signal_vs_zss = {
        "signal_events": int(len(signal_events)),
        "zss_events": int(len(zss_events)),
        "otherjet_b_auc_signal_vs_zss": auc_or_none(
            [1] * len(signal_events) + [0] * len(zss_events),
            signal_events[BRANCH["B"]].tolist() + zss_events[BRANCH["B"]].tolist()),
        "otherjet_b_thresholds": {},
    }
    threshold_scan = {}
    for threshold in (0.8, 0.9, 0.95, 0.99):
        sig_eff = float((signal_events[BRANCH["B"]] >= threshold).mean()) if len(signal_events) else None
        zss_eff = float((zss_events[BRANCH["B"]] >= threshold).mean()) if len(zss_events) else None
        signal_vs_zss["otherjet_b_thresholds"][str(threshold)] = {
            "direct_signal_retention": sig_eff,
            "zss_retention": zss_eff,
            "zss_rejection": (1 - zss_eff) if zss_eff is not None else None,
        }
        threshold_scan[str(threshold)] = {}
        for sample in (*CLASSES, "signal_direct"):
            values = event_frames[sample][BRANCH["B"]]
            retained = int((values >= threshold).sum())
            total = int(len(values))
            threshold_scan[str(threshold)][sample] = {
                "retained_events": retained,
                "total_events": total,
                "retention": float(retained / total) if total else None,
            }

    summary = {
        "study": "v5 six-file Z flavour pilot",
        "selection_region": REGION,
        "input_events_per_background_sample": 6000,
        "events_per_file": 1000,
        "input_files": {
            sample: sorted(all_rows.loc[all_rows["sample"] == sample,
                                        "input_file"].dropna().unique().tolist())
            for sample in CLASSES},
        "candidate_selection": "v5 Stage 1 config lb_reco_v5_training.json, then common energy and fitted-Lambda mass region",
        "event_representative": "highest lb_energy candidate per event; tie broken by candidate_slot; no flavour score used",
        "candidate_rows_and_scores": rows,
        "event_level_otherjet_BCS_winner_counts": confusion,
        "pairwise_auc": pairwise_auc,
        "otherjet_b_threshold_scan_by_sample": threshold_scan,
        "direct_signal_vs_zss": signal_vs_zss,
        "limitations": [
            "Only the first 1,000 entries of each of six 100,000-event files were processed.",
            "The selected background candidate/event denominators are small; all score metrics are exploratory and unweighted.",
            "One candidate per event is chosen by highest reconstructed Lambda_b energy to avoid candidate multiplicity weighting.",
            "No physical Z flavour normalization or cross-section weighting is applied.",
            "The Weaver model uses a reconstructed PV and full event jets that still include the candidate daughters.",
        ],
    }
    (args.output_dir / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    pq_path = args.output_dir / "candidate_rows_common_region.parquet"
    selected.to_parquet(pq_path, index=False)

    fig, axes = plt.subplots(1, 3, figsize=(13, 4.2), sharey=True)
    colors = {"zbb": "#d95f02", "zcc": "#1b9e77", "zss": "#7570b3",
              "signal_direct": "#1f78b4"}
    labels = {"zbb": "Z→bb", "zcc": "Z→cc", "zss": "Z→ss",
              "signal_direct": "Direct signal"}
    bins = np.linspace(0, 1, 21)
    for ax, tag in zip(axes, TAGS):
        for sample in (*CLASSES, "signal_direct"):
            values = event_frames[sample][BRANCH[tag]].to_numpy(dtype=float)
            if len(values):
                ax.hist(values, bins=bins, density=True, histtype="step", lw=1.8,
                        color=colors[sample], label=f"{labels[sample]} (n={len(values)})")
        ax.set(xlabel=f"Other-jet {tag} score", xlim=(0, 1))
        ax.grid(alpha=.2)
    axes[0].set_ylabel("Density per unit score")
    axes[-1].legend(frameon=False, fontsize=8)
    fig.suptitle("v5 other-jet flavour scores | one candidate per selected event")
    fig.tight_layout()
    fig.savefig(args.output_dir / "otherjet_bcs_scores.png", dpi=170)
    plt.close(fig)

    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()

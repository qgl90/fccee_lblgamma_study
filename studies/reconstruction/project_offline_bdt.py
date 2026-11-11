#!/usr/bin/env python3
"""Freeze a validation score cut, evaluate it on test data, and scale yields.

The default normalization treats the 100k forced physics events as one
generated target decay per event. The output records candidate and event
rates separately; a candidate yield is used in S/sqrt(S+B). No inferred
background fit is introduced. The score objective is evaluated in a named
reconstructed Lambda_b signal-peak mass window.
"""

import argparse
import hashlib
import json
from pathlib import Path
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import v3_plot_style  # noqa: F401 - shared mplhep LHCb-style figures
import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from scipy.stats import chi2

from train_offline_bdt import split_signal, split_chunk_record


NZ = 6e12
BR_ZBB = .15
FLB = .10
BR_SIGNAL = 7.1e-6
BR_LAMBDA = .639
SIGNAL_FACTOR = NZ * BR_ZBB * 2 * FLB * BR_SIGNAL * BR_LAMBDA
BACKGROUND_FACTOR = NZ * BR_ZBB
SCORE_COLUMNS = ["source_id", "event_entry", "candidate_slot", "lb_mass",
                 "cos_theta_p", "truth_matched", "bdt_score"]


def count_events(frame):
    if frame.empty:
        return 0
    return int(frame[["source_id", "event_entry"]].drop_duplicates().shape[0])


def counts(frame, threshold, sample, mass_window=None):
    kept = frame[(frame.bdt_score >= threshold) &
                 ((frame.truth_matched == 1) if sample == "signal" else
                  (frame.truth_matched != 1))]
    if mass_window is not None:
        kept = kept.loc[kept.lb_mass.between(*mass_window)]
    return {"candidates": len(kept), "events": count_events(kept)}


def projection(signal, background, threshold, ngen, nbg, mass_window=None):
    s = counts(signal, threshold, "signal", mass_window)
    b = counts(background, threshold, "zbb", mass_window)
    expected_s = SIGNAL_FACTOR * s["candidates"] / ngen
    expected_b = BACKGROUND_FACTOR * b["candidates"] / nbg
    b_count = b["candidates"]
    b_low = 0.5 * chi2.ppf(.025, 2*b_count) if b_count else 0.
    b_high = 0.5 * chi2.ppf(.975, 2*(b_count+1))
    conservative_b = BACKGROUND_FACTOR * max(3, b["candidates"]) / nbg
    return {"score": float(threshold), "mass_window_gev": mass_window,
            "signal": s, "zbb": b,
            "signal_candidate_efficiency": s["candidates"] / ngen,
            "signal_event_efficiency": s["events"] / ngen,
            "zbb_candidate_rate_per_event": b["candidates"] / nbg,
            "zbb_event_efficiency": b["events"] / nbg,
            "expected_signal_candidates": expected_s,
            "expected_zbb_candidates": expected_b,
            "expected_purity_central": expected_s / (expected_s + expected_b)
                if expected_s + expected_b else None,
            "expected_purity_with_background_95pct_upper":
                expected_s / (expected_s + BACKGROUND_FACTOR*b_high/nbg)
                if expected_s + BACKGROUND_FACTOR*b_high/nbg else None,
            "expected_zbb_candidates_95pct_poisson_interval": [
                BACKGROUND_FACTOR*b_low/nbg, BACKGROUND_FACTOR*b_high/nbg],
            "expected_zbb_events": BACKGROUND_FACTOR * b["events"] / nbg,
            "significance_raw": expected_s / np.sqrt(expected_s+expected_b)
                if expected_s+expected_b else None,
            "zbb_three_count_upper_scale": conservative_b,
            "significance_with_three_count_background_floor":
                expected_s / np.sqrt(expected_s+conservative_b)}


def plot_expected_distributions(signal, background, threshold, ngen, nbg,
                                mass_range, peak_window, output):
    sig = signal[(signal.truth_matched == 1) & (signal.bdt_score >= threshold)]
    bg = background[(background.truth_matched != 1) &
                    (background.bdt_score >= threshold)]
    weight_s = SIGNAL_FACTOR / ngen
    weight_b = BACKGROUND_FACTOR / nbg
    peak_min, peak_max = peak_window
    panels = [
        ("lb_mass", np.linspace(mass_range[0], mass_range[1], 37),
         np.ones(len(sig), bool), np.ones(len(bg), bool),
         "Full analysis mass interval"),
        ("lb_mass", np.linspace(peak_min, peak_max, 26),
         np.ones(len(sig), bool), np.ones(len(bg), bool),
         f"Optimization peak interval, {peak_min:g}–{peak_max:g} GeV"),
        ("cos_theta_p", np.linspace(-1, 1, 21),
         np.ones(len(sig), bool), np.ones(len(bg), bool),
         "Helicity angle, full mass interval"),
        ("cos_theta_p", np.linspace(-1, 1, 21),
         sig.lb_mass.between(peak_min, peak_max).to_numpy(),
         bg.lb_mass.between(peak_min, peak_max).to_numpy(),
         "Helicity angle, optimization peak interval"),
    ]
    fig, axes = plt.subplots(2, 2, figsize=(13, 9))
    for ax, (variable, edges, sig_mask, bg_mask, title) in zip(axes.flat, panels):
        svalues = sig.loc[sig_mask, variable].to_numpy()
        bvalues = bg.loc[bg_mask, variable].to_numpy()
        shist, _ = np.histogram(svalues[np.isfinite(svalues)], edges)
        bhist, _ = np.histogram(bvalues[np.isfinite(bvalues)], edges)
        ax.stairs(shist*weight_s, edges, lw=2, color="#2c6db2",
                  label=f"Expected signal: {shist.sum()*weight_s:,.0f} ({shist.sum():,} MC)")
        ax.stairs(bhist*weight_b, edges, lw=2, color="#c44e52",
                  label=f"Expected Zbb: {bhist.sum()*weight_b:,.0f} ({bhist.sum():,} MC)")
        centers = (edges[:-1]+edges[1:])/2
        ax.errorbar(centers[bhist > 0], (bhist*weight_b)[bhist > 0],
                    yerr=(np.sqrt(bhist)*weight_b)[bhist > 0], fmt="none",
                    color="#c44e52", alpha=.6, capsize=2)
        ax.set(xlabel=r"$m(\Lambda\gamma)$ [GeV]" if variable == "lb_mass" else
               r"$\cos\theta_p$", ylabel="Expected candidates per bin",
               title=title, yscale="log")
        ax.grid(alpha=.2)
        ax.legend(frameon=False, fontsize=8)
    fig.suptitle(f"FCC-ee Z-pole projection | BDT score ≥ {threshold:.4f} | "
                 f"test: {ngen:,} signal events, {nbg:,} Zbb events\n"
                 "N(Z)=6×10¹², BR(Z→bb)=0.15; weighted MC candidates",
                 fontsize=14)
    fig.tight_layout(rect=(0, 0, 1, .92))
    fig.savefig(output, dpi=180)
    plt.close(fig)


def plot_working_point_scan(scan, choice, target, minimum_significance,
                            minimum_purity, mass_window, output):
    score = np.asarray([row["score"] for row in scan])
    s = np.asarray([row["expected_signal_candidates"] for row in scan])
    b = np.asarray([row["expected_zbb_candidates"] for row in scan])
    b_upper = np.asarray([row["expected_zbb_candidates_95pct_poisson_interval"][1]
                          for row in scan])
    significance = np.asarray([row["significance_raw"]
                               if row["zbb"]["candidates"] > 0 else np.nan
                               for row in scan],
                              dtype=float)
    conservative = s/np.sqrt(s+b_upper)
    fig, axes = plt.subplots(1, 3, figsize=(17, 4.8))
    axes[0].plot(score, s, color="#2c6db2", label="Expected signal")
    axes[0].plot(score, b, color="#c44e52", label="Expected Zbb")
    axes[0].plot(score, b_upper, color="#c44e52", ls="--", alpha=.7,
                 label="Zbb 95% interval upper edge")
    axes[0].axhline(target, color="0.35", ls=":", label=f"Zbb target: {target:,.0f}")
    axes[0].set(xlabel="BDT signal-score cut", ylabel="Expected candidates",
                yscale="log", title=f"Yields in {mass_window[0]:g}–{mass_window[1]:g} GeV")
    axes[0].legend(frameon=False, fontsize=8)
    axes[1].plot(score, significance, color="#283f74",
                 label="Central S/√(S+B), observed B>0")
    axes[1].plot(score, conservative, color="#283f74", ls="--",
                 label="Using background interval upper edge")
    axes[1].axhline(minimum_significance, color="0.35", ls=":",
                    label=f"Requested significance: {minimum_significance:g}")
    axes[1].set(xlabel="BDT signal-score cut", ylabel="Projected S/√(S+B)",
                title="Validation optimization")
    axes[1].legend(frameon=False, fontsize=8)
    axes[2].plot(score, [row["signal_candidate_efficiency"] for row in scan],
                 color="#2c6db2", label="Direct signal / generated event")
    axes[2].plot(score, [row["zbb_candidate_rate_per_event"] for row in scan],
                 color="#c44e52", label="Zbb candidates / processed event")
    axes[2].set(xlabel="BDT signal-score cut", ylabel="Rate per input event",
                yscale="log", title="Underlying MC rates")
    axes[2].legend(frameon=False, fontsize=8)
    if choice:
        for ax in axes:
            ax.axvline(choice["score"], color="forestgreen", ls="--", lw=1.5)
    for ax in axes:
        ax.grid(alpha=.2)
    fig.suptitle("Validation score scan | thresholds fixed before independent-test evaluation",
                 fontsize=14)
    fig.tight_layout(rect=(0, 0, 1, .93))
    fig.savefig(output, dpi=180)
    plt.close(fig)
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.5))
    axes[0].plot(score, b, color="#c44e52", label="Central expected Zbb")
    axes[0].plot(score, b_upper, color="#c44e52", ls="--",
                 label="95% interval upper edge")
    axes[0].axhline(target, color="0.35", ls=":", label="Target")
    axes[0].set(xlim=(.9, 1), yscale="log", xlabel="BDT signal-score cut",
                ylabel="Expected Zbb candidates", title="Rare-background tail")
    axes[1].plot(score, significance, color="#283f74", label="Central, observed B>0")
    axes[1].plot(score, conservative, color="#283f74", ls="--",
                 label="Using background interval upper edge")
    axes[1].axhline(minimum_significance, color="0.35", ls=":", label="Target")
    axes[1].set(xlim=(.9, 1), xlabel="BDT signal-score cut",
                ylabel="Projected S/√(S+B)", title="Significance near the tight cut")
    for ax in axes:
        if choice:
            ax.axvline(choice["score"], color="forestgreen", ls="--")
        ax.legend(frameon=False, fontsize=8)
        ax.grid(alpha=.2)
    fig.tight_layout()
    fig.savefig(output.with_name("working_point_tail.png"), dpi=180)
    plt.close(fig)
    purity = np.asarray([row["expected_purity_central"] for row in scan],
                        dtype=float)
    purity_upper = np.asarray([
        row["expected_purity_with_background_95pct_upper"] for row in scan],
        dtype=float)
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.5))
    for ax in axes:
        ax.plot(score, purity, color="#2c6db2", label="Central S/(S+B)")
        ax.plot(score, purity_upper, color="#c44e52", ls="--",
                label="Using background 95% upper edge")
        if minimum_purity:
            ax.axhline(minimum_purity, color="0.35", ls=":",
                       label=f"Purity target: {minimum_purity:.1%}")
        if choice:
            ax.axvline(choice["score"], color="forestgreen", ls="--")
        ax.set(xlabel="BDT signal-score cut", ylabel="Expected signal purity",
               ylim=(0, 1))
        ax.grid(alpha=.2)
        ax.legend(frameon=False, fontsize=8)
    axes[1].set(xlim=(.9, 1), title="Tight-score region")
    fig.tight_layout()
    fig.savefig(output.with_name("working_point_purity.png"), dpi=180)
    plt.close(fig)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--prepared-dir", type=Path, required=True)
    ap.add_argument("--model-dir", type=Path, required=True)
    ap.add_argument("--output-dir", type=Path, required=True)
    ap.add_argument("--min-validation-background", type=int, default=20)
    ap.add_argument("--max-expected-background", type=float, default=1_000_000,
                    help="Target upper 95%% expected Zbb candidates in the signal-peak window")
    ap.add_argument("--min-significance", type=float, default=10.,
                    help="Requested minimum S/sqrt(S+B) at the chosen point")
    ap.add_argument("--min-expected-purity", type=float, default=0.,
                    help="Optional minimum S/(S+B), using the 95%% upper background count")
    ap.add_argument("--signal-mass-window", nargs=2, type=float,
                    metavar=("LOW_GEV", "HIGH_GEV"), default=(5.4, 5.9),
                    help="Reconstructed Lambda_b peak window for S, B, score objective, and constraints")
    args = ap.parse_args()
    if args.max_expected_background <= 0 or args.min_significance <= 0:
        ap.error("Background target and significance target must be positive")
    if not 0 <= args.min_expected_purity < 1:
        ap.error("--min-expected-purity must be in [0, 1)")
    if args.min_validation_background < 1:
        ap.error("--min-validation-background must be positive")
    peak_window = [float(x) for x in args.signal_mass_window]
    if not peak_window[0] < peak_window[1]:
        ap.error("--signal-mass-window needs increasing bounds")
    training = json.loads((args.model_dir / "training_summary.json").read_text())
    prepared_manifest_path = args.model_dir / "prepared_manifest.json"
    prepared_manifest_bytes = prepared_manifest_path.read_bytes()
    prepared_manifest_sha256 = hashlib.sha256(prepared_manifest_bytes).hexdigest()
    if prepared_manifest_sha256 != training["prepared_manifest_sha256"]:
        raise ValueError("Frozen model preparation manifest has changed")
    prep = json.loads(prepared_manifest_bytes)
    if prep["max_output_events_per_file"] is not None:
        raise ValueError("Cannot project a pilot with unknown processed-event denominator")
    if training["scenario"] != prep["scenario"]:
        raise ValueError("Training/preparation scenario mismatch")
    full_range = prep.get("fit_mass_range_gev", [4.7, 6.5])
    if peak_window[0] < full_range[0] or peak_window[1] > full_range[1]:
        ap.error("Signal peak window must lie inside the prepared mass range")
    generated = prep["events_processed"]["signal"]
    if not generated or not prep["events_processed"]["zbb"]:
        raise ValueError("Missing generated/processed denominator")
    entries = np.arange(generated, dtype="uint64")
    generated_split = split_signal(entries)
    generated_counts = {part: int(np.count_nonzero(generated_split == part))
                        for part in ("train", "validation", "test")}
    signal = pq.read_table(args.model_dir / "scored_selected" /
                           "signal_-1_selected.parquet", columns=SCORE_COLUMNS).to_pandas()
    if len(signal) and int(signal.event_entry.max()) >= generated:
        raise ValueError("Signal event_entry exceeds generated event count")
    signal["split"] = split_signal(signal.event_entry.to_numpy())
    background = []
    background_denominators = {"train": 0, "validation": 0, "test": 0}
    for index, item in enumerate(prep["records"][1:]):
        part = split_chunk_record(item["source_id"], index, training)
        background_denominators[part] += item["events_processed"]
        path = args.model_dir / "scored_selected" / f"zbb_{item['source_id']}_selected.parquet"
        if path.exists():
            frame = pq.read_table(path, columns=SCORE_COLUMNS).to_pandas()
            frame["split"] = part
            background.append(frame)
    background = pd.concat(background, ignore_index=True)
    valid_s = signal[signal.split == "validation"]
    valid_b = background[background.split == "validation"]
    test_s = signal[signal.split == "test"]
    test_b = background[background.split == "test"]
    scores = valid_s.loc[(valid_s.truth_matched == 1) &
                         valid_s.lb_mass.between(*peak_window), "bdt_score"].to_numpy()
    if not len(scores):
        raise ValueError("Validation partition has no direct signal")
    bg_scores = valid_b.loc[(valid_b.truth_matched != 1) &
                            valid_b.lb_mass.between(*peak_window), "bdt_score"].to_numpy()
    if not len(bg_scores):
        raise ValueError("Validation peak window has no Zbb background candidates")
    # Resolve the tight tail by the actual background order statistics as
    # well as a dense numeric grid. Cuts immediately above a score account
    # for the >= convention and score ties without test-set tuning.
    sorted_bg = np.sort(bg_scores)
    tail_counts = np.arange(args.min_validation_background,
                            min(len(sorted_bg), 500) + 1)
    tail_scores = sorted_bg[-tail_counts] if len(tail_counts) else np.array([])
    grid = np.unique(np.r_[np.linspace(0, 1, 401),
        1 - np.geomspace(1e-7, 0.1, 160),
        np.quantile(scores, np.r_[np.linspace(0, .99, 100),
                                  np.linspace(.99, .9999, 50),
                                  np.linspace(.9999, 1, 40)]),
        np.quantile(bg_scores, np.linspace(.9, .9999, 50)),
        tail_scores, np.nextafter(tail_scores, 1.)])
    grid = grid[np.isfinite(grid) & (grid >= 0) & (grid <= 1)]
    validation = [projection(valid_s, valid_b, cut, generated_counts["validation"],
                             background_denominators["validation"], peak_window) for cut in grid]
    eligible = [item for item in validation if
                item["zbb"]["candidates"] >= args.min_validation_background and
                item["signal"]["candidates"] > 0]
    # The unconstrained optimum is diagnostic. The adopted candidate must
    # pass the background and optional purity constraints on validation.
    unconstrained = max(eligible, key=lambda x: x["significance_raw"]) if eligible else None
    target_eligible = [item for item in validation
                       if item["signal"]["candidates"] > 0 and
                       item["zbb"]["candidates"] >= args.min_validation_background and
                       item["significance_raw"] >= args.min_significance and
                       item["expected_zbb_candidates_95pct_poisson_interval"][1]
                       <= args.max_expected_background and
                       item["expected_purity_with_background_95pct_upper"]
                       >= args.min_expected_purity]
    target_choice = max(target_eligible, key=lambda x: x["significance_raw"]) \
                    if target_eligible else None
    chosen = target_choice
    test = projection(test_s, test_b, chosen["score"], generated_counts["test"],
                      background_denominators["test"], peak_window) if chosen else None
    full_test = projection(test_s, test_b, chosen["score"], generated_counts["test"],
                           background_denominators["test"]) if chosen else None
    stage_signal = prep["stage_counts"]["signal"]
    stage_zbb = prep["stage_counts"]["zbb"]
    signal_generated_all = prep["events_processed"]["signal"]
    zbb_processed_all = prep["events_processed"]["zbb"]
    signal_test_before_bdt = counts(test_s, 0., "signal")["candidates"]
    zbb_test_before_bdt = counts(test_b, 0., "zbb")["candidates"]
    efficiency_chain = {
        "signal": {
            "stage0_forced_decays_per_generated_event_assumed": 1.0,
            "stage1_direct_candidates_per_generated_event_all":
                stage_signal["stage1"]["direct_candidates"] / signal_generated_all,
            "offline_direct_candidates_per_generated_event_all":
                stage_signal["selected"]["direct_candidates"] / signal_generated_all,
            "offline_conditional_on_stage1_direct_candidates_all":
                stage_signal["selected"]["direct_candidates"] /
                stage_signal["stage1"]["direct_candidates"]
                if stage_signal["stage1"]["direct_candidates"] else None,
            "bdt_conditional_on_offline_direct_candidates_test_full_mass":
                full_test["signal"]["candidates"] / signal_test_before_bdt
                if full_test and signal_test_before_bdt else None,
            "full_stage0_to_bdt_direct_candidates_per_generated_event_test":
                full_test["signal_candidate_efficiency"] if full_test else None,
            "peak_stage0_to_bdt_direct_candidates_per_generated_event_test":
                test["signal_candidate_efficiency"] if test else None,
        },
        "zbb": {
            "stage1_other_candidates_per_processed_event_all":
                stage_zbb["stage1"]["background_candidates"] / zbb_processed_all,
            "offline_other_candidates_per_processed_event_all":
                stage_zbb["selected"]["background_candidates"] / zbb_processed_all,
            "offline_conditional_on_stage1_other_candidates_all":
                stage_zbb["selected"]["background_candidates"] /
                stage_zbb["stage1"]["background_candidates"]
                if stage_zbb["stage1"]["background_candidates"] else None,
            "bdt_conditional_on_offline_other_candidates_test_full_mass":
                full_test["zbb"]["candidates"] / zbb_test_before_bdt
                if full_test and zbb_test_before_bdt else None,
            "full_stage1_to_bdt_other_candidates_per_processed_event_test":
                full_test["zbb_candidate_rate_per_event"] if full_test else None,
            "peak_stage1_to_bdt_other_candidates_per_processed_event_test":
                test["zbb_candidate_rate_per_event"] if test else None,
        },
        "note": "Stage 1/offline rates use all inputs; BDT conditional and final rates use the independent test split. Do not multiply mixed-split rates to reconstruct the test result."
    }
    args.output_dir.mkdir(parents=True, exist_ok=True)
    if chosen:
        signal_rows = test_s[(test_s.truth_matched == 1) &
                             (test_s.bdt_score >= chosen["score"])].copy()
        bg_rows = test_b[(test_b.truth_matched != 1) &
                         (test_b.bdt_score >= chosen["score"])].copy()
        signal_rows["expected_weight"] = SIGNAL_FACTOR / generated_counts["test"]
        bg_rows["expected_weight"] = BACKGROUND_FACTOR / background_denominators["test"]
        signal_rows["expected_component"] = "signal"
        bg_rows["expected_component"] = "zbb"
        signal_rows["inside_optimization_mass_window"] = signal_rows.lb_mass.between(*peak_window)
        bg_rows["inside_optimization_mass_window"] = bg_rows.lb_mass.between(*peak_window)
        pq.write_table(pa.Table.from_pandas(pd.concat([signal_rows, bg_rows],
                                             ignore_index=True), preserve_index=False),
                       args.output_dir / "expected_test_candidates.parquet",
                       compression="zstd")
        plot_expected_distributions(test_s, test_b, chosen["score"],
                                    generated_counts["test"],
                                    background_denominators["test"],
                                    full_range, peak_window,
                                    args.output_dir / "expected_mass_and_angle.png")
    summary = {
        "command": sys.argv,
        "projection_script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "prepared_manifest_sha256": prepared_manifest_sha256,
        "training_summary_sha256": hashlib.sha256(
            (args.model_dir / "training_summary.json").read_bytes()).hexdigest(),
        "model_sha256": hashlib.sha256(
            (args.model_dir / "bdt_model.json").read_bytes()).hexdigest(),
        "prepared_manifest": str(prepared_manifest_path),
        "training_summary": str(args.model_dir / "training_summary.json"),
        "scenario": prep["scenario"],
        "mass_range_gev": prep.get("fit_mass_range_gev", [4.7, 6.5]),
        "optimization_mass_window_gev": peak_window,
        "optimization_objective": "maximize expected S/sqrt(S+B) with both S and B in the reconstructed signal-peak mass window",
        "normalization": {"N_Z": NZ, "BR_Zbb": BR_ZBB, "f_Lambdab": FLB,
                          "BR_Lambdab_to_Lambda_gamma": BR_SIGNAL,
                          "BR_Lambda_to_p_pi": BR_LAMBDA,
                          "signal_factor": SIGNAL_FACTOR,
                          "zbb_factor": BACKGROUND_FACTOR,
                          "signal_formula": "N_Z * BR_Zbb * 2 * f_Lambdab * BR_Lambdab_to_Lambda_gamma * BR_Lambda_to_p_pi * direct_candidates / generated_signal_events",
                          "zbb_formula": "N_Z * BR_Zbb * other_zbb_candidates / processed_zbb_events"},
        "stage_counts_all_splits": prep["stage_counts"],
        "efficiency_chain": efficiency_chain,
        "stage0_direct_decay_assumption": "one forced direct decay per generated Physics input event; verify against generation audit",
        "signal_generated_events_by_split": generated_counts,
        "zbb_processed_events_by_split": background_denominators,
        "validation_scan": validation, "min_validation_background":
            args.min_validation_background,
        "max_expected_background_target": args.max_expected_background,
        "min_expected_purity_target": args.min_expected_purity,
        "min_significance_target": args.min_significance,
        "score_scan": "uniform plus logarithmic tail, signal/background quantiles, and exact high-background score order statistics",
        "score_grid_size": len(grid),
        "unconstrained_validation_choice": unconstrained,
        "background_target_validation_choice": target_choice,
        "validation_choice": chosen,
        "independent_test": full_test,
        "independent_test_optimization_peak": test,
        "independent_test_meets_background_target_at_95pct_upper":
            bool(test["expected_zbb_candidates_95pct_poisson_interval"][1]
                 <= args.max_expected_background) if test else None,
        "validation_meets_background_target_at_95pct_upper":
            bool(chosen["expected_zbb_candidates_95pct_poisson_interval"][1]
                 <= args.max_expected_background) if chosen else None,
        "validation_meets_significance_target":
            bool(chosen["significance_raw"] >= args.min_significance) if chosen else None,
        "independent_test_meets_significance_target":
            bool(test["significance_raw"] >= args.min_significance) if test else None,
        "expected_dataset": str(args.output_dir / "expected_test_candidates.parquet")
            if chosen else None,
        "statistical_limit": "A zero or sparse Zbb tail is unresolved; three counts is an approximate 95% Poisson upper scale, not a measured background",
        "normalization_limit": "One forced signal decay is assumed per generated physics event; verify generator truth and charge counts. Feed-down and other physical backgrounds are omitted."
    }
    (args.output_dir / "projection.json").write_text(json.dumps(summary, indent=2) + "\n")
    plot_working_point_scan(validation, chosen, args.max_expected_background,
                            args.min_significance, args.min_expected_purity,
                            peak_window,
                            args.output_dir / "working_point_scan.png")
    fig, ax = plt.subplots(figsize=(7, 5))
    ax.plot([x["signal_candidate_efficiency"] for x in validation],
            [x["expected_zbb_candidates"] for x in validation], ".-")
    ax.set(xlabel="Validation direct-candidate efficiency / generated event",
           ylabel=f"Expected Zbb candidates in {peak_window[0]:g}–{peak_window[1]:g} GeV", yscale="log")
    fig.tight_layout()
    fig.savefig(args.output_dir / "signal_vs_background.png", dpi=160)
    plt.close(fig)
    if chosen:
        for variable, edges, filename in (
                ("lb_mass", np.linspace(4.7, 6.5, 55), "mass_before_after_bdt.png"),
                ("cos_theta_p", np.linspace(-1, 1, 41), "angle_before_after_bdt.png")):
            fig, axes = plt.subplots(1, 2, figsize=(11, 4.4))
            for ax, frame, label, truth in ((axes[0], test_s, "Direct physics signal", 1),
                                            (axes[1], test_b, "Inclusive Zbb other", 0)):
                base = frame[frame.truth_matched == truth]
                for title, group in (("Before score", base),
                                     ("After score", base[base.bdt_score >= chosen["score"]])):
                    vals = group[variable].to_numpy()
                    hist_counts, _ = np.histogram(vals[np.isfinite(vals)], edges)
                    ax.stairs(hist_counts/max(1, hist_counts.sum()), edges,
                              label=f"{title} ({len(group)})")
                ax.set(xlabel=variable, ylabel="Fraction per bin", title=label)
                ax.legend()
            fig.tight_layout()
            fig.savefig(args.output_dir / filename, dpi=160)
            plt.close(fig)
    print(json.dumps({"validation_choice": chosen,
                      "independent_test_optimization_peak": test,
                      "independent_test_full_mass": full_test}, indent=2))


if __name__ == "__main__":
    main()

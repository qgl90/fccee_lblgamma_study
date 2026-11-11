#!/usr/bin/env python3
"""Stream native stage-1 ROOT files into auditable offline and BDT tables.

Selections operate on jagged reconstructed branches before conversion to a
candidate table. Truth is copied only to label/report the resulting rows.
The saved audit contains *all* stage-1 candidates, including failed cuts.
Use a frozen Condor catalog: its chunk IDs and eventsProcessed counters define
the background denominator and the source-disjoint training split.
"""

# Author: Renato Quagliani (rquaglia@cern.ch)

import argparse
from collections import Counter, defaultdict
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time

os.environ.setdefault("MPLCONFIGDIR", str(Path(tempfile.gettempdir()) / "lblgamma-mplconfig"))
os.environ.setdefault("XDG_CACHE_HOME", str(Path(tempfile.gettempdir()) / "lblgamma-cache"))
import awkward as ak
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq
import uproot


BRANCHES = [
    "event_entry", "n_lb", "lb_mass", "lb_lambda_mass", "lb_truth_matched",
    "lb_lambda_slot", "lb_sign", "lb_cos_theta_p",
    "gamma_combo_other_gamma_mass", "lb_proton_px", "lb_proton_py",
    "lb_proton_pz", "lb_pion_px", "lb_pion_py", "lb_pion_pz",
    "lb_photon_px", "lb_photon_py", "lb_photon_pz", "lb_photon_energy",
    "lb_lambda_px", "lb_lambda_py", "lb_lambda_pz", "lambda_energy",
    "lb_proton_energy", "lb_pion_energy", "lb_energy",
    "lb_px", "lb_py", "lb_pz", "lambda_proton_d0sig",
    "lambda_pion_d0sig", "lambda_d0_sig", "lambda_flight_rxy",
    "lambda_flight_rxy_sig", "lambda_vertex_chi2", "iso_R03_noLambda",
    "iso_R05_noLambda", "m_rec", "Estar_gamma_rec", "E_same",
    "deltaE", "lb_lambda_thrust_cos", "lb_neutral_thrust_cos",
]
PAIR_BRANCHES = {
    "all_raw_type22": "gamma_combo_other_gamma_mass",
    "same_hemi_all": "gamma_combo_same_hemi_all_mass",
    "same_hemi_selected": "gamma_combo_same_hemi_selected_mass",
}
PAIR_LIST_BRANCHES = (
    "gamma_combo_other_gamma_mass", "gamma_combo_other_gamma_index",
    "gamma_combo_same_hemi_all_mass", "gamma_combo_same_hemi_all_index",
    "gamma_combo_same_hemi_selected_mass",
    "gamma_combo_same_hemi_selected_index",
)
LAMBDA_BRANCHES = {"lambda_energy", "lambda_proton_d0sig", "lambda_pion_d0sig",
                   "lambda_d0_sig", "lambda_flight_rxy", "lambda_flight_rxy_sig",
                   "lambda_vertex_chi2"}
OPTIONAL_LAMBDA_BRANCHES = ("lambda_flight_xyz", "lambda_flight_xyz_sigma",
                            "lambda_flight_xyz_sig", "lambda_vertex_x", "lambda_vertex_y",
                            "lambda_vertex_z", "lambda_vertex_valid")
EXTRAS = {"proton_d0sig": "lambda_proton_d0sig",
          "pion_d0sig": "lambda_pion_d0sig", "lambda_d0_sig": "lambda_d0_sig",
          "lambda_flight_rxy": "lambda_flight_rxy",
          "lambda_flight_rxy_sig": "lambda_flight_rxy_sig",
          "lambda_vertex_chi2": "lambda_vertex_chi2",
          "iso_R03_noLambda": "iso_R03_noLambda",
          "iso_R05_noLambda": "iso_R05_noLambda", "m_rec": "m_rec",
          "Estar_gamma_rec": "Estar_gamma_rec", "E_same": "E_same",
          "deltaE": "deltaE", "lambda_thrust_cos": "lb_lambda_thrust_cos",
          "gamma_thrust_cos": "lb_neutral_thrust_cos"}
PRESERVE_BRANCHES = (
    "arm_alpha", "arm_qt", "lb_thrust_cos",
    "lb_flavtag_v5_recojet_isG_flavtag_v5_associated",
    "lb_flavtag_v5_recojet_isG_flavtag_v5_otherjet_max",
    "lb_flavtag_v5_recojet_isQ_flavtag_v5_associated",
    "lb_flavtag_v5_recojet_isQ_flavtag_v5_otherjet_max",
    "lb_flavtag_v5_recojet_isB_flavtag_v5_associated",
    "lb_flavtag_v5_recojet_isS_flavtag_v5_associated",
    "lb_flavtag_v5_recojet_isC_flavtag_v5_associated",
    "lb_flavtag_v5_recojet_isB_flavtag_v5_otherjet_max",
    "lb_flavtag_v5_recojet_isS_flavtag_v5_otherjet_max",
    "lb_flavtag_v5_recojet_isC_flavtag_v5_otherjet_max",
    "opp_hemi_px", "opp_hemi_py", "opp_hemi_pz", "opp_hemi_p",
    "opp_hemi_energy", "opp_hemi_n", "z_partial_deltaE", "z_partial_px",
    "z_partial_py", "z_partial_pz", "z_partial_deltaP",
    "z_full_deltaE", "z_full_px", "z_full_py", "z_full_pz", "z_full_deltaP",
) + tuple(
    f"{center}_{cone}_{kind}_{metric}"
    for center in ("iso", "lambda0_iso")
    for cone in ("R02", "R03", "R05", "R07", "R10", "R20", "R70")
    for kind in ("all", "charged", "neutral")
    for metric in ("px", "py", "pz", "p", "energy", "n")) + tuple(
    f"{center}_{cone}_charged_{metric}"
    for center in ("iso", "lambda0_iso")
    for cone in ("R02", "R03", "R05", "R07", "R10", "R20", "R70")
    for metric in ("d0_min", "d0_max", "absd0_min", "absd0_max", "n_d0"))
# Preserve v4 diagnostics through selection/scoring; never add to BDT features.
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "analysis/studies"))
from photon_pointing_stage1 import BRANCHES as POINTING_BRANCHES
PRESERVE_BRANCHES += POINTING_BRANCHES + tuple(
    "lb_photon_" + x for x in ("px", "py", "pz", "energy")) + tuple(
    "lb_lambda_" + x for x in ("px", "py", "pz"))

ANCESTRY_BRANCHES = (
    "reco_mc_index", "reco_mc_pdg", "reco_mc_n_parents",
    "reco_mc_parent_index", "reco_mc_parent_pdg",
    "reco_mc_grandparent_index", "reco_mc_grandparent_pdg",
    "reco_mc_greatgrandparent_index", "reco_mc_greatgrandparent_pdg",
    "reco_mc_greatgreatgrandparent_index", "reco_mc_greatgreatgrandparent_pdg",
)
ANCESTRY_LEGS = ("proton", "pion", "photon")
CUT_BRANCHES = {**EXTRAS, "lb_E": "lb_energy", **{name: name for name in
                             PRESERVE_BRANCHES + OPTIONAL_LAMBDA_BRANCHES}}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def preparation_identity(args, catalog):
    """Fields that must stay fixed while a catalog gains completed chunks."""
    return {
        "signal": str(args.signal.resolve()),
        "signal_bytes": args.signal.stat().st_size,
        "sample_name": catalog["sample_name"],
        "job_dir": str(Path(catalog["job_dir"]).resolve()),
        "root_dir": str(Path(catalog["root_dir"]).resolve()),
        "config_sha256": digest(args.config),
        "stage1_config_sha256": digest(args.stage1_config),
        "preparation_script_sha256": digest(Path(__file__)),
        "scenario": args.scenario,
        "max_output_events_per_file": args.max_output_events,
    }


def check_resume_directory(output_dir, identity, chunks, resume):
    """Never reuse old Parquets for a changed cut, code, or ROOT source."""
    identity_path = output_dir / "preparation_identity.json"
    old_tables = list(output_dir.glob("*_selected.parquet")) + list(
        output_dir.glob("*_audit.parquet"))
    if old_tables and not resume:
        raise ValueError("Output directory already has candidate Parquets; pass --resume "
                         "to reuse them or choose a fresh output directory")
    if identity_path.exists():
        previous = json.loads(identity_path.read_text())
        if previous != identity:
            changed = sorted(k for k in identity if previous.get(k) != identity[k])
            raise ValueError(f"Cannot resume with changed preparation identity: {changed}")
    elif old_tables:
        raise ValueError("Existing candidate Parquets have no preparation_identity.json; "
                         "use a fresh output directory to avoid mixing scenarios")
    old_summary = output_dir / "summary.json"
    if old_summary.exists():
        previous = json.loads(old_summary.read_text())
        current = {item["chunk_id"]: item for item in chunks}
        for record in previous["records"][1:]:
            source_id = record["source_id"]
            if source_id not in current:
                raise ValueError(f"Previously prepared chunk {source_id} is absent from new catalog")
            item = current[source_id]
            if str(item["root"]) != record["path"] or \
                    int(item["events_processed"]) != record["events_processed"] or \
                    (record.get("root_bytes") is not None and
                     int(item["root_bytes"]) != record["root_bytes"]):
                raise ValueError(f"Previously prepared chunk {source_id} changed in new catalog")
    if not identity_path.exists():
        temporary = identity_path.with_suffix(".json.tmp")
        temporary.write_text(json.dumps(identity, indent=2) + "\n")
        temporary.replace(identity_path)


def revision(path):
    try:
        return subprocess.check_output(["git", "-C", str(path), "rev-parse", "HEAD"],
                                       text=True).strip()
    except (OSError, subprocess.CalledProcessError):
        return None


def validate_config(cfg, scenario):
    if scenario not in cfg["scenarios"]:
        raise ValueError(f"Unknown scenario {scenario}; choose from {list(cfg['scenarios'])}")
    for name, item in cfg["scenarios"].items():
        if item["veto"] not in {"none", "pi0", "pi0_eta", "low_mass"}:
            raise ValueError(f"Invalid veto in {name}")
        if item.get("partner_definition", "all_raw_type22") not in PAIR_BRANCHES:
            raise ValueError(f"Invalid photon partner definition in {name}")
        if not 0 < item["lambda_half_window_mev"] <= 15:
            raise ValueError(f"{name}: native stage 1 already applied +/-15 MeV")
        if item["veto"] == "low_mass" and not 0 < item.get(
                "diphoton_min_gev", cfg["low_diphoton_mass_max_gev"]) <= 5:
            raise ValueError(f"{name}: invalid diphoton mass threshold")
        for cut in item.get("reco_cuts", []):
            if cut.get("column") not in CUT_BRANCHES or not ({"min", "max"} & cut.keys()):
                raise ValueError(f"{name}: reco_cuts need a saved reconstructed column and min/max")
            if "min" in cut and "max" in cut and cut["min"] > cut["max"]:
                raise ValueError(f"{name}: invalid reco_cuts interval")
    lo, hi = cfg["lb_mass_range_gev"]
    if not 4.5 <= lo < hi <= 6.5:
        raise ValueError("Fit range must be within the stage-1 saved range")


def flat(value):
    return np.asarray(ak.to_numpy(ak.flatten(value, axis=1)))


def pair_distances(pairs, cfg):
    valid = ak.where(np.isfinite(pairs) & (pairs >= 0), pairs, np.inf)
    def nearest(reference):
        return ak.fill_none(ak.min(abs(valid-reference), axis=-1), np.inf)
    return nearest(cfg["pi0_mass_gev"]), nearest(cfg["eta_mass_gev"]), \
        ak.fill_none(ak.min(valid, axis=-1), np.inf)


def selections(block, cfg, scenario):
    mass = block["lb_mass"]
    lm = block["lb_lambda_mass"]
    definition = cfg["scenarios"][scenario].get("partner_definition", "all_raw_type22")
    d_pi0, d_eta, min_pair = pair_distances(block[PAIR_BRANCHES[definition]], cfg)
    lo, hi = cfg["lb_mass_range_gev"]
    fit = np.isfinite(mass) & (mass >= lo) & (mass <= hi)
    window = cfg["scenarios"][scenario]["lambda_half_window_mev"] / 1000.
    lam = np.isfinite(lm) & (abs(lm-cfg["lambda_reference_gev"]) <= window)
    pi0 = d_pi0 > cfg["pi0_half_window_mev"] / 1000.
    eta = d_eta > cfg["eta_half_window_mev"] / 1000.
    low = min_pair >= cfg["low_diphoton_mass_max_gev"]
    veto = cfg["scenarios"][scenario]["veto"]
    low_scenario = min_pair >= cfg["scenarios"][scenario].get(
        "diphoton_min_gev", cfg["low_diphoton_mass_max_gev"])
    passed_veto = {"none": ak.ones_like(mass, dtype=np.bool_), "pi0": pi0,
                   "pi0_eta": pi0 & eta, "low_mass": low_scenario}[veto]
    for cut in cfg["scenarios"][scenario].get("reco_cuts", []):
        branch = CUT_BRANCHES[cut["column"]]
        if branch not in block.fields:
            raise ValueError(f"Stage-1 tuple lacks reconstructed cut branch {branch}")
        values = (block[branch][block["lb_lambda_slot"]]
                  if branch in LAMBDA_BRANCHES or branch in OPTIONAL_LAMBDA_BRANCHES
                  else block[branch])
        passed = np.isfinite(values) & (values > -998.)
        if "min" in cut:
            passed = passed & (values >= cut["min"])
        if "max" in cut:
            passed = passed & (values <= cut["max"])
        passed_veto = passed_veto & passed
    return {"stage1": ak.ones_like(mass, dtype=np.bool_), "fit": fit,
            "lambda": fit & lam, "selected": fit & lam & passed_veto,
            "pass_pi0": pi0, "pass_eta": eta, "pass_low_mass": low,
            "d_pi0": d_pi0, "d_eta": d_eta, "min_pair": min_pair}


def particle(rows, block, label, prefix, selected, energy=None):
    x = flat(block[f"{prefix}_px"][selected]).astype("float32")
    y = flat(block[f"{prefix}_py"][selected]).astype("float32")
    z = flat(block[f"{prefix}_pz"][selected]).astype("float32")
    pt = np.hypot(x, y)
    rows[f"{label}_p"] = np.sqrt(x*x + y*y + z*z)
    rows[f"{label}_pt"] = pt
    rows[f"{label}_eta"] = np.arcsinh(np.divide(
        z, pt, out=np.full_like(z, np.nan), where=pt > 0))
    if energy is not None:
        rows[f"{label}_E"] = flat(energy[selected]).astype("float32")


def rows_for(block, source_id, sample, flags, selected):
    mass = block["lb_mass"]
    event, _ = ak.broadcast_arrays(block["event_entry"], mass)
    multiplicity, _ = ak.broadcast_arrays(block["n_lb"], mass)
    rows = {
        "sample": np.repeat(sample, int(ak.sum(ak.sum(selected, axis=1)))),
        "source_id": np.full(int(ak.sum(ak.sum(selected, axis=1))), source_id, dtype="int32"),
        "event_entry": flat(event[selected]).astype("int64"),
        "candidate_slot": flat(ak.local_index(mass)[selected]).astype("int32"),
        "candidates_in_event": flat(multiplicity[selected]).astype("int32"),
        "lb_mass": flat(mass[selected]).astype("float32"),
        "lambda_mass": flat(block["lb_lambda_mass"][selected]).astype("float32"),
        "truth_matched": flat(block["lb_truth_matched"][selected]).astype("int8"),
        "lb_sign": flat(block["lb_sign"][selected]).astype("int8"),
        "cos_theta_p": flat(block["lb_cos_theta_p"][selected]).astype("float32"),
    }
    for key in ("fit", "lambda", "selected", "pass_pi0", "pass_eta", "pass_low_mass"):
        column = key if key.startswith("pass_") else f"pass_{key}"
        rows[column] = flat(flags[key][selected]).astype("bool")
    for key in ("d_pi0", "d_eta", "min_pair"):
        rows[key] = flat(flags[key][selected]).astype("float32")
    slots = block["lb_lambda_slot"]
    for output, branch in EXTRAS.items():
        values = block[branch][slots] if branch in LAMBDA_BRANCHES else block[branch]
        rows[output] = flat(values[selected]).astype("float32")
    for name in PRESERVE_BRANCHES:
        if name in block.fields:
            dtype = "int32" if name.endswith(("_n", "_n_d0")) else "float32"
            if name in POINTING_BRANCHES:
                dtype = "float64"
            rows[name] = flat(block[name][selected]).astype(dtype)
    for name in OPTIONAL_LAMBDA_BRANCHES:
        if name in block.fields:
            rows[name] = flat(block[name][slots][selected]).astype("float32")
    # Truth labels are copied for later inspection, never used by selections
    # or the BDT. Older Stage 1 files get explicit missing-generation values.
    for leg in ANCESTRY_LEGS:
        reco_index = block[f"lb_{leg}_index"][selected]
        rows[f"{leg}_reco_index"] = flat(reco_index).astype("int32")
        for branch in ANCESTRY_BRANCHES:
            column = f"{leg}_{branch.removeprefix('reco_')}"
            rows[column] = (flat(block[branch][reco_index]).astype("int32")
                            if branch in block.fields else
                            np.full(len(rows["lb_mass"]),
                                    0 if branch.endswith("_pdg") else -1,
                                    dtype="int32"))
    for name in PAIR_LIST_BRANCHES:
        if name in block.fields:
            values = ak.to_list(ak.flatten(block[name][selected], axis=1))
            item_type = pa.int32() if name.endswith("_index") else pa.float32()
            rows[name] = pa.array(values, type=pa.list_(item_type))
    for label, prefix, energy in (
            ("proton", "lb_proton", block["lb_proton_energy"]),
            ("pion", "lb_pion", block["lb_pion_energy"]),
            ("gamma", "lb_photon", block["lb_photon_energy"]),
            ("lambda", "lb_lambda", block["lambda_energy"][slots]),
            ("lb", "lb", block["lb_energy"])):
        particle(rows, block, label, prefix, selected, energy)
    photon_energy = rows["gamma_E"].astype(np.float32)
    valid_photon = np.isfinite(photon_energy) & (photon_energy > 0)
    for center in ("iso", "lambda0_iso"):
        for cone in ("R02", "R03", "R05", "R07", "R10", "R20"):
            for kind in ("all", "charged", "neutral"):
                source = f"{center}_{cone}_{kind}_energy"
                if source not in rows:
                    continue
                rows[f"{source}_over_gamma_E"] = np.divide(
                    rows[source], photon_energy,
                    out=np.full(len(photon_energy), np.nan, dtype=np.float32),
                    where=valid_photon).astype(np.float32)
    if "lb_thrust_cos" in rows:
        thrust_cos = rows["lb_thrust_cos"]
        rows["lb_thrust_abs_cos"] = np.where(
            np.isfinite(thrust_cos) & (thrust_cos > -998.),
            np.abs(thrust_cos), np.nan).astype(np.float32)
    return pa.table(rows)


class Writer:
    def __init__(self, path):
        self.path = path
        self.writer = None

    def write(self, table):
        if table.num_rows == 0:
            return
        if self.writer is None:
            self.writer = pq.ParquetWriter(self.path, table.schema, compression="zstd")
        self.writer.write_table(table)

    def close(self):
        if self.writer is not None:
            self.writer.close()


def count_stage(stats, stage, mask, truth, sample):
    count = int(ak.sum(ak.sum(mask, axis=1)))
    events = int(ak.sum(ak.any(mask, axis=1)))
    item = stats[stage]
    item["candidates"] += count
    item["events"] += events
    if sample == "signal":
        direct = mask & (truth == 1)
        item["direct_candidates"] += int(ak.sum(ak.sum(direct, axis=1)))
        item["direct_events"] += int(ak.sum(ak.any(direct, axis=1)))
        item["wrong_candidates"] += count - int(ak.sum(ak.sum(direct, axis=1)))
    else:
        direct = mask & (truth == 1)
        item["direct_in_zbb_candidates"] += int(ak.sum(ak.sum(direct, axis=1)))
        item["background_candidates"] += count - int(ak.sum(ak.sum(direct, axis=1)))


def process_file(path, sample, source_id, cfg, scenario, output_dir, max_output_events, scan):
    audit = Writer(output_dir / f"{sample}_{source_id}_audit.parquet")
    selected_writer = Writer(output_dir / f"{sample}_{source_id}_selected.parquet")
    stages = defaultdict(Counter)
    multiplicity = Counter()
    plots = {name: np.zeros(60, dtype=np.int64) for name in
             ("direct", "wrong", "zbb")}
    seen_events = set()
    with uproot.open(path, handler=uproot.source.file.MemmapSource) as root:
        tree = root["events"]
        definition = cfg["scenarios"][scenario].get("partner_definition", "all_raw_type22")
        pair_branch = PAIR_BRANCHES[definition]
        if pair_branch not in tree.keys():
            raise ValueError(f"{path} lacks {pair_branch}; rerun stage-1 reconstruction "
                             f"to use the {definition} veto")
        read_branches = BRANCHES + ([pair_branch] if pair_branch not in BRANCHES else [])
        read_branches += [name for name in PRESERVE_BRANCHES if name in tree.keys()]
        read_branches += [name for name in OPTIONAL_LAMBDA_BRANCHES if name in tree.keys()]
        read_branches += [name for name in PAIR_LIST_BRANCHES
                          if name in tree.keys() and name not in read_branches]
        read_branches += [f"lb_{leg}_index" for leg in ANCESTRY_LEGS]
        read_branches += [name for name in ANCESTRY_BRANCHES if name in tree.keys()]
        total_rows = int(tree.num_entries)
        stop = min(total_rows, max_output_events) if max_output_events else total_rows
        processed = int(root["eventsProcessed"].value)
        if "eventsSelected" in root and int(root["eventsSelected"].value) != total_rows:
            raise ValueError(f"eventsSelected mismatch in {path}")
        if stop != total_rows:
            processed = None  # filtered ROOT rows cannot recover the pilot input denominator
        for block in tree.iterate(read_branches, entry_stop=stop, step_size=2000,
                                  library="ak"):
            ids = np.asarray(ak.to_numpy(block["event_entry"]), dtype=np.int64)
            if len(np.unique(ids)) != len(ids) or any(int(i) in seen_events for i in ids):
                raise ValueError(f"Duplicate event_entry in {path}")
            if np.any(ids < 0) or np.any(ids >= int(root["eventsProcessed"].value)):
                raise ValueError(f"event_entry outside processed range in {path}")
            seen_events.update(int(i) for i in ids)
            if not np.array_equal(np.asarray(ak.to_numpy(ak.num(block["lb_mass"]))),
                                  np.asarray(ak.to_numpy(block["n_lb"]))):
                raise ValueError(f"n_lb does not match candidate vector length in {path}")
            flags = selections(block, cfg, scenario)
            truth = block["lb_truth_matched"]
            for stage in ("stage1", "fit", "lambda", "selected"):
                count_stage(stages, stage, flags[stage], truth, sample)
            n_selected = np.asarray(ak.to_numpy(ak.sum(flags["selected"], axis=1)))
            multiplicity.update(int(x) for x in n_selected if x)
            lam_delta = abs(block["lb_lambda_mass"]-cfg["lambda_reference_gev"])*1000.
            for width in cfg["lambda_scan_half_windows_mev"]:
                mask = flags["fit"] & (lam_delta <= width)
                count_stage(scan[str(width)][sample], "after_lambda", mask, truth, sample)
            masses = flat(block["lb_lambda_mass"])
            labels = flat(truth) == 1
            for name, use in (("direct", labels if sample == "signal" else np.zeros(len(labels), bool)),
                              ("wrong", ~labels if sample == "signal" else np.zeros(len(labels), bool)),
                              ("zbb", ~labels if sample == "zbb" else np.zeros(len(labels), bool))):
                plots[name] += np.histogram((masses[use]-cfg["lambda_reference_gev"])*1000,
                                            bins=np.linspace(-15, 15, 61))[0]
            audit.write(rows_for(block, source_id, sample, flags, flags["stage1"]))
            selected_writer.write(rows_for(block, source_id, sample, flags, flags["selected"]))
    audit.close()
    selected_writer.close()
    return {"path": str(path), "source_id": source_id,
            "root_bytes": path.stat().st_size,
            "root_output_events": total_rows, "read_output_events": stop,
            "events_processed": processed,
            "preserved_optional_branches": [name for name in PRESERVE_BRANCHES+
                                            OPTIONAL_LAMBDA_BRANCHES
                                            if name in tree.keys()],
            "preserved_ancestry_branches": [name for name in ANCESTRY_BRANCHES
                                             if name in tree.keys()],
            "preserved_pair_list_branches": [name for name in PAIR_LIST_BRANCHES
                                             if name in tree.keys()],
            "stages": {k: dict(v) for k, v in stages.items()},
            "selected_event_multiplicity": dict(sorted(multiplicity.items())),
            "plots": {k: v.tolist() for k, v in plots.items()}}


def recover_file(path, sample, source_id, cfg, output_dir, scan):
    """Rebuild counters from a complete audit/selected pair after interruption."""
    audit_path = output_dir / f"{sample}_{source_id}_audit.parquet"
    selected_path = output_dir / f"{sample}_{source_id}_selected.parquet"
    if not audit_path.exists() or not selected_path.exists():
        return None
    try:
        audit_meta = pq.read_metadata(audit_path)
        selected_meta = pq.read_metadata(selected_path)
        if audit_meta.num_rows <= 0 or selected_meta.num_rows <= 0:
            return None
        columns = ["event_entry", "lb_mass", "lambda_mass", "truth_matched",
                   "pass_fit", "pass_lambda", "pass_selected"]
        table = pq.read_table(audit_path, columns=columns)
        selected = pq.read_table(selected_path, columns=["event_entry"])
        if len(table) != audit_meta.num_rows or len(selected) != selected_meta.num_rows:
            return None
        flags = table["pass_selected"].to_numpy(zero_copy_only=False)
        if int(np.sum(flags)) != selected_meta.num_rows:
            return None
    except (OSError, ValueError, pa.ArrowException):
        return None
    events = table["event_entry"].to_numpy(zero_copy_only=False)
    masses = table["lambda_mass"].to_numpy(zero_copy_only=False)
    truth = table["truth_matched"].to_numpy(zero_copy_only=False) == 1
    def count(mask):
        ids = events[mask]
        item = {"candidates": int(np.sum(mask)), "events": int(len(np.unique(ids)))}
        direct = mask & truth
        if sample == "signal":
            item.update(direct_candidates=int(np.sum(direct)),
                        direct_events=int(len(np.unique(events[direct]))),
                        wrong_candidates=int(np.sum(mask & ~truth)))
        else:
            item.update(direct_in_zbb_candidates=int(np.sum(direct)),
                        background_candidates=int(np.sum(mask & ~truth)))
        return item
    stages = {name: count(np.ones(len(events), bool) if name == "stage1" else
                          table[f"pass_{name}"].to_numpy(zero_copy_only=False))
              for name in ("stage1", "fit", "lambda", "selected")}
    fit = table["pass_fit"].to_numpy(zero_copy_only=False)
    for width in cfg["lambda_scan_half_windows_mev"]:
        mask = fit & (abs(masses-cfg["lambda_reference_gev"])*1000. <= width)
        scan[str(width)][sample]["after_lambda"].update(count(mask))
    plot_bins = np.linspace(-15, 15, 61)
    plots = {name: np.zeros(60, dtype=np.int64) for name in ("direct", "wrong", "zbb")}
    for name, mask in (("direct", truth if sample == "signal" else np.zeros(len(truth), bool)),
                       ("wrong", ~truth if sample == "signal" else np.zeros(len(truth), bool)),
                       ("zbb", ~truth if sample == "zbb" else np.zeros(len(truth), bool))):
        plots[name] = np.histogram((masses[mask]-cfg["lambda_reference_gev"])*1000.,
                                   bins=plot_bins)[0]
    selected_ids = events[flags]
    _, multiplicities = np.unique(selected_ids, return_counts=True)
    multiplicity = Counter(int(x) for x in multiplicities)
    with uproot.open(path) as root:
        processed = int(root["eventsProcessed"].value)
        output_events = int(root["events"].num_entries)
    if output_events != len(np.unique(events)):
        raise ValueError(f"Recovered {path} has incomplete audit event coverage")
    fields = set(audit_meta.schema.names)
    return {"path": str(path), "source_id": source_id,
            "root_bytes": path.stat().st_size,
            "root_output_events": output_events, "read_output_events": output_events,
            "events_processed": processed,
            "preserved_optional_branches": [n for n in PRESERVE_BRANCHES+OPTIONAL_LAMBDA_BRANCHES
                                             if n in fields],
            "preserved_ancestry_branches": [n for n in ANCESTRY_BRANCHES if n in fields],
            "preserved_pair_list_branches": [n for n in PAIR_LIST_BRANCHES if n in fields],
            "stages": stages, "selected_event_multiplicity": dict(sorted(multiplicity.items())),
            "plots": {k: v.tolist() for k, v in plots.items()}, "recovered_from_parquet": True}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--signal", type=Path, required=True)
    ap.add_argument("--zbb-catalog", type=Path, required=True)
    ap.add_argument("--config", type=Path, default=Path("config/lb_offline_selections.json"))
    ap.add_argument("--stage1-config", type=Path,
                    default=Path("config/lb_reco_preselection_15mev_45_65.json"),
                    help="Named reconstruction scenario that produced both ROOT inputs")
    ap.add_argument("--scenario", help="Named offline selection; defaults to the config's default_prebdt_scenario")
    ap.add_argument("--output-dir", type=Path, required=True)
    ap.add_argument("--max-zbb-chunks", type=int)
    ap.add_argument("--max-output-events", type=int,
                    help="Pilot cap per ROOT file; input-event efficiencies then unavailable")
    ap.add_argument("--resume", action="store_true",
                    help="Validate complete Parquet pairs and recover their counters")
    args = ap.parse_args()
    cfg = json.loads(args.config.read_text())
    if args.scenario is None:
        args.scenario = cfg["default_prebdt_scenario"]
    validate_config(cfg, args.scenario)
    catalog = json.loads(args.zbb_catalog.read_text())
    chunks = catalog["chunks"][:args.max_zbb_chunks]
    if not chunks or len({x["chunk_id"] for x in chunks}) != len(chunks):
        raise ValueError("Catalog needs distinct chunk IDs")
    args.output_dir.mkdir(parents=True, exist_ok=True)
    identity = preparation_identity(args, catalog)
    check_resume_directory(args.output_dir, identity, chunks, args.resume)
    scan = defaultdict(lambda: defaultdict(lambda: defaultdict(Counter)))
    def make_record(path, sample, source_id):
        local_scan = defaultdict(lambda: defaultdict(lambda: defaultdict(Counter)))
        if args.resume and args.max_output_events is None:
            cached = recover_file(path, sample, source_id, cfg, args.output_dir, local_scan)
            if cached is not None:
                for width, samples in local_scan.items():
                    for label, stages in samples.items():
                        for stage, values in stages.items():
                            scan[width][label][stage].update(values)
                return cached
        for attempt in range(3):
            local_scan = defaultdict(lambda: defaultdict(lambda: defaultdict(Counter)))
            try:
                record = process_file(path, sample, source_id, cfg, args.scenario,
                                      args.output_dir, args.max_output_events, local_scan)
                for width, samples in local_scan.items():
                    for label, stages in samples.items():
                        for stage, values in stages.items():
                            scan[width][label][stage].update(values)
                return record
            except OSError:
                if attempt == 2:
                    raise
                print(f"I/O error on {sample} {source_id}; retry {attempt+1}/2", flush=True)
                time.sleep(2)
    records = [make_record(args.signal, "signal", -1)]
    for i, item in enumerate(chunks, 1):
        record = make_record(Path(item["root"]), "zbb", item["chunk_id"])
        if record["events_processed"] is not None and \
                record["events_processed"] != item["events_processed"]:
            raise ValueError(f"Catalog denominator changed for chunk {item['chunk_id']}")
        if record["root_bytes"] != item["root_bytes"]:
            raise ValueError(f"Catalog ROOT size changed for chunk {item['chunk_id']}")
        records.append(record)
        if i % 25 == 0 or i == len(chunks):
            print(f"Prepared {i}/{len(chunks)} Zbb chunks", flush=True)
    summary = {
        "signal": str(args.signal), "zbb_catalog": str(args.zbb_catalog),
        "zbb_catalog_sha256": digest(args.zbb_catalog),
        "zbb_chunk_ids": [x["chunk_id"] for x in chunks],
        "config": str(args.config), "config_sha256": digest(args.config),
        "stage1_config": str(args.stage1_config),
        "stage1_config_sha256": digest(args.stage1_config),
        "repository_revision": revision(Path.cwd()),
        "fccanalyses_revision": revision(Path("external/FCCAnalyses")),
        "preparation_script_sha256": digest(Path(__file__)),
        "command": sys.argv,
        "scenario": args.scenario, "scenario_definition": cfg["scenarios"][args.scenario],
        "fit_mass_range_gev": cfg["lb_mass_range_gev"],
        "max_output_events_per_file": args.max_output_events,
        "records": records,
        "lambda_scan": {width: {sample: {stage: dict(counts) for stage, counts in stages.items()}
                                for sample, stages in samples.items()}
                        for width, samples in scan.items()},
        "pair_definition": cfg["scenarios"][args.scenario].get(
            "partner_definition", "all_raw_type22"),
        "pair_rule": "candidate photon against each eligible partner; empty pair list passes",
        "training_labels": "truth_matched=1 signal positive; truth_matched=0 Zbb negative; signal wrong combinations and true Zbb decays diagnostic only",
        "note": "Stage 1 applied +/-15 MeV Lambda window and filtered n_lb>0 before these ROOT files were written"
    }
    for sample in ("signal", "zbb"):
        own = [r for r in records if (r["source_id"] == -1) == (sample == "signal")]
        values = [r["events_processed"] for r in own]
        summary.setdefault("events_processed", {})[sample] = sum(values) if all(
            x is not None for x in values) else None
        summary.setdefault("stage_counts", {})[sample] = {
            stage: dict(sum((Counter(r["stages"].get(stage, {})) for r in own), Counter()))
            for stage in ("stage1", "fit", "lambda", "selected")}
        first = summary["stage_counts"][sample]["stage1"]
        previous = first
        for stage in ("stage1", "fit", "lambda", "selected"):
            item = summary["stage_counts"][sample][stage]
            for quantity in ("candidates", "events"):
                item[f"conditional_{quantity}_retention"] = (
                    item[quantity] / previous[quantity] if previous[quantity] else None)
                item[f"cumulative_{quantity}_retention"] = (
                    item[quantity] / first[quantity] if first[quantity] else None)
            if summary["events_processed"][sample]:
                denom = summary["events_processed"][sample]
                item["event_efficiency_per_processed_event"] = item["events"] / denom
                item["candidate_rate_per_processed_event"] = item["candidates"] / denom
                if sample == "signal":
                    item["direct_candidate_rate_per_generated_event"] = (
                        item["direct_candidates"] / denom)
            previous = item
    (args.output_dir / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    bins = np.linspace(-15, 15, 61)
    fig, ax = plt.subplots(figsize=(8, 5))
    for key, label in (("direct", "Physics direct"), ("wrong", "Physics wrong"),
                       ("zbb", "Inclusive Zbb other")):
        counts = sum((np.asarray(r["plots"][key]) for r in records), np.zeros(60))
        if counts.sum():
            ax.stairs(counts/counts.sum(), bins, label=label)
    ax.set(xlabel=r"$m(p\pi)-m(\Lambda^0)$ [MeV]", ylabel="Fraction per 0.5 MeV")
    ax.legend()
    fig.tight_layout()
    fig.savefig(args.output_dir / "lambda_mass.png", dpi=160)
    plt.close(fig)
    fig, ax = plt.subplots(figsize=(7, 5))
    widths = cfg["lambda_scan_half_windows_mev"]
    for sample, key, label in (("signal", "direct_candidates", "Direct signal"),
                               ("zbb", "background_candidates", "Inclusive Zbb")):
        baseline = summary["lambda_scan"][str(max(widths))][sample]["after_lambda"][key]
        values = [summary["lambda_scan"][str(w)][sample]["after_lambda"][key] /
                  baseline if baseline else np.nan for w in widths]
        ax.plot(widths, values, ".-", label=label)
    ax.set(xlabel=r"$\Lambda^0$ mass half-window [MeV]",
           ylabel="Retention after fit-range cut", ylim=(0, 1.05))
    ax.legend()
    fig.tight_layout()
    fig.savefig(args.output_dir / "lambda_window_scan.png", dpi=160)
    plt.close(fig)
    fig, axes = plt.subplots(1, 2, figsize=(10, 4))
    for ax, sample in zip(axes, ("signal", "zbb")):
        mult = Counter()
        for item in records:
            if (item["source_id"] == -1) == (sample == "signal"):
                mult.update({int(k): int(v) for k, v in
                             item["selected_event_multiplicity"].items()})
        ax.bar(sorted(mult), [mult[x] for x in sorted(mult)])
        ax.set(xlabel="Selected candidates per selected event", ylabel="Events",
               title=sample)
    fig.tight_layout()
    fig.savefig(args.output_dir / "selected_multiplicity.png", dpi=160)
    plt.close(fig)
    print(json.dumps({"events_processed": summary["events_processed"],
                      "stage_counts": summary["stage_counts"]}, indent=2))


if __name__ == "__main__":
    main()

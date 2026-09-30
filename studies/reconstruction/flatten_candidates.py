#!/usr/bin/env python3
"""
Author: Renato Quagliani (rquaglia@cern.ch)

Flatten selected FCCAnalysis event vectors to one Parquet row per candidate.

All candidates are retained, including fakes and combinations with missing MC
links. Candidate slots and event multiplicity preserve multiple candidates in
the same event. Reco-level ancestry is joined by each candidate's leg index.
The output retains the source columns, duplicates event scalars on candidate
rows, and adds LHCb-style aliases.
"""

import argparse
import json
from pathlib import Path
import sys

import awkward as ak
import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq
import uproot

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "analysis" / "studies"))
from observables_stage1 import BRANCHES as OBS_BRANCHES


CANDIDATE_BRANCHES = {
    "lb_mass": "lb_mass",
    "lb_pt": "lb_pt",
    "lb_energy": "lb_energy",
    "lb_px": "lb_px",
    "lb_py": "lb_py",
    "lb_pz": "lb_pz",
    "lb_sign": "lb_sign",
    "cos_theta_p": "lb_cos_theta_p",
    "truth_cos_theta_p": "lb_truth_cos_theta_p",
    "lambda_mass": "lb_lambda_mass",
    "neutral_mass": "lb_neutral_mass",
    "neutral_energy": "lb_neutral_energy",
    "truth_matched": "lb_truth_matched",
    "lb_mc_index": "lb_truth_lb_mc_index",
    "neutral_mc_index": "lb_truth_neutral_mc_index",
    "mass_hypothesis_correct": "lb_mass_hypothesis_correct",
    "same_hemisphere": "lb_same_hemisphere",
    "lambda_thrust_cos": "lb_lambda_thrust_cos",
    "neutral_thrust_cos": "lb_neutral_thrust_cos",
    "lambda_px": "lb_lambda_px",
    "lambda_py": "lb_lambda_py",
    "lambda_pz": "lb_lambda_pz",
    "photon_px": "lb_photon_px",
    "photon_py": "lb_photon_py",
    "photon_pz": "lb_photon_pz",
    "proton_px": "lb_proton_px",
    "proton_py": "lb_proton_py",
    "proton_pz": "lb_proton_pz",
    "proton_energy": "lb_proton_energy",
    "proton_d0": "lb_proton_d0",
    "pion_px": "lb_pion_px",
    "pion_py": "lb_pion_py",
    "pion_pz": "lb_pion_pz",
    "pion_energy": "lb_pion_energy",
    "pion_d0": "lb_pion_d0",
}
CANDIDATE_BRANCHES.update({name: name for name in OBS_BRANCHES})
NESTED_CANDIDATE_BRANCHES = {
    "gamma_combo_other_gamma_mass", "gamma_combo_other_gamma_index",
}
LAMBDA_BRANCHES = {
    "lambda_vertex_primary": "lambda_vertex_primary",
    "lambda_vertex_chi2": "lambda_vertex_chi2",
    "lambda_vertex_x": "lambda_vertex_x",
    "lambda_vertex_y": "lambda_vertex_y",
    "lambda_vertex_z": "lambda_vertex_z",
    "lambda_flight_rxy": "lambda_flight_rxy",
    "lambda_flight_xyz": "lambda_flight_xyz",
    "lambda_flight_rxy_sigma": "lambda_flight_rxy_sigma",
    "lambda_flight_rxy_sig": "lambda_flight_rxy_sig",
    "lambda_d0": "lambda_d0",
    "lambda_d0_sigma": "lambda_d0_sigma",
    "lambda_d0_sig": "lambda_d0_sig",
    "proton_d0sig": "lambda_proton_d0sig",
    "pion_d0sig": "lambda_pion_d0sig",
}
LEG_BRANCHES = {
    "mc_index": "reco_mc_index",
    "mc_pdg": "reco_mc_pdg",
    "mc_n_parents": "reco_mc_n_parents",
    "mc_parent_index": "reco_mc_parent_index",
    "mc_parent_pdg": "reco_mc_parent_pdg",
    "mc_grandparent_index": "reco_mc_grandparent_index",
    "mc_grandparent_pdg": "reco_mc_grandparent_pdg",
    "reco_p": "reco_p",
    "reco_energy": "reco_energy",
    "mc_p": "reco_mc_p",
    "mc_energy": "reco_mc_energy",
    "mc_pt": "reco_mc_pt",
    "mc_eta": "reco_mc_eta",
    "mc_vertex_rxy": "reco_mc_vertex_rxy",
    "mc_cos_opening": "reco_mc_cos_opening",
}
LEGS = ("proton", "pion", "photon", "photon2")


def flat(array):
    return ak.to_numpy(ak.flatten(array, axis=1))


def candidate_columns(block, mode, source_id=None, candidate_branches=None,
                      event_branches=None):
    """Return one row per candidate while preserving event multiplicity.

    `candidate_slot` is local to an event; join it with `event_entry` when
    comparing scenarios. Truth and ancestry are copied as labels, never
    used to remove wrong combinations during flattening.
    """
    mass = block["lb_mass"]
    event, _ = ak.broadcast_arrays(block["event_entry"], mass)
    multiplicity, _ = ak.broadcast_arrays(block["n_lb"], mass)
    columns = {
        "event_entry": flat(event),
        "candidate_slot": flat(ak.local_index(mass)),
        "candidates_in_event": flat(multiplicity),
    }
    if source_id is not None:
        # Separate file-level batch jobs each restart event_entry at zero.
        # (source_id, event_entry, candidate_slot) is the stable joined key.
        columns["source_id"] = np.full(len(columns["event_entry"]),
                                       source_id, dtype=np.int32)
    for branch in ("thrust_value", "thrust_x", "thrust_y", "thrust_z",
                   "pv_x", "pv_y", "pv_z"):
        value, _ = ak.broadcast_arrays(block[branch], mass)
        columns[branch] = flat(value)
    # Preserve every scalar branch from the reconstructed event tree on each
    # candidate row, including future event-level additions to that tree.
    for branch in event_branches or ():
        if branch in columns:
            continue
        value, _ = ak.broadcast_arrays(block[branch], mass)
        columns[branch] = flat(value)
    for output, branch in (candidate_branches or CANDIDATE_BRANCHES).items():
        if branch in NESTED_CANDIDATE_BRANCHES:
            columns[output] = ak.to_list(ak.flatten(block[branch], axis=1))
        else:
            columns[output] = flat(block[branch])
    lambda_slots = block["lb_lambda_slot"]
    columns["lambda_slot"] = flat(lambda_slots)
    for output, branch in LAMBDA_BRANCHES.items():
        columns[output] = flat(block[branch][lambda_slots])

    # An MT snapshot made before the Lambda-to-PV pointing fields were added
    # still stores the fitted Lambda momentum and PV/SV coordinates. Derive
    # exactly the same geometry here; never substitute raw track momentum.
    can_derive = all(key in columns for key in
                     ("lambda_px", "lambda_py", "lambda_pz",
                      "lambda_vertex_x", "lambda_vertex_y", "lambda_vertex_z"))
    if "lambda_pv_cos" not in columns and can_derive:
        flight = np.stack([columns[f"lambda_vertex_{axis}"] - columns[f"pv_{axis}"]
                           for axis in "xyz"], axis=1)
        momentum = np.stack([columns[f"lambda_p{axis}"] for axis in "xyz"], axis=1)
        lm = np.linalg.norm(momentum, axis=1)
        lf = np.linalg.norm(flight, axis=1)
        dot = np.sum(flight * momentum, axis=1)
        valid = (lm > 0) & (lf > 0) & np.isfinite(dot)
        cosine = np.full(len(lm), -999., dtype=np.float32)
        distance = np.full(len(lm), -999., dtype=np.float32)
        cosine[valid] = np.clip(dot[valid] / (lm[valid] * lf[valid]), -1, 1)
        distance[valid] = np.sqrt(np.maximum(0., lf[valid] ** 2 -
                                             (dot[valid] / lm[valid]) ** 2))
        columns["lambda_pv_cos"] = cosine
        columns["lambda_pv_dca"] = distance
        columns["pointing_derived_in_flattening"] = np.ones(len(lm), dtype=np.int8)
    elif "lambda_pv_cos" in columns:
        columns["pointing_derived_in_flattening"] = np.zeros(
            len(columns["lambda_pv_cos"]), dtype=np.int8)

    for leg in LEGS:
        source = "lb_photon2_index" if leg == "photon2" else f"lb_{leg}_index"
        reco = block[source]
        columns[f"{leg}_reco_index"] = flat(reco)
        if leg == "photon2" and mode in ("gamma", "zbb"):
            for output in LEG_BRANCHES:
                columns[f"{leg}_{output}"] = np.full(
                    len(columns["lb_mass"]),
                    -999. if output in ("reco_p", "reco_energy", "mc_p",
                                       "mc_energy", "mc_pt", "mc_eta",
                                       "mc_vertex_rxy", "mc_cos_opening") else -1)
            continue
        for output, branch in LEG_BRANCHES.items():
            columns[f"{leg}_{output}"] = flat(block[branch][reco])
    if len({len(values) for values in columns.values()}) != 1:
        raise ValueError("Flattened candidate columns have unequal lengths")
    return columns


def lhcb_columns(columns):
    """Add compact LHCb-style aliases without discarding audit columns."""
    out = {key: value for key, value in columns.items()
           if key in ("source_id", "event_entry", "candidate_slot",
                      "candidates_in_event")}
    count = len(columns["lb_mass"])
    missing = np.full(count, -999., dtype=np.float32)

    def copy(alias, source):
        out[alias] = columns.get(source, missing)

    def kinematics(prefix, px, py, pz, energy=None, mass=None):
        momentum = [np.asarray(columns.get(key, missing), dtype=np.float64)
                    for key in (px, py, pz)]
        for axis, value in zip(("Px", "Py", "Pz"), momentum):
            out[f"{prefix}_{axis}"] = value
        x, y, z = momentum
        valid = np.isfinite(x) & np.isfinite(y) & np.isfinite(z) & \
            (x > -998.) & (y > -998.) & (z > -998.)
        magnitude = np.sqrt(x*x + y*y + z*z)
        transverse = np.hypot(x, y)
        out[f"{prefix}_P"] = np.where(valid, magnitude, missing)
        out[f"{prefix}_Pt"] = np.where(valid, transverse, missing)
        out[f"{prefix}_Eta"] = np.where(
            valid & (transverse > 0.), np.arcsinh(np.divide(
                z, transverse, out=np.zeros(len(z)), where=transverse > 0.)), missing)
        out[f"{prefix}_Phi"] = np.where(valid, np.arctan2(y, x), missing)
        if energy is not None:
            out[f"{prefix}_E"] = np.asarray(columns.get(energy, missing))
        elif mass is not None and mass in columns:
            out[f"{prefix}_E"] = np.where(
                valid, np.sqrt(out[f"{prefix}_P"]**2 +
                               np.asarray(columns[mass])**2), missing)
        else:
            out[f"{prefix}_E"] = missing

    # Older snapshots saved the Lambda and photon momenta but not the summed
    # Lambda_b four-vector. Recover its spatial components from those branches.
    for axis in "xyz":
        component = f"lb_p{axis}"
        if component not in columns:
            lambda_component = columns.get(f"lambda_p{axis}")
            photon_component = columns.get(f"photon_p{axis}")
            if lambda_component is not None and photon_component is not None:
                columns[component] = (np.asarray(lambda_component) +
                                      np.asarray(photon_component))
    if "lb_energy" not in columns:
        if all(key in columns and np.all(np.asarray(columns[key]) > -998.)
               for key in ("lambda_px", "lambda_py", "lambda_pz")):
            lambda_energy = np.sqrt(
                np.asarray(columns["lambda_px"])**2 +
                np.asarray(columns["lambda_py"])**2 +
                np.asarray(columns["lambda_pz"])**2 +
                np.asarray(columns.get("lambda_mass", missing))**2)
            if "photon_reco_energy" in columns:
                columns["lb_energy"] = lambda_energy + np.asarray(
                    columns["photon_reco_energy"])

    copy("Lb_M", "lb_mass")
    kinematics("Lb", "lb_px", "lb_py", "lb_pz", energy="lb_energy")
    copy("Lb_ChargeSign", "lb_sign")
    kinematics("Lambda0", "lambda_px", "lambda_py", "lambda_pz",
               mass="lambda_mass")
    copy("Lambda0_M", "lambda_mass")
    copy("Lambda0_FlightRxy", "lambda_flight_rxy")
    copy("Lambda0_Rxy", "lambda_flight_rxy")
    copy("Lambda0_FlightXYZ", "lambda_flight_xyz")
    copy("Lambda0_FlightRxySigma", "lambda_flight_rxy_sigma")
    copy("Lambda0_FlightRxySignificance", "lambda_flight_rxy_sig")
    copy("Lambda0_d0", "lambda_d0")
    copy("Lambda0_d0Sigma", "lambda_d0_sigma")
    copy("Lambda0_d0Significance", "lambda_d0_sig")
    for alias, source in (("Lambda0_PV_DCA", "lambda_pv_dca"),
                          ("Lambda0_PV_Cos", "lambda_pv_cos"),
                          ("Lambda0_SV_X", "lambda_vertex_x"),
                          ("Lambda0_SV_Y", "lambda_vertex_y"),
                          ("Lambda0_SV_Z", "lambda_vertex_z"),
                          ("Lambda0_VertexChi2", "lambda_vertex_chi2")):
        copy(alias, source)
    for axis in "xyz":
        copy(f"PV_{axis.upper()}", f"pv_{axis}")

    for particle, source in (("Proton", "proton"), ("Pion", "pion")):
        kinematics(particle, f"{source}_px", f"{source}_py",
                   f"{source}_pz", energy=f"{source}_energy")
        copy(f"{particle}_d0", f"{source}_d0")
        copy(f"{particle}_d0Significance", f"{source}_d0sig")

    kinematics("Gamma", "photon_px", "photon_py", "photon_pz",
               energy="photon_reco_energy")
    for alias, source in (("Gamma_RecoIndex", "photon_reco_index"),
                          ("Gamma_IsoR02", "iso_R02"),
                          ("Gamma_IsoR03", "iso_R03"),
                          ("Gamma_IsoR05", "iso_R05"),
                          ("Gamma_IsoR03_NoLambda", "iso_R03_noLambda"),
                          ("Gamma_IsoR05_NoLambda", "iso_R05_noLambda"),
                          ("Gamma_NPhotonsDR03", "n_photons_DR03"),
                          ("Gamma_NPhotonsDR05", "n_photons_DR05"),
                          ("GammaGamma_M_BestPi0", "m_gg_best"),
                          ("GammaGamma_DeltaM_Pi0", "dm_gg_pi0"),
                          ("GammaGamma_PartnerEnergy", "E_gamma2"),
                          ("GammaGamma_DeltaR", "dr_gg"),
                          ("GammaGamma_PartnerIndex", "gamma2_index"),
                          ("Gamma_Combo_OtherGamma_M",
                           "gamma_combo_other_gamma_mass"),
                          ("Gamma_Combo_OtherGamma_Index",
                           "gamma_combo_other_gamma_index")):
        copy(alias, source)

    # Preserve all audit/truth/isolation observables alongside the aliases.
    out.update(columns)
    return out


def _root_leaf_type(arrow_type):
    """Map an Arrow scalar type to the corresponding uproot TTree leaf type."""
    if pa.types.is_boolean(arrow_type):
        return "bool"
    if pa.types.is_integer(arrow_type):
        prefix = "u" if pa.types.is_unsigned_integer(arrow_type) else ""
        return f"{prefix}int{arrow_type.bit_width}"
    if pa.types.is_floating(arrow_type):
        return f"float{arrow_type.bit_width}"
    raise TypeError(f"Unsupported flattened ROOT branch type: {arrow_type}")


def _root_branch_types(schema):
    """Build scalar and jagged TTree branch declarations from the Arrow schema."""
    types = {}
    for field in schema:
        arrow_type = field.type
        if pa.types.is_list(arrow_type) or pa.types.is_large_list(arrow_type):
            types[field.name] = f"var * {_root_leaf_type(arrow_type.value_type)}"
        else:
            types[field.name] = _root_leaf_type(arrow_type)
    return types


def _root_arrays(table):
    """Convert an Arrow batch to arrays accepted by uproot's TTree writer."""
    arrays = {}
    for field in table.schema:
        column = table[field.name].combine_chunks()
        if pa.types.is_list(field.type) or pa.types.is_large_list(field.type):
            arrays[field.name] = ak.Array(column.to_pylist())
        else:
            arrays[field.name] = column.to_numpy(zero_copy_only=False)
    return arrays


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--root-output", type=Path,
        help="Optional flat ROOT file with an events TTree, one candidate per row")
    parser.add_argument(
        "--mode", choices=("gamma", "eta", "zbb"), required=True,
        help=("Output hypothesis/sample layout: gamma or zbb uses one photon; "
              "eta uses a two-photon neutral candidate"))
    parser.add_argument(
        "--chunk-events", type=int, default=500,
        help=("ROOT entries converted per batch (default: 500); increase for "
              "speed if memory allows, decrease to limit peak memory"))
    parser.add_argument("--source-id", type=int,
                        help="Index of the input file in a batch manifest")
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    if args.root_output is not None:
        args.root_output.parent.mkdir(parents=True, exist_ok=True)
    writer = None
    root_output = None
    root_tree = None
    events = candidates = matched = 0
    with uproot.open(str(args.input),
                     handler=uproot.source.file.MemmapSource) as root:
        tree = root["events"]
        available = set(tree.keys())
        # Keep Parquet column order reproducible across Python hash seeds.
        event_branches = tuple(sorted(
            name for name in available if "/" not in name and
            "vector" not in tree[name].typename.lower()))
        candidate_branches = {name: branch for name, branch in
                              CANDIDATE_BRANCHES.items() if branch in available}
        branches = sorted(set(event_branches) | set(candidate_branches.values()) |
                          set(LAMBDA_BRANCHES.values()) |
                          set(LEG_BRANCHES.values()) |
                          {"event_entry", "n_lb", "lb_lambda_slot",
                           "thrust_value", "thrust_x", "thrust_y", "thrust_z",
                           "pv_x", "pv_y", "pv_z"} |
                          {"lb_proton_index", "lb_pion_index",
                           "lb_photon_index", "lb_photon2_index"})
        for block in tree.iterate(branches, library="ak",
                                  step_size=args.chunk_events):
            events += len(block)
            n = int(ak.sum(block["n_lb"]))
            candidates += n
            if n == 0:
                continue
            columns = candidate_columns(block, args.mode, args.source_id,
                                        candidate_branches, event_branches)
            matched += int(np.count_nonzero(columns["truth_matched"]))
            table = pa.table(lhcb_columns(columns))
            if writer is None:
                metadata = {b"mode": args.mode.encode(),
                            b"source": str(args.input).encode(),
                            b"schema": b"candidate rows plus LHCb-style aliases"}
                if args.source_id is not None:
                    metadata[b"source_id"] = str(args.source_id).encode()
                writer = pq.ParquetWriter(
                    str(args.output), table.schema.with_metadata(metadata),
                    compression="zstd")
            writer.write_table(table)
            if args.root_output is not None:
                if root_output is None:
                    root_output = uproot.recreate(str(args.root_output))
                    root_tree = root_output.mktree(
                        "events", _root_branch_types(table.schema),
                        title="One row per selected Lambda_b candidate")
                root_tree.extend(_root_arrays(table))
    if writer is not None:
        writer.close()
    else:
        pq.write_table(pa.table({"event_entry": pa.array([], type=pa.int64())}),
                       args.output)
    if root_output is not None:
        root_output.close()
    elif args.root_output is not None:
        # Keep a valid, empty candidate TTree for a sample with no selected rows.
        with uproot.recreate(str(args.root_output)) as empty_root:
            empty_root.mktree("events", {"event_entry": "int64"},
                              title="One row per selected Lambda_b candidate")
    summary = {"input": str(args.input), "output": str(args.output),
               "mode": args.mode, "events": events,
               "source_id": args.source_id,
               "candidates": candidates, "truth_matched_candidates": matched,
               "gamma_combo_other_gamma_mass":
                   "list of invariant masses against every other raw reconstructed photon"}
    summary_path = args.output.with_suffix(".summary.json")
    summary_path.write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()

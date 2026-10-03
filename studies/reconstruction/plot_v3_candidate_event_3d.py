#!/usr/bin/env python3
"""Draw one reconstructed v3 candidate and its event activity in 3D.

The figure is a direction-space display. Arrow lengths are normalized for
legibility; the recorded momenta and object classifications are in JSON.
Candidate vectors come from the Stage 1 tuple, while other reconstructed
particles come from the corresponding EDM4hep input entry. Truth is only
reported as an annotation, never used to define the displayed candidate.
"""

import argparse
import json
import math
import os
from pathlib import Path
import tempfile

os.environ.setdefault("MPLCONFIGDIR", str(Path(tempfile.gettempdir()) / "lblgamma-mplconfig"))
os.environ.setdefault("XDG_CACHE_HOME", str(Path(tempfile.gettempdir()) / "lblgamma-cache"))
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import awkward as ak
import numpy as np
import uproot

import v3_plot_style  # noqa: F401: apply the shared mplhep LHCb style


DEFAULT_RADII = (0.3, 0.5)
VECTOR_NAMES = ("proton", "pion", "photon", "lambda")


def unit(vector):
    norm = np.linalg.norm(vector)
    if not np.isfinite(norm) or norm <= 0:
        raise ValueError(f"Zero or invalid direction: {vector}")
    return vector / norm


def eta_phi(vector):
    x, y, z = vector
    pt = math.hypot(x, y)
    if pt <= 0:
        return math.nan, math.nan
    return math.asinh(z / pt), math.atan2(y, x)


def direction(eta, phi):
    return np.stack((np.cos(phi) / np.cosh(eta),
                     np.sin(phi) / np.cosh(eta), np.tanh(eta)), axis=-1)


def delta_r(a, b):
    ea, pa = eta_phi(a)
    eb, pb = eta_phi(b)
    if not np.isfinite(ea + pa + eb + pb):
        return math.inf
    dphi = math.atan2(math.sin(pa - pb), math.cos(pa - pb))
    return math.hypot(ea - eb, dphi)


def root_row(tree, row, branches):
    if row < 0 or row >= tree.num_entries:
        raise ValueError(f"Tuple row {row} outside 0..{tree.num_entries - 1}")
    values = tree.arrays(branches, entry_start=row, entry_stop=row + 1,
                         library="np")
    return {name: values[name][0] for name in branches}


def source_identity(path):
    stat = path.stat()
    return {"path": str(path.resolve()), "bytes": stat.st_size,
            "mtime_ns": stat.st_mtime_ns}


def find_source_entry(tree, photon_index, photon_momentum):
    """Find the unique raw event with this measured photon at this index."""
    branches = [f"ReconstructedParticles/ReconstructedParticles.momentum.{dim}"
                for dim in ("x", "y", "z")]
    matches = []
    offset = 0
    for block in tree.iterate(branches, step_size=4096, library="ak"):
        arrays = [ak.to_list(block[name]) for name in branches]
        for local, components in enumerate(zip(*arrays)):
            if all(len(values) > photon_index for values in components):
                found = np.array([values[photon_index] for values in components])
                if np.linalg.norm(found - photon_momentum) < .005:
                    matches.append(offset + local)
        offset += len(arrays[0])
    if len(matches) != 1:
        raise ValueError(f"Expected one raw event for selected photon; found {matches}")
    return matches[0]


def arrow(ax, vector, color, label, length=1.0, linewidth=2.5,
          label_offset=(0, 0, 0)):
    u = unit(vector) * length
    ax.quiver(0, 0, 0, *u, color=color, linewidth=linewidth,
              arrow_length_ratio=0.10)
    ax.text(*(u * 1.08 + np.asarray(label_offset)), label, color=color, fontsize=9)


def cone_boundary(ax, center, radius, color, linestyle="-"):
    """Map the exact ΔR circle in η–φ onto unit 3D directions."""
    eta, phi = eta_phi(center)
    t = np.linspace(0, 2 * np.pi, 240)
    xyz = direction(eta + radius * np.cos(t), phi + radius * np.sin(t))
    ax.plot(*xyz.T, color=color, linestyle=linestyle, marker="", linewidth=1.5,
            alpha=0.8)


def plot_display(output, title, candidate, thrust, objects, radii, view,
                 show_other):
    fig = plt.figure(figsize=(11.5, 8.5))
    ax = fig.add_subplot(111, projection="3d", computed_zorder=False)
    theta = np.linspace(0, 2 * np.pi, 100)
    circle = np.stack((np.cos(theta), np.sin(theta), np.zeros_like(theta)))
    # The plane perpendicular to thrust separates the two thrust hemispheres.
    normal = unit(thrust)
    base = np.array([1., 0., 0.]) if abs(normal[0]) < .85 else np.array([0., 1., 0.])
    u = unit(np.cross(normal, base))
    v = np.cross(normal, u)
    ring = circle[0, :, None] * u + circle[1, :, None] * v
    ax.plot(*ring.T, color="0.6", marker="", linewidth=1, alpha=.8)
    arrow(ax, normal, "0.45", "thrust", .92, 1.3)
    arrow(ax, -normal, "0.65", "−thrust", .92, 1.0)

    for obj in objects:
        if obj["index"] in show_other:
            continue
        p = np.array(obj["momentum_gev"])
        if np.linalg.norm(p) <= 0:
            continue
        d = unit(p)
        color = "#6b7180" if obj["charge"] else "#9c88a8"
        ax.scatter(*d, color=color, s=12 + 6 * np.log1p(np.linalg.norm(p)),
                   alpha=.68 if obj["same_lambda_hemisphere"] else .25,
                   marker="o" if obj["same_lambda_hemisphere"] else "x",
                   depthshade=False)

    colors = {"proton": "#d1495b", "pion": "#ed8d35",
              "photon": "#2b7bb9", "lambda": "#32885b"}
    for name in VECTOR_NAMES:
        label = {"proton": "p", "pion": "π", "photon": "γ",
                 "lambda": "fitted Λ⁰"}[name]
        offset = {"proton": (0, -.12, -.05), "pion": (0, .09, .05),
                  "photon": (0, -.03, -.05), "lambda": (0, .02, .07)}[name]
        arrow(ax, candidate[name], colors[name], label,
              .95 if name != "lambda" else 1.04, label_offset=offset)
    for i, radius in enumerate(radii):
        cone_boundary(ax, candidate["photon"], radius, colors["photon"],
                      "-" if i == 0 else "--")
        cone_boundary(ax, candidate["lambda"], radius, colors["lambda"],
                      "-" if i == 0 else "--")

    ax.set(xlabel="unit pₓ", ylabel="unit pᵧ", zlabel="unit p_z",
           xlim=(-1.25, 1.25), ylim=(-1.25, 1.25), zlim=(-1.25, 1.25),
           title=title)
    ax.set_box_aspect((1, 1, 1), zoom=.86)
    ax.view_init(elev=view[0], azim=view[1])
    ax.text2D(.02, .02,
              "Blue/green rings: exact ΔR boundaries around γ/Λ⁰ in η–φ\n"
              "Solid/dashed: ΔR = " + ", ".join(str(x) for x in radii) +
              "   •   grey ring: thrust-hemisphere boundary\n"
              "Grey/purple: other charged/neutral particles; crosses: opposite hemisphere\n"
              "Arrow lengths normalized; fitted daughter directions shown",
              transform=ax.transAxes, fontsize=8.5, va="bottom")
    fig.tight_layout()
    fig.savefig(output, dpi=180)
    plt.close(fig)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--stage1", type=Path, required=True)
    ap.add_argument("--edm4hep", type=Path, required=True)
    ap.add_argument("--tuple-row", type=int, default=0,
                    help="Row in filtered Stage 1 events tree")
    ap.add_argument("--candidate-slot", type=int, default=0)
    ap.add_argument("--resolve-source-entry", action="store_true",
                    help="If event_entry mismatches raw photon, search raw events by exact photon momentum/index")
    ap.add_argument("--radii", type=float, nargs="+", default=DEFAULT_RADII)
    ap.add_argument("--output-dir", type=Path, required=True)
    args = ap.parse_args()
    if any(r <= 0 for r in args.radii):
        ap.error("All ΔR radii must be positive")

    fields = ["event_entry", "thrust_x", "thrust_y", "thrust_z",
              "lb_truth_matched", "lb_same_hemisphere", "lb_mass",
              "lb_proton_index", "lb_pion_index", "lb_photon_index"]
    for name in VECTOR_NAMES:
        prefix = "lb_lambda" if name == "lambda" else f"lb_{name}"
        fields.extend(f"{prefix}_{dim}" for dim in ("px", "py", "pz"))
    iso_fields = {}
    for center, prefix in (("photon", "iso"), ("lambda", "lambda0_iso")):
        for radius in args.radii:
            code = round(radius * 10)
            if abs(radius * 10 - code) > 1e-9 or code not in (2, 3, 5, 7, 10, 20):
                continue
            for klass in ("all", "charged", "neutral"):
                branch = f"{prefix}_R{code:02d}_{klass}_n"
                fields.append(branch)
                iso_fields[(center, str(radius), klass)] = branch
    with uproot.open(f"{args.stage1}:events") as stage1:
        row = root_row(stage1, args.tuple_row, fields)
    slot = args.candidate_slot
    n = len(row["lb_mass"])
    if slot < 0 or slot >= n:
        ap.error(f"Candidate slot {slot} outside 0..{n - 1}")
    entry = int(row["event_entry"])
    candidate = {}
    for name in VECTOR_NAMES:
        prefix = "lb_lambda" if name == "lambda" else f"lb_{name}"
        candidate[name] = np.array([float(row[f"{prefix}_{dim}"][slot])
                                    for dim in ("px", "py", "pz")])
    thrust = np.array([float(row[f"thrust_{dim}"]) for dim in ("x", "y", "z")])
    indices = {name: int(row[f"lb_{name}_index"][slot])
               for name in ("proton", "pion", "photon")}

    source_fields = ["ReconstructedParticles/ReconstructedParticles.momentum.x",
                     "ReconstructedParticles/ReconstructedParticles.momentum.y",
                     "ReconstructedParticles/ReconstructedParticles.momentum.z",
                     "ReconstructedParticles/ReconstructedParticles.energy",
                     "ReconstructedParticles/ReconstructedParticles.charge"]
    source_entry = entry
    with uproot.open(f"{args.edm4hep}:events") as source:
        if entry >= source.num_entries:
            raise ValueError(f"Stage 1 event_entry={entry} exceeds input entries")
        original = root_row(source, source_entry, source_fields)
        pi = indices["photon"]
        original_photon = np.array([original[name][pi] for name in source_fields[:3]])
        if np.linalg.norm(original_photon - candidate["photon"]) > .05:
            if not args.resolve_source_entry:
                raise ValueError(
                    f"Stage 1 event_entry {entry} photon at index {pi} differs "
                    "from the raw file. Use --resolve-source-entry to search "
                    "for an exact photon match and record the discrepancy.")
            source_entry = find_source_entry(source, pi, candidate["photon"])
            original = root_row(source, source_entry, source_fields)
    cols = [original[name] for name in source_fields]
    objects = []
    for i, (px, py, pz, energy, charge) in enumerate(zip(*cols)):
        momentum = [float(px), float(py), float(pz)]
        objects.append({"index": i, "momentum_gev": momentum,
                        "energy_gev": float(energy), "charge": float(charge),
                        "same_lambda_hemisphere": bool(np.dot(thrust, candidate["lambda"])
                                                        * np.dot(thrust, momentum) > 0),
                        "dr_photon": delta_r(candidate["photon"], momentum),
                        "dr_lambda": delta_r(candidate["lambda"], momentum)})
    if max(indices.values()) >= len(objects):
        raise ValueError("Candidate reconstructed-particle index exceeds source collection")
    for name, index in indices.items():
        if name == "photon" and np.linalg.norm(candidate[name] - objects[index]["momentum_gev"]) > .05:
            nearest = sorted(
                ((float(np.linalg.norm(candidate[name] - obj["momentum_gev"])),
                  obj["index"]) for obj in objects))[:3]
            raise ValueError(
                f"Candidate photon {candidate[name].tolist()} at index {index} "
                f"does not match input event {source_entry} photon "
                f"{objects[index]['momentum_gev']}; nearest objects: {nearest}; "
                "check source provenance")

    args.output_dir.mkdir(parents=True, exist_ok=True)
    title = (f"v3 reconstructed Λb→Λ⁰γ candidate • tuple key {entry}, raw entry {source_entry}, slot {slot}\n"
             f"m(Λγ)={float(row['lb_mass'][slot]):.3f} GeV; "
             f"same thrust hemisphere={bool(row['lb_same_hemisphere'][slot])}")
    for suffix, view in (("a", (23, -62)), ("b", (20, 32))):
        plot_display(args.output_dir / f"candidate_3d_view_{suffix}.png",
                     title, candidate, thrust, objects, args.radii, view,
                     set(indices.values()))
    record = {
        "purpose": "single-event explanatory display; no efficiency or yield inference",
        "stage1": source_identity(args.stage1), "edm4hep": source_identity(args.edm4hep),
        "tuple_row": args.tuple_row, "event_entry": entry,
        "source_entry": source_entry,
        "source_entry_matches_stage1_event_entry": source_entry == entry,
        "candidate_slot": slot,
        "candidate_count_in_output_event": n,
        "truth_matched_annotation_only": int(row["lb_truth_matched"][slot]),
        "candidate_mass_gev": float(row["lb_mass"][slot]),
        "same_hemisphere": bool(row["lb_same_hemisphere"][slot]),
        "thrust_axis": thrust.tolist(), "candidate_momenta_gev":
        {name: vector.tolist() for name, vector in candidate.items()},
        "candidate_reco_indices": indices, "radii_delta_r": args.radii,
        "other_objects": objects,
        "excluded_from_isolation": list(indices.values()),
        "isolation_counts": {
            center: {str(radius): {
                klass: sum(1 for obj in objects
                           if obj["index"] not in indices.values()
                           and obj["same_lambda_hemisphere"]
                           and obj[f"dr_{center}"] < radius
                           and (klass == "all" or
                                bool(obj["charge"]) == (klass == "charged")))
                for klass in ("all", "charged", "neutral")}
                for radius in args.radii}
            for center in ("photon", "lambda")},
        "note": "Activity cone membership additionally requires fitted-Lambda thrust hemisphere. "
                "The displayed 3D ring is the exact mapped eta-phi DeltaR boundary, "
                "not a constant opening-angle cone. All arrow lengths are normalized."
    }
    record["saved_stage1_isolation_counts"] = {}
    for (center, radius, klass), branch in iso_fields.items():
        saved = int(row[branch][slot])
        computed = record["isolation_counts"][center][radius][klass]
        record["saved_stage1_isolation_counts"][branch] = saved
        if saved != computed:
            raise ValueError(
                f"Display cone membership disagrees with Stage 1 {branch}: "
                f"computed={computed}, saved={saved}; no figure accepted")
    (args.output_dir / "event_display.json").write_text(json.dumps(record, indent=2) + "\n")
    print(json.dumps({"event_entry": entry, "source_entry": source_entry,
                      "candidate_slot": slot,
                      "truth_matched_annotation_only": record["truth_matched_annotation_only"],
                      "reconstructed_particles": len(objects),
                      "output_dir": str(args.output_dir)}, indent=2))


if __name__ == "__main__":
    main()

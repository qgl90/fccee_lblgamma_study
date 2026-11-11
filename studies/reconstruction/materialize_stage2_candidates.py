#!/usr/bin/env python3
"""Join offline flags and a frozen BDT score onto full Stage-1 candidate rows.

The full flattened Stage-1 table supplies every saved candidate observable;
the scored audit supplies cut flags, derived Stage-2 observables, and the score. Join by the exact
(source_id, event_entry, candidate_slot) key and reject any incomplete join.
"""

# Author: Renato Quagliani (rquaglia@cern.ch)

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.parquet as pq

from armenteros import from_three_momenta


KEYS = ("source_id", "event_entry", "candidate_slot")
ATTACH = ("pass_fit", "pass_lambda", "pass_selected",
          "pass_pi0", "pass_eta", "pass_low_mass", "d_pi0", "d_eta",
          "min_pair", "bdt_score")


def keys(table):
    for name in KEYS:
        if name not in table.column_names:
            raise ValueError(f"Missing key column {name}")
    cols = [table[name].to_numpy(zero_copy_only=False) for name in KEYS]
    return list(zip(*(col.tolist() for col in cols)))


def attach(full, scored):
    for name in ATTACH:
        if name not in scored.column_names:
            raise ValueError(f"Scored audit lacks {name}")
        if name in full.column_names:
            raise ValueError(f"Full candidate table already contains {name}")
    full_keys = keys(full)
    scored_keys = keys(scored)
    index = {key: row for row, key in enumerate(scored_keys)}
    if len(index) != len(scored_keys) or len(set(full_keys)) != len(full_keys):
        raise ValueError("Repeated candidate key in a flat or scored table")
    if len(full_keys) != len(scored_keys) or set(full_keys) != set(index):
        raise ValueError("Flat and scored audit candidate keys do not match exactly")
    ordered = scored.take(pa.array([index[key] for key in full_keys], type=pa.int64()))
    # Preserve every derived Stage-2 observable as well as the full Stage-1
    # schema. The fixed list above guards the required selection/score fields.
    for name in ordered.column_names:
        if name not in full.column_names:
            full = full.append_column(name, ordered[name])
    # Compute the misidentification-study plane from fitted reconstructed
    # daughter momenta. Keep these as diagnostics; neither the offline cut nor
    # the trained BDT uses them unless a later named scenario says so.
    momentum = ("proton_px", "proton_py", "proton_pz",
                "pion_px", "pion_py", "pion_pz", "lb_sign")
    if not all(name in full.column_names for name in momentum):
        raise ValueError("Full Stage-1 table lacks fitted Armenteros inputs")
    proton = np.column_stack([full[name].to_numpy(zero_copy_only=False)
                              for name in momentum[:3]])
    pion = np.column_stack([full[name].to_numpy(zero_copy_only=False)
                            for name in momentum[3:6]])
    alpha, qt = from_three_momenta(
        proton, pion, full["lb_sign"].to_numpy(zero_copy_only=False))
    # v3 already stores both values from the fitted momenta in Stage 1.
    # Keep their provenance and check the independent Python calculation.
    for name, calculated in (("arm_alpha", alpha), ("arm_qt", qt),
                             ("arm_qt_gev", qt)):
        if name in full.column_names:
            saved = full[name].to_numpy(zero_copy_only=False)
            if not np.allclose(saved, calculated, atol=2e-5, rtol=2e-5,
                               equal_nan=True):
                raise ValueError(f"Saved {name} differs from fitted-track calculation")
        else:
            full = full.append_column(name, pa.array(calculated))
    return full


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--flat-dir", type=Path, required=True,
                    help="Full flattened Stage-1 shards named signal_-1.parquet, zbb_N.parquet")
    ap.add_argument("--prepared-dir", type=Path, required=True,
                    help="Offline preparation containing the unscored audit shards")
    ap.add_argument("--scored-audit-dir", type=Path, required=True,
                    help="Audit shards scored by apply_offline_bdt.py --table audit")
    ap.add_argument("--projection", type=Path,
                    help="Optional projection.json containing the validation-fixed BDT score")
    ap.add_argument("--output-dir", type=Path, required=True)
    ap.add_argument("--max-shards", type=int, help="Development check only")
    ap.add_argument("--resume", action="store_true",
                    help="Reuse complete output shards after an interrupted run")
    args = ap.parse_args()
    projection = json.loads(args.projection.read_text()) if args.projection else None
    prepared_manifest = (args.prepared_dir / "summary.json").resolve()
    if projection and Path(projection["prepared_manifest"]).resolve() != prepared_manifest:
        raise ValueError("Projection and prepared directory differ")
    score_manifest_path = args.scored_audit_dir / "score_manifest.json"
    if score_manifest_path.exists():
        score_manifest = json.loads(score_manifest_path.read_text())
        if Path(score_manifest["input_manifest"]).resolve() != prepared_manifest or \
                score_manifest["table"] != "audit":
            raise ValueError("Scored audit and prepared directory differ")
    choice = projection.get("validation_choice") if projection else None
    if projection and (not choice or "score" not in choice):
        raise ValueError("Projection has no validation-fixed score choice")
    threshold = float(choice["score"]) if choice else None
    if threshold is not None and not np.isfinite(threshold):
        raise ValueError("Nonfinite BDT threshold")
    shards = sorted(args.scored_audit_dir.glob("*_audit.parquet"))
    expected = {p.name for p in args.prepared_dir.glob("*_audit.parquet")}
    actual = {p.name for p in shards}
    if not expected or (args.max_shards is None and expected != actual):
        raise ValueError("Scored audit shards do not match the prepared audit")
    if args.max_shards is not None:
        if args.max_shards < 1:
            ap.error("--max-shards must be positive")
        shards = shards[:args.max_shards]
    if not shards:
        raise ValueError("No scored audit shards found")
    names = ("audit", "offline_selected", "bdt_selected") if choice else (
        "audit", "offline_selected")
    for name in names:
        (args.output_dir / name).mkdir(parents=True, exist_ok=True)
    records = []
    for scored_path in shards:
        stem = scored_path.name.removesuffix("_audit.parquet")
        flat_path = args.flat_dir / f"{stem}.parquet"
        if not flat_path.is_file():
            raise FileNotFoundError(flat_path)
        destinations = {name: args.output_dir / name / f"{stem}.parquet"
                        for name in names}
        existing = [path.exists() for path in destinations.values()]
        if any(existing):
            if not args.resume or not all(existing):
                raise FileExistsError(f"Incomplete or existing {stem} Stage-2 output")
            output_counts = {name: pq.read_metadata(path).num_rows
                             for name, path in destinations.items()}
            scored_rows = pq.read_metadata(scored_path).num_rows
            prepared_selected = args.prepared_dir / f"{stem}_selected.parquet"
            selected_rows = pq.read_metadata(prepared_selected).num_rows
            if output_counts["audit"] != scored_rows or \
                    output_counts["offline_selected"] != selected_rows or \
                    ("bdt_selected" in output_counts and
                     output_counts["bdt_selected"] > selected_rows):
                raise ValueError(f"Existing {stem} output has wrong row count")
            flat_columns = set(pq.read_schema(flat_path).names)
            for path in destinations.values():
                columns = set(pq.read_schema(path).names)
                if not flat_columns.issubset(columns) or \
                        not {"pass_selected", "bdt_score"}.issubset(columns):
                    raise ValueError(f"Existing {path} lacks required columns")
            records.append({"shard": stem, "flat_input": str(flat_path),
                            "scored_audit": str(scored_path),
                            "stage1_candidates": output_counts["audit"],
                            "offline_selected_candidates": output_counts["offline_selected"],
                            "bdt_selected_candidates": output_counts.get("bdt_selected"),
                            "columns_preserved_from_flat": len(pq.read_schema(flat_path).names),
                            "reused": True})
            continue
        full = attach(pq.read_table(flat_path), pq.read_table(scored_path))
        metadata = dict(full.schema.metadata or {})
        metadata.update({b"stage2_flat_input": str(flat_path).encode(),
                         b"stage2_scored_audit": str(scored_path).encode()})
        if args.projection:
            metadata[b"stage2_projection"] = str(args.projection).encode()
            metadata[b"stage2_bdt_score_cut"] = repr(threshold).encode()
        full = full.replace_schema_metadata(metadata)
        offline = full.filter(full["pass_selected"])
        bdt = (offline.filter(pc.greater_equal(offline["bdt_score"], threshold))
               if choice else None)
        tables = (("audit", full), ("offline_selected", offline)) + (
            (("bdt_selected", bdt),) if choice else ())
        for name, table in tables:
            pq.write_table(table, destinations[name], compression="zstd")
        records.append({"shard": stem, "flat_input": str(flat_path),
                        "scored_audit": str(scored_path),
                        "stage1_candidates": full.num_rows,
                        "offline_selected_candidates": offline.num_rows,
                        "bdt_selected_candidates": bdt.num_rows if bdt is not None else None,
                        "columns_preserved_from_flat": len(pq.read_schema(flat_path).names)})
        print(f"Materialized {stem}: {full.num_rows} → {offline.num_rows}"
              + (f" → {bdt.num_rows}" if bdt is not None else ""), flush=True)
    result = {"projection": str(args.projection) if args.projection else None,
              "projection_sha256": hashlib.sha256(args.projection.read_bytes()).hexdigest()
              if args.projection else None,
              "bdt_score_cut": threshold,
              "limited_shards": args.max_shards is not None,
              "shards": records,
              "totals": {name: sum(row[name] for row in records) for name in
                         (("stage1_candidates", "offline_selected_candidates",
                           "bdt_selected_candidates") if choice else
                          ("stage1_candidates", "offline_selected_candidates"))}}
    (args.output_dir / "manifest.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result["totals"], indent=2))


if __name__ == "__main__":
    main()

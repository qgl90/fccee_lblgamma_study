#!/usr/bin/env python3
"""Inventory winter2023 IDEA generic Zbb ROOT files without processing events.

Read only each ROOT `events` tree header. Save an exact entry count and a
deterministic file list reaching the requested baseline size. A catalogue
entry is not a physics yield: no generator weights or selection are applied.
"""

import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
import json
import os
from pathlib import Path

import uproot


DEFAULT_DIRECTORY = Path(
    "/eos/experiment/fcc/ee/generation/DelphesEvents/winter2023/IDEA/"
    "p8_ee_Zbb_ecm91")
DEFAULT_METADATA = Path(
    "/cvmfs/fcc.cern.ch/FCCDicts/FCCee_procDict_winter2023_IDEA.json")


def inspect(path):
    try:
        with uproot.open(str(path), handler=uproot.source.file.MemmapSource) as root:
            entries = int(root["events"].num_entries)
        return {"path": str(path), "entries": entries,
                "bytes": path.stat().st_size}
    except Exception as exc:
        return {"path": str(path), "error": str(exc)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", type=Path, default=DEFAULT_DIRECTORY)
    parser.add_argument("--metadata", type=Path, default=DEFAULT_METADATA)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--all-files-output", type=Path,
                        help="Optional path list containing every readable ROOT file")
    parser.add_argument("--target-events", type=int, default=1_000_000)
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--max-files", type=int, default=0,
                        help="Optional initial subset for a catalog smoke check")
    args = parser.parse_args()
    if args.target_events <= 0 or not 1 <= args.workers <= 32:
        raise ValueError("target-events must be positive; workers must be 1–32")
    files = sorted(Path(entry.path) for entry in os.scandir(args.directory)
                   if entry.is_file() and entry.name.endswith(".root"))
    files_on_eos = len(files)
    if args.max_files:
        files = files[:args.max_files]
    metadata = json.loads(args.metadata.read_text())["p8_ee_Zbb_ecm91"]
    rows = []
    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = [executor.submit(inspect, path) for path in files]
        for i, future in enumerate(as_completed(futures), start=1):
            rows.append(future.result())
            if i % 500 == 0 or i == len(files):
                print(f"Inspected {i}/{len(files)} ROOT headers", flush=True)
    rows.sort(key=lambda row: row["path"])
    good = [row for row in rows if "entries" in row]
    errors = [row for row in rows if "error" in row]
    selected = []
    total_target = 0
    for row in good:
        if total_target >= args.target_events:
            break
        selected.append(row)
        total_target += row["entries"]
    if total_target < args.target_events:
        raise ValueError(f"Readable files provide only {total_target} entries, "
                         f"below target {args.target_events}")
    counts = Counter(row["entries"] for row in good)
    result = {
        "sample": "p8_ee_Zbb_ecm91",
        "campaign": "winter2023",
        "detector": "IDEA",
        "directory": str(args.directory),
        "metadata_source": str(args.metadata),
        "campaign_metadata": metadata,
        "indexed_utc": datetime.now(timezone.utc).isoformat(),
        "root_files_on_eos": files_on_eos,
        "files_inspected": len(files), "files_readable": len(good),
        "files_failed": len(errors),
        "events_available_in_readable_files": sum(row["entries"] for row in good),
        "total_bytes_readable_files": sum(row["bytes"] for row in good),
        "event_counts_per_file": dict(sorted(counts.items())),
        "target_events": args.target_events,
        "selected_files": len(selected),
        "selected_files_total_entries": total_target,
        "selected_file_paths": [row["path"] for row in selected],
        "errors": errors,
        "files": good,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    files_path = args.output.with_suffix(".files.txt")
    files_path.write_text("\n".join(row["path"] for row in selected) + "\n")
    if args.all_files_output:
        args.all_files_output.parent.mkdir(parents=True, exist_ok=True)
        args.all_files_output.write_text("\n".join(row["path"] for row in good) + "\n")
    print(json.dumps({key: value for key, value in result.items()
                      if key not in ("files", "selected_file_paths", "errors")},
                     indent=2))
    print(f"File list: {files_path}")


if __name__ == "__main__":
    main()

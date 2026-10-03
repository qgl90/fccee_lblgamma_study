#!/usr/bin/env python3
"""Catalog native FCCAnalyses Z-flavour Condor chunks and their input files."""

import argparse
import hashlib
import json
import re
import shlex
import subprocess
from pathlib import Path

import uproot


ROOT_RE = re.compile(r"chunk_(\d+)\.root$")


def indexed_paths(directory, pattern, regex):
    result = {}
    for path in directory.glob(pattern):
        match = regex.fullmatch(path.name)
        if match is None:
            continue
        index = int(match.group(1))
        if index in result:
            raise ValueError(f"Duplicate chunk {index} in {directory}")
        result[index] = path
    return result


def eos_root_sizes(directory):
    """List EOS files without relying on the mounted directory enumeration."""
    output = subprocess.check_output(["eos", "ls", "-l", str(directory)], text=True)
    sizes = {}
    for line in output.splitlines():
        words = line.split()
        if len(words) < 9 or not ROOT_RE.fullmatch(words[-1]):
            continue
        index = int(ROOT_RE.fullmatch(words[-1]).group(1))
        if index in sizes:
            raise ValueError(f"Duplicate EOS chunk {index}")
        sizes[index] = int(words[4])
    return sizes


def job_inputs(path):
    commands = [line for line in path.read_text().splitlines()
                if "fccanalysis run " in line and "--files-list " in line]
    if len(commands) != 1:
        raise ValueError(f"Expected one fccanalysis command in {path}")
    tokens = shlex.split(commands[0])
    start = tokens.index("--files-list") + 1
    files = [token for token in tokens[start:] if token.endswith(".root")]
    if not files or len(files) != len(set(files)):
        raise ValueError(f"Empty or repeated input file list in {path}")
    return files


def root_counts(path):
    with uproot.open(path) as root:
        required = ("events", "eventsProcessed", "eventsSelected")
        if any(name not in root for name in required):
            raise ValueError(f"Missing ROOT objects in {path}")
        processed = int(root["eventsProcessed"].value)
        selected = int(root["eventsSelected"].value)
        entries = int(root["events"].num_entries)
        if processed < 0 or selected < 0 or entries != selected or selected > processed:
            raise ValueError(f"Inconsistent event counters in {path}: "
                             f"{processed}, {selected}, {entries}")
        tree = root["events"]
        schema_text = "\n".join(f"{name}:{tree[name].typename}"
                                for name in sorted(tree.keys()))
        schema_sha256 = hashlib.sha256(schema_text.encode()).hexdigest()
        return processed, selected, schema_sha256, len(tree.keys())


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--job-dir", type=Path, required=True)
    ap.add_argument("--root-dir", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--sample-name",
                    help="FCC process name; defaults to the job-dir basename")
    ap.add_argument("--max-chunks", type=int,
                    help="Limit completed roots checked for a development trial")
    ap.add_argument("--previous-catalog", type=Path,
                    help="Reuse previously validated headers when path and byte size match")
    ap.add_argument("--eos-cli", action="store_true",
                    help="List EOS with its CLI and open new ROOT files through XRootD")
    args = ap.parse_args()
    if args.max_chunks is not None and args.max_chunks <= 0:
        ap.error("--max-chunks must be positive")
    sample_name = args.sample_name or args.job_dir.name
    if not re.fullmatch(r"p8_ee_Z[a-z]+_ecm91", sample_name):
        ap.error(f"Unsupported sample name: {sample_name}")
    job_re = re.compile(rf"job_{re.escape(sample_name)}_chunk_(\d+)\.sh$")
    jobs = indexed_paths(args.job_dir, f"job_{sample_name}_chunk_*.sh", job_re)
    if args.eos_cli:
        root_sizes = eos_root_sizes(args.root_dir)
        roots = {index: args.root_dir / f"chunk_{index}.root" for index in root_sizes}
    else:
        roots = indexed_paths(args.root_dir, "chunk_*.root", ROOT_RE)
        root_sizes = {index: path.stat().st_size for index, path in roots.items()}
    previous = {}
    if args.previous_catalog:
        old = json.loads(args.previous_catalog.read_text())
        if old["sample_name"] != sample_name or old["root_dir"] != str(args.root_dir):
            raise ValueError("Previous catalog identifies a different campaign")
        previous = {item["chunk_id"]: item for item in old["chunks"]}
    if not jobs:
        raise ValueError(f"No native job scripts found in {args.job_dir}")
    unknown_roots = sorted(set(roots) - set(jobs))
    if unknown_roots:
        raise ValueError(f"ROOT chunks without job scripts: {unknown_roots}")
    all_inputs = {}
    for index, path in sorted(jobs.items()):
        for source in job_inputs(path):
            if source in all_inputs:
                raise ValueError(f"Input {source} repeated in jobs {all_inputs[source]} and {index}")
            all_inputs[source] = index
    selected = sorted(roots)[:args.max_chunks]
    records = []
    errors = []
    reused = 0
    for index in selected:
        path = roots[index]
        prior = previous.get(index)
        if prior and prior["root"] == str(path) and prior["root_bytes"] == root_sizes[index] \
                and prior["job_script"] == str(jobs[index]) and \
                prior["input_files"] == job_inputs(jobs[index]):
            records.append(prior)
            reused += 1
            continue
        try:
            access_path = ("root://eoslhcb.cern.ch//" + str(path).lstrip("/")) \
                          if args.eos_cli else path
            processed, kept, schema_sha256, branches = root_counts(access_path)
        except Exception as exc:
            errors.append({"chunk_id": index, "path": str(path), "error": str(exc)})
            continue
        records.append({
            "chunk_id": index,
            "root": str(path),
            "root_bytes": root_sizes[index],
            "job_script": str(jobs[index]),
            "input_files": job_inputs(jobs[index]),
            "events_processed": processed,
            "candidate_bearing_output_events": kept,
            "schema_sha256": schema_sha256,
            "root_branches": branches,
        })
    result = {
        "sample_name": sample_name,
        "job_dir": str(args.job_dir), "root_dir": str(args.root_dir),
        "job_scripts": len(jobs), "unique_source_files_in_jobs": len(all_inputs),
        "root_chunks_present_at_scan": len(roots),
        "root_chunks_checked": len(selected),
        "previously_validated_chunks_reused": reused,
        "newly_header_validated_chunks": len(records) - reused,
        "valid_chunks": len(records), "invalid_chunks": errors,
        "missing_chunk_ids": sorted(set(jobs) - set(roots)),
        "total_processed_events_in_valid_chunks": sum(r["events_processed"] for r in records),
        "total_candidate_bearing_output_events_in_valid_chunks": sum(
            r["candidate_bearing_output_events"] for r in records),
        "schema_counts": {signature: sum(r["schema_sha256"] == signature for r in records)
                          for signature in sorted({r["schema_sha256"] for r in records})},
        "chunks": records,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({k: result[k] for k in (
        "job_scripts", "unique_source_files_in_jobs", "root_chunks_present_at_scan",
        "root_chunks_checked", "valid_chunks", "total_processed_events_in_valid_chunks",
        "total_candidate_bearing_output_events_in_valid_chunks")}, indent=2))
    if errors:
        raise SystemExit(f"{len(errors)} invalid ROOT chunks; inspect {args.output}")


if __name__ == "__main__":
    main()

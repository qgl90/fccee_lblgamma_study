#!/usr/bin/env python3
"""Resume a frozen v3 catalog in disjoint workers, then merge and audit it.

Existing complete candidate pairs can be supplied with --reuse-dir.  A new
catalog snapshot is never edited by this command.  The final parent summary
is rebuilt by prepare_offline_bdt.py from all merged candidate tables.
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path
import shutil

import pyarrow.parquet as pq


def complete_pair(directory, stem):
    paths = [directory / f"{stem}_{kind}.parquet" for kind in ("audit", "selected")]
    if not all(path.is_file() for path in paths):
        return None
    try:
        counts = [pq.read_metadata(path).num_rows for path in paths]
    except Exception:
        return None
    return paths if min(counts) > 0 else None


def run(command, log=None):
    if log is None:
        subprocess.run(command, check=True)
    else:
        with log.open("a") as output:
            subprocess.run(command, stdout=output, stderr=subprocess.STDOUT, check=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--catalog", type=Path, required=True)
    parser.add_argument("--signal", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--reuse-dir", type=Path)
    parser.add_argument("--workers", type=int, default=8)
    args = parser.parse_args()
    if args.workers < 1:
        parser.error("--workers must be positive")
    catalog = json.loads(args.catalog.read_text())
    chunks = catalog["chunks"]
    if not chunks or len({record["chunk_id"] for record in chunks}) != len(chunks):
        parser.error("Catalog must contain distinct chunks")
    root = args.output_dir
    root.mkdir(parents=True, exist_ok=True)
    config = Path("config/lb_offline_selections.json")
    stage1_config = Path("config/lb_reco_preselection_15mev_45_65_3d.json")
    scenario = "lambda12p5_lbE10p5_same_hemi_all"
    script = Path("studies/reconstruction/prepare_offline_bdt.py")
    partition_dir = root / "worker_catalogs"
    partition_dir.mkdir(exist_ok=True)
    assignments = [chunks[i::args.workers] for i in range(args.workers)]
    workers = []
    for index, records in enumerate(assignments):
        worker = root / "workers" / f"part_{index}"
        worker.mkdir(parents=True, exist_ok=True)
        partition = partition_dir / f"part_{index}.json"
        subset = dict(catalog)
        subset["chunks"] = records
        subset["valid_chunks"] = len(records)
        subset["total_processed_events_in_valid_chunks"] = sum(
            item["events_processed"] for item in records)
        subset["total_candidate_bearing_output_events_in_valid_chunks"] = sum(
            item["candidate_bearing_output_events"] for item in records)
        encoded = json.dumps(subset, indent=2) + "\n"
        if partition.exists() and partition.read_text() != encoded:
            raise ValueError(f"Partition already exists with other contents: {partition}")
        partition.write_text(encoded)
        workers.append((worker, partition, records))
    # Only reuse candidate pairs made with precisely the same selection and code.
    if args.reuse_dir:
        import prepare_offline_bdt as preparation
        namespace = argparse.Namespace(signal=args.signal, config=config,
            stage1_config=stage1_config, scenario=scenario, max_output_events=None)
        expected = preparation.preparation_identity(namespace, catalog)
        sources = [args.reuse_dir / "prepared"] + sorted(
            (args.reuse_dir / "workers").glob("part_*"))
        for source in sources:
            identity_path = source / "preparation_identity.json"
            if not identity_path.exists():
                continue
            if json.loads(identity_path.read_text()) != expected:
                raise ValueError(f"Preparation identity differs: {source}")
        for worker, _, _ in workers:
            identity_path = worker / "preparation_identity.json"
            if identity_path.exists() and json.loads(identity_path.read_text()) != expected:
                raise ValueError(f"Worker preparation identity differs: {worker}")
            if not identity_path.exists():
                identity_path.write_text(json.dumps(expected, indent=2) + "\n")
        reused = 0
        for worker, _, records in workers:
            for record in records:
                stem = f"zbb_{record['chunk_id']}"
                if complete_pair(worker, stem):
                    continue
                matches = [complete_pair(source, stem) for source in sources]
                matches = [match for match in matches if match]
                if not matches:
                    continue
                for path in matches[0]:
                    target = worker / path.name
                    if not target.exists():
                        shutil.copy2(path, target)
                reused += 1
        print(f"Seeded {reused} complete Zbb pairs from {args.reuse_dir}", flush=True)
    processes = []
    for worker, partition, _ in workers:
        command = [sys.executable, str(script), "--signal", str(args.signal),
                   "--zbb-catalog", str(partition), "--config", str(config),
                   "--stage1-config", str(stage1_config), "--scenario", scenario,
                   "--output-dir", str(worker), "--resume"]
        log = (worker / "prepare.log").open("a")
        processes.append((subprocess.Popen(command, stdout=log,
                                           stderr=subprocess.STDOUT), log, worker))
    failed = []
    for process, log, worker in processes:
        code = process.wait()
        log.close()
        if code:
            failed.append((str(worker), code))
    if failed:
        raise RuntimeError(f"Preparation workers failed: {failed}")
    prepared = root / "prepared"
    prepared.mkdir(exist_ok=True)
    identity = workers[0][0] / "preparation_identity.json"
    target = prepared / identity.name
    if target.exists() and target.read_bytes() != identity.read_bytes():
        raise ValueError("Parent preparation identity differs")
    if not target.exists():
        shutil.copy2(identity, target)
    run([sys.executable, "studies/reconstruction/merge_parallel_preparation.py",
         "--catalog", str(args.catalog), "--worker-root", str(root / "workers"),
         "--prepared-dir", str(prepared)])
    run([sys.executable, str(script), "--signal", str(args.signal),
         "--zbb-catalog", str(args.catalog), "--config", str(config),
         "--stage1-config", str(stage1_config), "--scenario", scenario,
         "--output-dir", str(prepared), "--resume"], root / "prepare_final.log")
    print(f"Prepared full frozen catalog: {prepared / 'summary.json'}", flush=True)


if __name__ == "__main__":
    main()

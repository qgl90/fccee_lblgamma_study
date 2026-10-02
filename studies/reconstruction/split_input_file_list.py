#!/usr/bin/env python3
"""Generate visible contiguous Zbb batches and runnable job cards.

Each ``file_list_chunkNNN.txt`` contains ROOT inputs. When ``--job-spec-dir``
is supplied, a ``job_NNN.txt`` also records the exact runner arguments and a
``jobs.txt`` lists those cards for Condor queue itemdata.

Full Winter2023 Zbb production example (from the repository root)::

  env -u PYTHONPATH -u PYTHONHOME myenv/bin/python \\
    studies/reconstruction/split_input_file_list.py \\
    --input-list config/zbb_winter2023_full_file_list.txt \\
    --output-dir condor/zbb_winter2023_full/batches \\
    --n-shards 600 \\
    --job-spec-dir condor/zbb_winter2023_full/job_cards \\
    --queue-list condor/zbb_winter2023_full/jobs.txt \\
    --output-root /eos/lhcb/lbdt3/user/rquaglia/fcc_ee/lblgamma/outputs/zbb_full_condor \\
    --ncpus 4 --event-limit all \\
    --reco-config config/lb_reco_preselection_15mev_45_65.json

Inspect ``job_cards/job_000.txt`` and ``batches/file_list_chunk0.txt``. Run one generated
job card locally with ``bash scripts/run_zbb_preselection_shard.sh JOB.txt``;
submit the full Condor queue with ``condor_submit scripts/condor_zbb_full_eos_600.sub``.
For a bounded Condor smoke test, use ``config/zbb_condor_pilot_1file.txt``,
``--n-shards 1``, ``--ncpus 1``, and ``--event-limit 1000``, then submit
``scripts/condor_zbb_full_eos_test.sub``.
"""

import argparse
import hashlib
import json
from pathlib import Path


def read_list(path):
    result = []
    for line in path.read_text().splitlines():
        value = line.strip()
        if value and not value.startswith("#"):
            result.append(value)
    return result


def main():
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--input-list", required=True, type=Path,
                        help="complete ordered source ROOT file manifest")
    parser.add_argument("--output-dir", required=True, type=Path,
                        help="directory for file_list_chunkNNN.txt files")
    parser.add_argument("--n-shards", type=int, default=600)
    parser.add_argument("--job-spec-dir", type=Path,
                        help="also write runnable job_NNN.txt cards here")
    parser.add_argument("--queue-list", type=Path,
                        help="write absolute job-card paths for Condor queue itemdata")
    parser.add_argument("--output-root", type=str,
                        help="job output root, e.g. the EOS campaign directory")
    parser.add_argument("--ncpus", type=int, default=4)
    parser.add_argument("--event-limit", default="all",
                        help="all, or 1..1000 for a smoke test")
    parser.add_argument("--reco-config", type=str,
                        default="config/lb_reco_preselection_15mev_45_65.json")
    args = parser.parse_args()
    if args.n_shards < 1 or args.ncpus < 1:
        parser.error("--n-shards and --ncpus must be positive")
    if args.event_limit != "all":
        try:
            limited_events = int(args.event_limit)
        except ValueError:
            parser.error("--event-limit must be 'all' or an integer from 1 to 1000")
        if not 1 <= limited_events <= 1000:
            parser.error("--event-limit must be 'all' or an integer from 1 to 1000")
    files = read_list(args.input_list)
    if not files:
        parser.error("input list contains no file paths")
    if len(files) < args.n_shards:
        parser.error(f"{len(files)} files cannot populate {args.n_shards} nonempty batches")
    if len(files) != len(set(files)):
        parser.error("input list contains duplicate paths")
    if args.job_spec_dir and not args.output_root:
        parser.error("--output-root is required with --job-spec-dir")

    args.output_dir.mkdir(parents=True, exist_ok=True)
    job_paths = []
    sizes = []
    for batch in range(args.n_shards):
        start = batch * len(files) // args.n_shards
        stop = (batch + 1) * len(files) // args.n_shards
        batch_path = args.output_dir / f"file_list_chunk{batch}.txt"
        batch_files = files[start:stop]
        batch_path.write_text("\n".join(batch_files) + "\n")
        sizes.append(len(batch_files))
        if args.job_spec_dir:
            args.job_spec_dir.mkdir(parents=True, exist_ok=True)
            spec_path = args.job_spec_dir / f"job_{batch:03d}.txt"
            output = f"{args.output_root.rstrip('/')}/shard_{batch:03d}"
            lines = [
                "# Zbb batch job card; run locally with scripts/run_zbb_preselection_shard.sh <this-file>",
                f"batch_index={batch}",
                f"batch_list={batch_path.resolve()}",
                f"source_manifest={args.input_list.resolve()}",
                f"output_dir={output}",
                f"ncpus={args.ncpus}",
                f"event_limit={args.event_limit}",
                f"reco_config={args.reco_config}",
            ]
            spec_path.write_text("\n".join(lines) + "\n")
            job_paths.append(str(spec_path.resolve()))
    if args.queue_list:
        args.queue_list.parent.mkdir(parents=True, exist_ok=True)
        args.queue_list.write_text("\n".join(job_paths) + "\n")
    digest = hashlib.sha256(args.input_list.read_bytes()).hexdigest()
    manifest = {
        "source_manifest": str(args.input_list.resolve()),
        "source_manifest_sha256": digest,
        "source_files": len(files),
        "batches": args.n_shards,
        "files_per_batch_min": min(sizes),
        "files_per_batch_max": max(sizes),
        "batch_lists": [str((args.output_dir / f"file_list_chunk{i}.txt").resolve())
                        for i in range(args.n_shards)],
        "job_cards": job_paths,
        "runner_arguments": {
            "output_root": args.output_root,
            "ncpus": args.ncpus,
            "event_limit": args.event_limit,
            "reco_config": args.reco_config,
        },
    }
    (args.output_dir / "batch_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"Wrote {args.n_shards} batch lists for {len(files)} source files to {args.output_dir}")
    print(f"files per batch: min={min(sizes)}, max={max(sizes)}")
    if job_paths:
        print(f"Wrote {len(job_paths)} runnable job cards; Condor queue list: {args.queue_list}")


if __name__ == "__main__":
    main()

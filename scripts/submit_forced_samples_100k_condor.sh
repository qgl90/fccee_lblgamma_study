#!/usr/bin/env bash
# Generate the queue from config/config.yaml and submit the 100k sample chunks.
set -euo pipefail

usage() {
  cat <<'EOF'
Submit the configured 100k-event forced samples as Condor chunk jobs.

Usage:
  scripts/submit_forced_samples_100k_condor.sh [--dry-run]

The job queue is generated from preselection_generation in config/config.yaml.
The submit description assumes shared repository storage and CVMFS access on
execute nodes. Edit REPO_DIR in scripts/condor_forced_samples_100k.sub first.
After all chunks finish, merge each sample with scripts/merge_chunks.sh.
EOF
}

repo_dir=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
cd "$repo_dir"
dry_run=0
case ${1:-} in
  --help|-h) usage; exit 0 ;;
  --dry-run) dry_run=1 ;;
  "") ;;
  *) usage >&2; exit 2 ;;
esac

queue_file=work/condor/forced_samples_100k.queue
env -u PYTHONPATH -u PYTHONHOME myenv/bin/python \
  scripts/write_forced_samples_100k_queue.py --output "$queue_file"
mkdir -p outputs/logs/condor
if (( dry_run )); then
  printf 'condor_submit %s\n' scripts/condor_forced_samples_100k.sub
  cat "$queue_file"
  exit 0
fi
condor_submit scripts/condor_forced_samples_100k.sub

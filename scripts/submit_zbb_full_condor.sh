#!/usr/bin/env bash
# Validate the generated complete Zbb queue, then submit all 600 Condor jobs.
set -euo pipefail

usage() {
  cat <<'EOF'
Validate and submit the complete Winter2023 Zbb 600-batch Condor campaign.

Usage:
  scripts/submit_zbb_full_condor.sh [--dry-run]

The generated 600 job cards and file lists must already exist under
condor/zbb_winter2023_full. Each job card is queued
by scripts/condor_zbb_full_eos_600.sub and writes to the EOS zbb_full_condor
directory. --dry-run validates the manifest, batches, and cards without
creating EOS directories or submitting jobs.
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
[[ $# -le 1 ]] || { usage >&2; exit 2; }

env -u PYTHONPATH -u PYTHONHOME myenv/bin/python - "$repo_dir" <<'PY'
from pathlib import Path
import sys

repo = Path(sys.argv[1])
manifest_path = repo / "config/zbb_winter2023_full_file_list.txt"
batch_dir = repo / "condor/zbb_winter2023_full/batches"
job_dir = repo / "condor/zbb_winter2023_full/job_cards"
queue_path = repo / "condor/zbb_winter2023_full/jobs.txt"

def entries(path):
    return [line.strip() for line in path.read_text().splitlines()
            if line.strip() and not line.lstrip().startswith("#")]

files = entries(manifest_path)
queue = [line.strip() for line in queue_path.read_text().splitlines()
         if line.strip() and not line.lstrip().startswith("#")]
if len(files) != 4398 or len(files) != len(set(files)):
    raise SystemExit(f"Expected 4,398 unique manifest paths; found {len(files)}")
if len(queue) != 600:
    raise SystemExit(f"Expected 600 queue entries; found {len(queue)}")

offset = 0
sizes = []
for i in range(600):
    chunk = batch_dir / f"file_list_chunk{i}.txt"
    card_path = job_dir / f"job_{i:03d}.txt"
    if not chunk.is_file() or not card_path.is_file():
        raise SystemExit(f"Missing batch or card for index {i}")
    chunk_files = entries(chunk)
    start = i * len(files) // 600
    stop = (i + 1) * len(files) // 600
    if chunk_files != files[start:stop]:
        raise SystemExit(f"Batch {i} differs from the ordered source manifest")
    card = {}
    for line in card_path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        key, sep, value = line.partition("=")
        if not sep or key in card:
            raise SystemExit(f"Malformed or duplicate setting in {card_path}: {line}")
        card[key] = value
    expected = {
        "batch_index": str(i),
        "batch_list": str(chunk.resolve()),
        "source_manifest": str(manifest_path.resolve()),
        "output_dir": f"/eos/lhcb/lbdt3/user/rquaglia/fcc_ee/lblgamma/outputs/zbb_full_condor/shard_{i:03d}",
        "ncpus": "4",
        "event_limit": "all",
        "reco_config": "config/lb_reco_preselection_15mev_45_65.json",
    }
    if card != expected:
        raise SystemExit(f"Settings in {card_path} do not match the full production configuration")
    if queue[i] != str(card_path.resolve()):
        raise SystemExit(f"Queue entry {i} does not point to {card_path}")
    offset += len(chunk_files)
    sizes.append(len(chunk_files))
if offset != len(files):
    raise SystemExit(f"Batches contain {offset} files, expected {len(files)}")
print(f"Validated {len(files)} ordered inputs in 600 batches ({min(sizes)}–{max(sizes)} files/job).")
PY

if (( dry_run )); then
  echo "Dry run: would submit all 600 jobs with scripts/condor_zbb_full_eos_600.sub"
  exit 0
fi

if ! command -v condor_submit >/dev/null 2>&1; then
  echo "condor_submit is not available; load the CERN Condor environment and rerun." >&2
  exit 127
fi

eos_output=/eos/lhcb/lbdt3/user/rquaglia/fcc_ee/lblgamma/outputs/zbb_full_condor
mkdir -p "$eos_output/condor_logs"
condor_submit scripts/condor_zbb_full_eos_600.sub

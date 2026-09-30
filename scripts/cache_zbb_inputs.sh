#!/usr/bin/env bash
# Stage the selected Winter2023 IDEA Zbb files locally for reproducible MT ROOT I/O.
set -euo pipefail
repo_dir=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
cd "$repo_dir"
manifest=${1:-outputs/analysis/studies/Zbb_winter2023_baseline_manifest.files.txt}
cache=${2:-work/cache/winter2023_zbb}
[[ -s "$manifest" ]] || { echo "Missing manifest: $manifest" >&2; exit 1; }
command -v rsync >/dev/null || { echo "rsync is required" >&2; exit 1; }
mkdir -p "$cache"
count=0
while IFS= read -r source_file; do
  [[ -f "$source_file" ]] || { echo "Cannot read $source_file" >&2; exit 1; }
  target="$cache/$(basename "$source_file")"
  echo "Caching $source_file -> $target"
  # EOS files are owned by a different uid/gid; preserve contents and time,
  # but do not attempt to apply their ownership or group to the local copy.
  rsync -t --partial "$source_file" "$target"
  [[ $(stat -c%s "$source_file") == $(stat -c%s "$target") ]] || {
    echo "Size mismatch after copy: $target" >&2; exit 1;
  }
  ((count+=1))
done < "$manifest"
echo "Verified $count local Zbb files in $cache"

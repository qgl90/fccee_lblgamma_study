#!/usr/bin/env bash
set -euo pipefail

repo_dir=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
fcc_dir="$repo_dir/external/FCCAnalyses"
expected_branch=pre-edm4hep1
expected_commit=91c7d6c5a5c8ad5c3848d6d7cf8383e93c9b74e3
cores=${1:-4}

if [[ ! -d "$fcc_dir/.git" ]]; then
    echo "Missing local FCCAnalyses checkout: $fcc_dir" >&2
    exit 1
fi

actual_branch=$(git -C "$fcc_dir" branch --show-current)
actual_commit=$(git -C "$fcc_dir" rev-parse HEAD)
if [[ "$actual_branch" != "$expected_branch" || "$actual_commit" != "$expected_commit" ]]; then
    echo "FCCAnalyses revision mismatch: $actual_branch $actual_commit" >&2
    echo "Expected: $expected_branch $expected_commit" >&2
    exit 1
fi

echo "Building FCCAnalyses from $actual_branch at $actual_commit"
if [[ -n $(git -C "$fcc_dir" status --porcelain) ]]; then
    echo "Local FCCAnalyses source edits are present and will be included in the build."
fi

cd "$fcc_dir"
# The pre-edm4hep1 setup script pins Key4hep 2024-03-10.
set +u
source ./setup.sh
set -u
command -v fccanalysis
fccanalysis build -j "$cores"

mkdir -p "$repo_dir/outputs/build"
{
    printf 'branch=%s\ncommit=%s\nkey4hep_stack=%s\n' \
        "$actual_branch" "$actual_commit" "$KEY4HEP_STACK"
    printf 'tracked_diff_sha256=%s\n' "$(git diff --binary HEAD | sha256sum | cut -d ' ' -f 1)"
    printf 'working_tree_status:\n'
    git status --short
} > "$repo_dir/outputs/build/fccanalyses_revision.txt"
echo "Build manifest: $repo_dir/outputs/build/fccanalyses_revision.txt"

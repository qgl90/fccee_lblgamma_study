#!/usr/bin/env bash
# Check or run the existing merged 100k forced samples through Stage 1 v4.
set -euo pipefail
usage() {
 cat <<'EOF'
Usage: scripts/run_stage1_v4_forced_100k.sh [--check-only|--run]
Default: --check-only. --run uses four independent inputs in parallel.
V4_DIRECT_CPUS=8 and V4_DIRECT_JOBS=4 use 32 cores total by default.
EOF
}
mode=${1:---check-only}
case "$mode" in --check-only|--run) ;; --help|-h) usage; exit 0;; *) usage >&2; exit 2;; esac
repo_dir=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
cd "$repo_dir"
input_eos=/eos/lhcb/lbdt3/user/rquaglia/fcc_ee/lblgamma/outputs
output_dir="$input_eos/stage1_v4_pointing_forced_100k_20261005"
log_dir="$repo_dir/outputs/logs/stage1_v4_pointing_20261005"
config="$repo_dir/config/lb_reco_preselection_15mev_45_65_3d.json"
mode_names=(signal_phsp signal_physics lbgamma_eta lbgamma_eta_physics lbgamma_pi0 lbgamma_pi0_phsp)
input_paths=(
 "$input_eos/Lb2LambdaGamma_nev100000_IDEA_edm4hep.root"
 "$input_eos/Lb2LambdaGammaPhysics_nev100000_IDEA_edm4hep.root"
 "$input_eos/Lb2LambdaEta_nev100000_IDEA_edm4hep.root"
 "$input_eos/stage0_v3_pseudoscalar_physics_100k_20261004/Lb2LambdaEtaPhysics_nev100000_IDEA_edm4hep.root"
 "$input_eos/stage0_v3_pseudoscalar_physics_100k_20261004/Lb2LambdaPi0Physics_nev100000_IDEA_edm4hep.root"
 "$repo_dir/outputs/delphes/Lb2LambdaPi0_nev100000_IDEA_edm4hep.root"
)
cpus=${V4_DIRECT_CPUS:-8}; jobs=${V4_DIRECT_JOBS:-4}
[[ "$cpus" =~ ^[1-9][0-9]*$ && "$jobs" =~ ^[1-9][0-9]*$ ]] || { echo "V4_DIRECT_CPUS/JOBS must be positive integers" >&2; exit 2; }
(( cpus*jobs <= 32 )) || { echo "V4_DIRECT_CPUS * V4_DIRECT_JOBS must not exceed the 32-core default allocation" >&2; exit 2; }
ready=(); missing=0
for i in "${!mode_names[@]}"; do
 sample=${mode_names[i]}; input=${input_paths[i]}; output="$output_dir/${sample}_stage1_v4.root"
 if [[ ! -s "$input" ]]; then echo "MISSING input: $sample -> $input" >&2; missing=$((missing+1)); continue; fi
 if [[ -e "$output" ]]; then echo "EXISTS output: $output" >&2; if [[ "$mode" == --run ]]; then exit 1; fi; continue; fi
 echo "READY $sample input=$input output=$output cpus=$cpus"
 ready+=("$i")
done
if [[ "$mode" == --check-only ]]; then
 echo "parallel_jobs=$jobs total_cpus=$((jobs*cpus)) missing_100k_inputs=$missing"
 exit 0
fi
mkdir -p "$log_dir"
run_one() {
 local idx=$1 sample=${mode_names[$1]} input=${input_paths[$1]}
 local output="$output_dir/${mode_names[$1]}_stage1_v4.root"
 LB_RECO_ANALYSIS=analysis/studies/lb2lambda_gamma_reco_v4.py \
  scripts/run_reco_preselection.sh "$sample" "$input" "$output" all "$config" "$cpus"
 env -u PYTHONPATH -u PYTHONHOME myenv/bin/python \
  studies/resolutions/validate_stage1_v4_tuple.py --input "$output" \
  --output "${output%.root}_validation.json"
}
failed=0
for ((start=0; start<${#ready[@]}; start+=jobs)); do
 pids=()
 for ((offset=0; offset<jobs && start+offset<${#ready[@]}; offset++)); do
  idx=${ready[start+offset]}; sample=${mode_names[idx]}
  run_one "$idx" > "$log_dir/${sample}.log" 2>&1 &
  pids+=("$!")
 done
 for pid in "${pids[@]}"; do if ! wait "$pid"; then failed=1; fi; done
done
(( failed == 0 )) || { echo "One or more Stage 1 v4 jobs failed; inspect $log_dir" >&2; exit 1; }
echo "Completed and validated ${#ready[@]} available samples; missing_100k_inputs=$missing; logs=$log_dir"

"""FCCAnalyses processList for selected v5 forced-decay signal chunks."""

import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
os.environ.setdefault("LB_RECO_CONFIG", str(REPO_ROOT / "config/lb_reco_v5_training.json"))
os.environ.setdefault("LB_STAGE1_OUTPUT_DIR", "outputs/analysis/studies")

from lb2lambda_gamma_reco_v5 import RDFanalysis, includePaths as reco_include_paths

analysisName = "lb2lambda_gamma_reco_v5_forced_1m"
inputDir = None
prodTag = None
outputDir = os.environ["LB_STAGE1_OUTPUT_DIR"]
outputDirEos = os.environ.get("LB_STAGE1_OUTPUT_EOS", "")
eosType = "eoslhcb"
nCPUS = int(os.environ.get("LB_STAGE1_NCPUS", "4"))
runBatch = os.environ.get("LB_STAGE1_EXECUTOR", "local") == "condor"
includePaths = reco_include_paths
batchQueue = os.environ.get("LB_STAGE1_QUEUE", "workday")
compGroup = os.environ.get("LB_STAGE1_ACCOUNTING_GROUP", "group_u_FCC.local_gen")

input_dir = Path(os.environ.get("LB_STAGE1_INPUT_DIR", "."))
sample_names = {
    "Lb2LambdaGamma": "phase-space Λb→Λγ",
    "Lb2LambdaGammaPhysics": "HELAMP Physics Λb→Λγ",
    "Lb2LambdaEtaPhysics": "HELAMP Physics Λb→Λη",
    "Lb2LambdaPi0Physics": "HELAMP Physics Λb→Λπ⁰",
}
samples = [value for value in os.environ.get(
    "LB_STAGE1_SAMPLES", "Lb2LambdaGammaPhysics").split(",") if value]
unknown_samples = sorted(set(samples) - set(sample_names))
if unknown_samples:
    raise ValueError(f"Unsupported v5 forced samples: {unknown_samples}")
chunk_list = os.environ.get("LB_STAGE1_CHUNKS", "")
chunk_ids = [int(value) for value in chunk_list.split(",") if value]
if runBatch:
    outputDir = "."
processList = {}
for sample in samples:
    for chunk_id in chunk_ids:
        input_name = f"{sample}_nev1000000_chunk{chunk_id}_IDEA_edm4hep"
        processList[input_name] = {
            "inputDir": str(input_dir),
            "output": f"{sample}_nev1000000_chunk{chunk_id}_stage1_v5",
            "chunks": 1,
        }

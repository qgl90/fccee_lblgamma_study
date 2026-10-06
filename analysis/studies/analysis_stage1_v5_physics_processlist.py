"""FCCAnalyses processList entry point for selected generated signal chunks."""

import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
os.environ.setdefault("LB_RECO_CONFIG", str(REPO_ROOT / "config/lb_reco_v5_training.json"))
os.environ.setdefault("LB_STAGE1_OUTPUT_DIR", "outputs/analysis/studies")

from lb2lambda_gamma_reco_v5 import RDFanalysis, includePaths as reco_include_paths

analysisName = "lb2lambda_gamma_reco_v5_physics_1m"
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
sample = "Lb2LambdaGammaPhysics_nev1000000"
chunk_list = os.environ.get("LB_STAGE1_CHUNKS", "")
chunk_ids = [int(value) for value in chunk_list.split(",") if value]
if runBatch:
    outputDir = "."
processList = {}
for chunk_id in chunk_ids:
    input_name = f"{sample}_chunk{chunk_id}_IDEA_edm4hep"
    processList[input_name] = {
        "inputDir": str(input_dir),
        "output": f"{sample}_chunk{chunk_id}_stage1_v5",
        "chunks": 1,
    }

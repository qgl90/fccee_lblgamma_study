"""Native Condor dispatch for the v5 flavour-tagging Stage-1 tuples."""

import sys
from pathlib import Path
import os

sys.path.insert(0, str(Path(__file__).resolve().parent))

# The base Condor dispatcher resolves the reconstruction config at import
# time, and lb2lambda_gamma_reco_v5 imports the same setting for its C++
# builder expression. Keep the v5 selection as the default on submit and
# worker processes while still allowing an explicit scenario override.
REPO_ROOT = Path(__file__).resolve().parents[2]
os.environ.setdefault(
    "LB_RECO_CONFIG", str(REPO_ROOT / "config/lb_reco_v5_training.json"))

import analysis_preselection_zbb as batch
from lb2lambda_gamma_reco_v5 import RDFanalysis as _v5_RDFanalysis

batch._RDFanalysis = _v5_RDFanalysis
batch.include_paths = batch.include_paths + [
    "photon_pointing_v4.h", "flavour_tagging_v5.h"]
batch.DEFAULT_OUTPUT_EOS = (
    "/eos/lhcb/lbdt3/user/rquaglia/fcc_ee/lblgamma/outputs/"
    "zbb_full_condor/stage1_v5_flavtag")


class Analysis(batch.Analysis):
    def __init__(self, cmdline_args):
        opts, _ = batch.parse_sample_args(cmdline_args)
        if "stage1_v5" not in opts.output_eos:
            raise ValueError("v5 production requires an output-eos containing stage1_v5")
        super().__init__(cmdline_args)
        self.output_dir = f"outputs/{self.sample_name}_stage1_v5_flavtag_work"

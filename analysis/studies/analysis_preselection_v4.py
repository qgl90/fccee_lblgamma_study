"""Native Zbb/Zcc/Zss dispatch with the v4 photon diagnostics."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import analysis_preselection_zbb as batch
from lb2lambda_gamma_reco_v4 import RDFanalysis
batch._RDFanalysis = RDFanalysis
batch.include_paths = batch.include_paths + ["photon_pointing_v4.h"]
batch.DEFAULT_OUTPUT_EOS = batch.DEFAULT_OUTPUT_EOS.replace("_v3", "_v4")
class Analysis(batch.Analysis):
    def __init__(self, cmdline_args):
        opts, _ = batch.parse_sample_args(cmdline_args)
        if "v4" not in opts.output_eos:
            raise ValueError("v4 production requires a distinct output-eos containing v4")
        super().__init__(cmdline_args)
        self.output_dir = f"outputs/{self.sample_name}_stage1_v4_work"

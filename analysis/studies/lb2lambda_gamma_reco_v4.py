"""v4: unchanged v3 candidate selection, extended offline pointing inputs."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from lb2lambda_gamma_reco import *
from lb2lambda_gamma_reco import RDFanalysis as V3
from photon_pointing_stage1 import attach, BRANCHES
analysisName = "lb2lambda_gamma_reco_v4"
includePaths = includePaths + ["photon_pointing_v4.h"]
class RDFanalysis:
    @staticmethod
    def analysers(df):
        return attach(V3.analysers(df))
    @staticmethod
    def output():
        return V3.output() + list(BRANCHES)

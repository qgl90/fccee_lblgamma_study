"""v5: v4 candidate selection plus reconstructed-PV Weaver jet-tag outputs."""

import sys
from pathlib import Path
import os

sys.path.insert(0, str(Path(__file__).resolve().parent))

from lb2lambda_gamma_reco_v4 import RDFanalysis as V4
from lb2lambda_gamma_reco_v4 import includePaths as V4_INCLUDE_PATHS
from lb2lambda_gamma_reco import build_dataframe, CPP_CONFIG
from observables_stage1 import attach as attach_observables
from photon_pointing_stage1 import attach as attach_pointing
from flavour_tagging_v5 import attach as attach_flavour_tagging
from flavour_tagging_v5 import output_branches as flavour_tagging_branches

analysisName = "lb2lambda_gamma_reco_v5"
outputDir = os.environ.get("LB_STAGE1_OUTPUT_DIR", "outputs/analysis/studies")
nCPUS = 4
includePaths = list(V4_INCLUDE_PATHS) + ["flavour_tagging_v5.h"]
MIN_LB_ENERGY_GEV = float(os.environ.get("LB_V5_MIN_LB_ENERGY_GEV", "10.5"))
_ENERGY_BRANCH = "flavtag_v5_n_candidate_energy_pass"


class RDFanalysis:
    @staticmethod
    def analysers(df):
        # Match v4 exactly through candidate building. Apply the known
        # training energy gate before truth labels and offline observables.
        df = build_dataframe(
            df, CPP_CONFIG, with_vertices=True, filter_min_photons=1,
            filter_empty_candidates=True,
            filter_min_lb_energy_gev=MIN_LB_ENERGY_GEV)
        df = attach_observables(df)
        df = attach_pointing(df)
        return attach_flavour_tagging(df)

    @staticmethod
    def output():
        return list(dict.fromkeys(
            V4.output() + [_ENERGY_BRANCH] + flavour_tagging_branches()))

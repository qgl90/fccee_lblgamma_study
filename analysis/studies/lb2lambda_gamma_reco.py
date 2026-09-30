"""
Author: Renato Quagliani (rquaglia@cern.ch), main stage-1 analysis for 
Lambda_b -> Lambda0(p pi) gamma reconstruction chain.

Configured Lambda_b -> Lambda0(p pi) gamma reconstruction.

For each opposite-sign pair, 
1. fit the two-track vertex once and use the fitted
momenta for both p+ pi- and anti-p- pi+ mass assignments. 
2. Require the configured track and vertex displacement/quality, apply the broad Lambda0 mass window,
then choose the surviving assignment closest in absolute mass difference to
the Lambda0 reference. 
3. Combine it with selected IDEA photons and retain
Lambda_b masses in the configured fit interval and thrust hemisphere. 
4. The same script is run on Eta-generated events as a one-photon reconstruction to
measure the partially reconstructed shape. MC truth only labels output.

The JSON file is an analysis-selection configuration. Detector-response
variations belong to a separately versioned Delphes card and EDM4hep input.

The code imports the baseline candidate dataframe and adds the stage-1 observables.
The code is configured to run on a single file at a time, and the Snakefile or condor execution expects 
to run it in parallel over all input files.

See lb2lambda_gamma_baseline for the baseline candidate dataframe and Gamma reconstruction inputs in 
analysis/studies folder
"""

import json
import math
import os
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lb2lambda_gamma_baseline import (build_dataframe, RDFanalysis as Baseline,
                                     _INPUT)
from observables_stage1 import attach as attach_observables, BRANCHES as OBS_BRANCHES


processList = {}
analysisName = "lb2lambda_gamma_reco"
outputDir = "outputs/analysis/studies"
nCPUS = 4
includePaths = ["lb_event_selection.h", "lb_candidate_builder.h",
                "lb_candidate_truth.h", "lb_candidate_observables.h"]

CONFIG_PATH = Path(os.environ.get(
    "LB_RECO_CONFIG",
    Path(__file__).resolve().parents[2] / "config" / "lb_reco.json"))
CONFIG = json.loads(CONFIG_PATH.read_text())
# Keep this positional mapping synchronized with LbCandidateBuilder::Config.
# A changed threshold requires a new output name and a paired baseline run;
# the charge-separated signal cutflow uses the same cpp_config() expression.
TARGET = float(CONFIG["lambda_mass_gev"])
MASS_MIN = float(CONFIG["lambda_mass_min_gev"])
MASS_MAX = float(CONFIG["lambda_mass_max_gev"])
PRESELECT_MASS_MIN = float(CONFIG.get("candidate_lambda_mass_min_gev", -1.))
PRESELECT_MASS_MAX = float(CONFIG.get("candidate_lambda_mass_max_gev", -1.))
CHOOSE_CLOSEST = CONFIG["choose_closest_mass_hypothesis"]
MAX_CHI2 = float(CONFIG["vertex_max_chi2"])
MIN_RXY = float(CONFIG["min_flight_rxy_mm"])
MIN_TRACK_SIG = float(CONFIG["min_track_d0sig"])
MIN_VERTEX_SIG = float(CONFIG["min_vertex_flight_sig"])
REQUIRE_VERTEX = CONFIG["require_good_vertex"]
LB_MASS_MIN = float(CONFIG["lb_mass_min_gev"])
LB_MASS_MAX = float(CONFIG["lb_mass_max_gev"])
REQUIRE_SAME_HEMISPHERE = CONFIG["require_same_hemisphere"]
RAW_MASS_PREFILTER_HALF_WINDOW = float(
    CONFIG.get("raw_mass_prefilter_half_window_gev", -1.))
if not (math.isfinite(TARGET) and MASS_MIN <= TARGET <= MASS_MAX and
        math.isfinite(MASS_MIN) and math.isfinite(MASS_MAX) and
        0 < MASS_MIN < MASS_MAX and math.isfinite(MAX_CHI2) and MAX_CHI2 > 0 and
        math.isfinite(PRESELECT_MASS_MIN) and math.isfinite(PRESELECT_MASS_MAX) and
        ((PRESELECT_MASS_MIN < 0. and PRESELECT_MASS_MAX < 0.) or
         (0 < PRESELECT_MASS_MIN < PRESELECT_MASS_MAX and
          PRESELECT_MASS_MIN >= MASS_MIN and PRESELECT_MASS_MAX <= MASS_MAX)) and
        math.isfinite(MIN_RXY) and MIN_RXY >= 0 and
        math.isfinite(MIN_TRACK_SIG) and MIN_TRACK_SIG >= 0 and
        math.isfinite(MIN_VERTEX_SIG) and MIN_VERTEX_SIG >= 0 and
        math.isfinite(RAW_MASS_PREFILTER_HALF_WINDOW) and
        math.isfinite(LB_MASS_MIN) and math.isfinite(LB_MASS_MAX) and
        0 < LB_MASS_MIN < LB_MASS_MAX and
        isinstance(CHOOSE_CLOSEST, bool) and isinstance(REQUIRE_VERTEX, bool) and
        isinstance(REQUIRE_SAME_HEMISPHERE, bool)):
    raise ValueError(f"Invalid Lambda0 reconstruction config: {CONFIG_PATH}")


def cpp_config(neutral_pdg=22, neutral_min=-1., neutral_max=-1.):
    """Build one validated C++ config expression for either neutral mode."""
    return ("FCCAnalyses::LbCandidateBuilder::Config{"
            f"{TARGET!r}, {MASS_MIN!r}, {MASS_MAX!r}, "
            f"{PRESELECT_MASS_MIN!r}, {PRESELECT_MASS_MAX!r}, "
            f"{'true' if CHOOSE_CLOSEST else 'false'}, "
            f"{MAX_CHI2!r}, {MIN_RXY!r}, {MIN_TRACK_SIG!r}, "
            f"{MIN_VERTEX_SIG!r}, "
            f"{'true' if REQUIRE_VERTEX else 'false'}, "
            f"{neutral_pdg!r}, {neutral_min!r}, {neutral_max!r}, "
            f"{LB_MASS_MIN!r}, {LB_MASS_MAX!r}, "
            f"{'true' if REQUIRE_SAME_HEMISPHERE else 'false'}, "
            f"{RAW_MASS_PREFILTER_HALF_WINDOW!r}" + "}")


CPP_CONFIG = cpp_config()


class RDFanalysis:
    @staticmethod
    def analysers(df):
        df = build_dataframe(df, CPP_CONFIG, with_vertices=True,
                             filter_min_photons=1,
                             filter_empty_candidates=True)
        return attach_observables(df)

    @staticmethod
    def output():
        return Baseline.output() + _INPUT + list(OBS_BRANCHES)

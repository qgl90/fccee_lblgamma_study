# Author: Renato Quagliani (rquaglia@cern.ch)
"""Diagnostic full Lambda_b -> Lambda0(p pi) eta(gamma gamma) reconstruction.

Uses the same charged Lambda0 selection and central VertexFitterSimple path
as lb2lambda_gamma_reco.py. Photon pairs are unordered and pass a configurable
broad eta mass interval; no MC information enters the candidate builder.
For the Eta background under the signal hypothesis, instead run
lb2lambda_gamma_reco.py on the Eta-generated EDM4hep sample.
"""

import json
import math
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lb2lambda_gamma_baseline import (build_dataframe, RDFanalysis as Baseline,
                                     _INPUT)
from lb2lambda_gamma_reco import cpp_config


processList = {}
analysisName = "lb2lambda_eta_reco"
outputDir = "outputs/analysis/studies"
nCPUS = 4
includePaths = ["lb_event_selection.h", "lb_candidate_builder.h",
                "lb_candidate_truth.h"]

CONFIG_PATH = Path(__file__).resolve().parents[2] / "config" / "lb_reco_eta.json"
CONFIG = json.loads(CONFIG_PATH.read_text())
MASS_MIN = float(CONFIG["eta_mass_min_gev"])
MASS_MAX = float(CONFIG["eta_mass_max_gev"])
if not (math.isfinite(MASS_MIN) and math.isfinite(MASS_MAX) and
        0 <= MASS_MIN < MASS_MAX):
    raise ValueError(f"Invalid eta reconstruction config: {CONFIG_PATH}")

CPP_CONFIG = cpp_config(neutral_pdg=221, neutral_min=MASS_MIN,
                        neutral_max=MASS_MAX)


class RDFanalysis:
    @staticmethod
    def analysers(df):
        return build_dataframe(df, CPP_CONFIG, with_vertices=True,
                               filter_min_photons=2)

    @staticmethod
    def output():
        return Baseline.output() + _INPUT

# Author: Renato Quagliani (rquaglia@cern.ch)
"""v5 truth-diagnostic event cutflow for the Gamma reconstruction.

v5 variant of lb2lambda_gamma_cutflow.py using lb_signal_cutflow_v5.h and, by
default, config/lb_reco_v5_training.json plus the E(Lambda_b) >= 10.5 GeV
offline candidate cut (LB_V5_MIN_LB_ENERGY_GEV).
Run with fccanalysis run and --nevents 1000 on the Gamma signal EDM4hep file.
Every input event is retained. The truth association is read only by the
diagnostic helper and never changes the production candidate selection.
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
os.environ.setdefault("LB_RECO_CONFIG", str(
    Path(__file__).resolve().parents[2] / "config/lb_reco_v5_training.json"))
from lb2lambda_gamma_reco import CPP_CONFIG
MIN_LB_ENERGY_GEV = float(os.environ.get("LB_V5_MIN_LB_ENERGY_GEV", "10.5"))


processList = {}
analysisName = "lb2lambda_gamma_cutflow_v5"
outputDir = "outputs/analysis/studies"
nCPUS = 1
includePaths = [
    "lb_event_selection.h", "lb_candidate_builder.h",
    "lb_candidate_truth.h", "lb_signal_cutflow_v5.h",
]

STAGES = [
    "raw_truth_candidate", "selected_photon", "valid_pv", "event_tracks",
    "nonprimary_tracks", "daughter_d0", "vertex_fit_valid",
    "vertex_chi2", "flight_distance", "flight_significance",
    "lambda_mass_window", "closest_mass_hypothesis",
    "candidate_lambda_window", "lb_mass_window", "same_hemisphere", "lb_energy",
]


class RDFanalysis:
    @staticmethod
    def analysers(df):
        df = (df.Alias("SelectedPhotonIndices", "Photon#0.index")
                .Alias("AssocReco", "MCRecoAssociations#0.index")
                .Alias("AssocMC", "MCRecoAssociations#1.index")
                .Alias("MCParents", "Particle#0.index")
                .Define("event_entry", "static_cast<unsigned long long>(rdfentry_)")
                .Define("PrimaryTracks",
                        "VertexFitterSimple::get_PrimaryTracks("
                        "EFlowTrack_1, true, 4.5, 20e-3, 300, 0., 0., 0.)")
                .Define("PrimaryVertexObject",
                        "VertexFitterSimple::VertexFitter_Tk("
                        "1, PrimaryTracks, true, 4.5, 20e-3, 300, "
                        "0., 0., 0., false)")
                .Define("PrimaryTrackMask",
                        "VertexFitterSimple::IsPrimary_forTracks("
                        "EFlowTrack_1, PrimaryTracks)")
                .Define("EventThrust",
                        "Algorithms::calculate_thrust()("
                        "ReconstructedParticle::get_px(ReconstructedParticles), "
                        "ReconstructedParticle::get_py(ReconstructedParticles), "
                        "ReconstructedParticle::get_pz(ReconstructedParticles))")
                )
        call = ("FCCAnalyses::LbSignalCutflowV5::evaluate("
                "ReconstructedParticles, EFlowTrack_1, "
                "PrimaryVertexObject, PrimaryTrackMask, "
                "SelectedPhotonIndices, EventThrust, Particle, "
                "AssocReco, AssocMC, MCParents, " + CPP_CONFIG +
                f", {MIN_LB_ENERGY_GEV!r}")
        df = (df.Define("signal_cutflow", call + ")")
                .Define("positive_cutflow", call + ", 1)")
                .Define("negative_cutflow", call + ", -1)"))
        for name in STAGES:
            df = df.Define(name, "signal_cutflow." + name)
            df = df.Define("positive_" + name, "positive_cutflow." + name)
            df = df.Define("negative_" + name, "negative_cutflow." + name)
        df = df.Define("fitted_lambda_mass", "signal_cutflow.fitted_lambda_mass")
        df = df.Define("true_vertex_chi2", "signal_cutflow.true_vertex_chi2")
        df = df.Define("positive_true_vertex_chi2",
                       "positive_cutflow.true_vertex_chi2")
        df = df.Define("negative_true_vertex_chi2",
                       "negative_cutflow.true_vertex_chi2")
        return df

    @staticmethod
    def output():
        return (["event_entry", "fitted_lambda_mass", "true_vertex_chi2",
                 "positive_true_vertex_chi2", "negative_true_vertex_chi2"] + STAGES +
                ["positive_" + name for name in STAGES] +
                ["negative_" + name for name in STAGES])

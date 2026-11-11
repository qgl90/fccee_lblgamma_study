# Author: Renato Quagliani (rquaglia@cern.ch)
"""Event-wide charged-particle and photon truth/reco response ntuple.

Run with fccanalysis run and --files-list; no Lambda_b decay selection is made.
"""

processList = {}
analysisName = "delphes_resolutions"
outputDir = "outputs/analysis/studies"
nCPUS = 4
includePaths = ["resolutions.h"]

_SCALARS = [
    "n_reco_track_candidates", "n_reco_photon_candidates", "n_selected_photons",
]
_TRACK = [
    "track_mc_index", "track_pdg", "track_reco_index", "track_n_links",
    "track_matched", "track_truth_charge", "track_truth_p", "track_truth_pt",
    "track_truth_eta", "track_truth_rxy", "track_reco_charge", "track_reco_p", "track_reco_pt",
    "track_reco_eta", "track_dp_rel", "track_dpt_rel", "track_dqoverpt",
]
_GAMMA = [
    "gamma_mc_index", "gamma_reco_index", "gamma_n_links", "gamma_matched",
    "gamma_selected", "gamma_signal", "gamma_truth_e", "gamma_truth_pt", "gamma_truth_eta",
    "gamma_truth_phi", "gamma_reco_e", "gamma_reco_pt", "gamma_reco_eta",
    "gamma_reco_phi", "gamma_dE_rel",
]
_COLUMNS = ["event_entry"] + _SCALARS + _TRACK + _GAMMA


class RDFanalysis:
    @staticmethod
    def analysers(df):
        df = (
            df.Alias("AssocReco", "MCRecoAssociations#0.index")
              .Alias("AssocMC", "MCRecoAssociations#1.index")
              .Alias("SelectedPhoton", "Photon#0.index")
              .Alias("MCDaughters", "Particle#1.index")
              .Define("event_entry", "static_cast<unsigned long long>(rdfentry_)")
              .Define("resolution", "FCCAnalyses::ResolutionStudy::make("
                      "Particle, ReconstructedParticles, AssocReco, AssocMC, "
                      "SelectedPhoton, MCDaughters)")
        )
        for name in _SCALARS + _TRACK + _GAMMA:
            df = df.Define(name, f"resolution.{name}")
        return df

    @staticmethod
    def output():
        return _COLUMNS

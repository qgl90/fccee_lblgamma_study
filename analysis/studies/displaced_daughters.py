# Author: Renato Quagliani (rquaglia@cern.ch)
"""Direct Lambda0/K0S proton and pion daughters: truth, reco match, origin."""

processList = {}
analysisName = "delphes_displaced_daughters"
outputDir = "outputs/analysis/studies"
nCPUS = 4
includePaths = ["displaced_daughters.h"]

_FIELDS = [
    "mc_index", "parent_pdg", "pdg", "matched", "n_links", "reco_index",
    "truth_p", "truth_pt", "truth_eta", "truth_phi",
    "vertex_x", "vertex_y", "vertex_z", "vertex_rxy",
    "reco_p", "reco_pt", "reco_eta", "dp_rel", "dpt_rel", "dqoverpt",
]


class RDFanalysis:
    @staticmethod
    def analysers(df):
        df = (df.Alias("AssocReco", "MCRecoAssociations#0.index")
                .Alias("AssocMC", "MCRecoAssociations#1.index")
                .Alias("MCParents", "Particle#0.index")
                .Define("event_entry", "static_cast<unsigned long long>(rdfentry_)")
                .Define("daughter_study",
                        "FCCAnalyses::DisplacedDaughters::make("
                        "Particle, ReconstructedParticles, AssocReco, AssocMC, MCParents)"))
        for name in _FIELDS:
            df = df.Define("daughter_" + name, "daughter_study." + name)
        return df

    @staticmethod
    def output():
        return ["event_entry"] + ["daughter_" + name for name in _FIELDS]

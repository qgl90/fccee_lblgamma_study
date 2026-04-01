from __future__ import annotations

# Minimal FCCAnalyses treemaker for:
#   Lambda_b0 -> Lambda0(p pi) gamma
#
# Strategy:
# - Find truth decay products (stable final state) with MCParticle::get_indices
# - Match those MC particles to reco objects using MCRecoAssociations
# - Store a few sanity-check kinematics and reconstructed invariant masses

import ROOT
import os


# -----------------------------------------------------------------------------
# FCCAnalyses steering knobs (kept for compatibility with common examples)

processList = {"Lb2LambdaGamma": {"fraction": 1.0}}
analysisName = "Lb2LambdaGamma"
outputDir = "outputs/analysis"
nCPUS = 4
runBatch = False
batchQueue = "longlunch"


class RDFanalysis:
    @staticmethod
    def analysers(df):
        pdg_mother = int(os.getenv("FCC_SIG_PDG_MOTHER", "5122"))
        daughters_env = os.getenv("FCC_SIG_PDG_DAUGHTERS", "2212,-211,22")
        pdg_daughters = [int(x.strip()) for x in daughters_env.split(",") if x.strip()]
        pdg_daughters_cpp = "{" + ", ".join(str(x) for x in pdg_daughters) + "}"

        # Standard aliases used across FCCAnalyses examples/tutorials
        df = df.Alias("Particle0", "Particle#0.index")
        df = df.Alias("Particle1", "Particle#1.index")
        df = df.Alias("MCRecoAssociations0", "MCRecoAssociations#0.index")
        df = df.Alias("MCRecoAssociations1", "MCRecoAssociations#1.index")

        # -----------------------------------------------------------------------------
        # Truth decay selection:
        # pick stable daughters: p, pi, gamma from Lb decay tree.
        # charge conjugation enabled to catch anti-Lb as well.
        #
        # Note: get_indices can return multiple candidates; we keep the first triplet.
        df = df.Define(
            "Lb_truth_idx_all",
            f"MCParticle::get_indices({pdg_mother}, {pdg_daughters_cpp}, true, true, true, true)(Particle, Particle1)",
        )
        df = df.Filter("Lb_truth_idx_all.size() >= 3")
        df = df.Define("Lb_truth_idx", "ROOT::VecOps::Take(Lb_truth_idx_all, 3)")

        # -----------------------------------------------------------------------------
        # Truth-seeded reco matching (avoids combinatorics for the first iteration)
        df = df.Define(
            "LbRecoParts",
            "ReconstructedParticle2MC::selRP_matched_to_list(Lb_truth_idx, MCRecoAssociations0, MCRecoAssociations1, ReconstructedParticles, Particle)",
        )
        df = df.Filter("LbRecoParts.size() == 3")

        # -----------------------------------------------------------------------------
        # Reco kinematics and masses
        df = df.Define("p_tlv", "ReconstructedParticle::get_tlv(LbRecoParts, 0)")
        df = df.Define("pi_tlv", "ReconstructedParticle::get_tlv(LbRecoParts, 1)")
        df = df.Define("g_tlv", "ReconstructedParticle::get_tlv(LbRecoParts, 2)")

        df = df.Define("lambda0_reco_m", "(p_tlv + pi_tlv).M()")
        df = df.Define("lb_reco_m", "(p_tlv + pi_tlv + g_tlv).M()")

        df = df.Define("p_reco_p", "p_tlv.P()")
        df = df.Define("pi_reco_p", "pi_tlv.P()")
        df = df.Define("g_reco_e", "g_tlv.E()")

        return df

    @staticmethod
    def output():
        return [
            "lambda0_reco_m",
            "lb_reco_m",
            "p_reco_p",
            "pi_reco_p",
            "g_reco_e",
        ]

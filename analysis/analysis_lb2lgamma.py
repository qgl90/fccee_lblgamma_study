from __future__ import annotations

# Minimal FCCAnalyses treemaker for:
#   Lambda_b0 -> Lambda0(p pi) gamma
#
# Strategy:
# - Find truth decay products (stable final state) with MCParticle::get_indices
# - Store a few sanity-check kinematics for the selected truth particles

import logging
from os import getenv

import ROOT

# -----------------------------------------------------------------------------
# FCCAnalyses steering knobs (kept for compatibility with common examples)

processList = {"Lb2LambdaGamma": {"fraction": 1.0}}
analysisName = "Lb2LambdaGamma"
outputDir = "outputs/analysis"
nCPUS = 4
runBatch = False
batchQueue = "longlunch"

inputDir = (
    "/afs/cern.ch/user/r/rquaglia/work/fcc_ee/fccee_lblgamma_study/outputs/delphes/"
)
procDict = "FCCee_procDict_winter2023_IDEA.json"


FCC_LB_DEBUG = getenv("FCC_LB_DEBUG", "").lower() in {"1", "true", "yes", "on"}


def _debug(message: str) -> None:
    if FCC_LB_DEBUG:
        logging.getLogger(__name__).info(message)


ROOT.gInterpreter.Declare("""
using namespace FCCAnalyses;
using namespace FCCAnalyses::MCParticle;

// return one MC leg corresponding to the Lambda_b decay
// note: the size of the vector is always zero or one. I return a ROOT::VecOps::RVec for convenience
struct selMC_leg{
  selMC_leg( int idx );
  int m_idx;
  ROOT::VecOps::RVec<edm4hep::MCParticleData> operator() (ROOT::VecOps::RVec<int> list_of_indices,
							  ROOT::VecOps::RVec<edm4hep::MCParticleData> in) ;
};


// To retrieve a given MC leg corresponding to the Lambda_b decay
selMC_leg::selMC_leg( int idx ) {
  m_idx = idx;
};

// I return a vector instead of a single particle :
//   - such that the vector is empty when there is no such decay mode (instead
//     of returning a dummy particle)
//   - such that I can use the getMC_theta etc functions, which work with a
//     ROOT::VecOps::RVec of particles, and not a single particle

ROOT::VecOps::RVec<edm4hep::MCParticleData> selMC_leg::operator() ( ROOT::VecOps::RVec<int> list_of_indices,  ROOT::VecOps::RVec<edm4hep::MCParticleData> in) {
  ROOT::VecOps::RVec<edm4hep::MCParticleData>  res;
  if ( list_of_indices.size() == 0) return res;
  if ( m_idx < list_of_indices.size() ) {
	res.push_back( sel_byIndex( list_of_indices[m_idx], in ) );
	return res;
  }
  return res;
}
""")


class RDFanalysis:
    @staticmethod
    def analysers(df):
        # Lb -> Lambda0( p pi) gamma
        pdg_mother = ["5122", "-5122"]  # Lambda_b, anti-Lambda_b
        pdg_daughters = ["2212,-211,22", "-2212,211,22"]  # p pi gamma
        lb_pdg_daughters_cpp = [
            "{" + ", ".join(str(x) for x in daughters.split(",")) + "}"
            for daughters in pdg_daughters
        ]
        _debug(f"PDG mothers: {pdg_mother}")
        _debug(f"PDG daughter lists: {lb_pdg_daughters_cpp}")

        dfProcessed = (
            #############################################
            ##          Aliases for # in python        ##
            #############################################
            df
            # .Alias("Particle0", "Particle#0.index")
            .Alias("Particle1", "Particle#1.index")
            # Extract Lb    , p+  pi- gamma indices for Lb
            .Define(
                "LbToPPiGamma_indices",
                f"FCCAnalyses::MCParticle::get_indices_ExclusiveDecay(  {pdg_mother[0]} , {lb_pdg_daughters_cpp[0]}, true, false)( Particle, Particle1)",
            )
            # Extract Lbbar , p-~ pi+ gamma indices for Lb~
            .Define(
                "LbToPPiGamma_indices_bar",
                f"FCCAnalyses::MCParticle::get_indices_ExclusiveDecay(  {pdg_mother[1]} , {lb_pdg_daughters_cpp[1]}, true, false)( Particle, Particle1)",
            )
            .Filter(
                "LbToPPiGamma_indices.size()==4 || LbToPPiGamma_indices_bar.size()==4"
            )
            .Define(
                "Lambda_b",
                "selMC_leg(0)   ( LbToPPiGamma_indices.size() !=0 ?  LbToPPiGamma_indices : LbToPPiGamma_indices_bar , Particle)",
            )
            .Define(
                "Proton",
                "selMC_leg(1)   ( LbToPPiGamma_indices.size() !=0 ?  LbToPPiGamma_indices : LbToPPiGamma_indices_bar , Particle)",
            )
            .Define(
                "Pion",
                "selMC_leg(2)   ( LbToPPiGamma_indices.size() !=0 ?  LbToPPiGamma_indices : LbToPPiGamma_indices_bar , Particle)",
            )
            .Define(
                "Gamma",
                "selMC_leg(3)   ( LbToPPiGamma_indices.size() !=0 ?  LbToPPiGamma_indices : LbToPPiGamma_indices_bar , Particle)",
            )
            # Kinematics of the Lambda_b :
            .Define("Lb_theta", "FCCAnalyses::MCParticle::get_theta( Lambda_b )")
            .Define("Lb_phi", "FCCAnalyses::MCParticle::get_phi( Lambda_b )")
            .Define("Lb_PDG", "FCCAnalyses::MCParticle::get_pdg(Lambda_b)")
            .Define("Lb_x", "FCCAnalyses::MCParticle::get_vertex_x(Lambda_b)")
            .Define("Lb_y", "FCCAnalyses::MCParticle::get_vertex_y(Lambda_b)")
            .Define("Lb_z", "FCCAnalyses::MCParticle::get_vertex_z(Lambda_b)")
            .Define("Lb_e", "FCCAnalyses::MCParticle::get_e(Lambda_b)")
            .Define("Lb_m", "FCCAnalyses::MCParticle::get_mass(Lambda_b)")
            .Define("Gamma_theta", "FCCAnalyses::MCParticle::get_theta( Gamma )")
            .Define("Gamma_phi", "FCCAnalyses::MCParticle::get_phi( Gamma )")
            .Define("Gamma_PDG", "FCCAnalyses::MCParticle::get_pdg(Gamma)")
            .Define("Gamma_x", "FCCAnalyses::MCParticle::get_vertex_x(Gamma)")
            .Define("Gamma_y", "FCCAnalyses::MCParticle::get_vertex_y(Gamma)")
            .Define("Gamma_z", "FCCAnalyses::MCParticle::get_vertex_z(Gamma)")
            .Define("Gamma_e", "FCCAnalyses::MCParticle::get_e(Gamma)")
            .Define("Gamma_m", "FCCAnalyses::MCParticle::get_mass(Gamma)")
            .Define("Proton_theta", "FCCAnalyses::MCParticle::get_theta( Proton )")
            .Define("Proton_phi", "FCCAnalyses::MCParticle::get_phi( Proton )")
            .Define("Proton_PDG", "FCCAnalyses::MCParticle::get_pdg(Proton)")
            .Define("Proton_x", "FCCAnalyses::MCParticle::get_vertex_x(Proton)")
            .Define("Proton_y", "FCCAnalyses::MCParticle::get_vertex_y(Proton)")
            .Define("Proton_z", "FCCAnalyses::MCParticle::get_vertex_z(Proton)")
            .Define("Proton_e", "FCCAnalyses::MCParticle::get_e(Proton)")
            .Define("Proton_m", "FCCAnalyses::MCParticle::get_mass(Proton)")
            .Define("Pion_theta", "FCCAnalyses::MCParticle::get_theta( Pion )")
            .Define("Pion_phi", "FCCAnalyses::MCParticle::get_phi( Pion )")
            .Define("Pion_PDG", "FCCAnalyses::MCParticle::get_pdg(Pion)")
            .Define("Pion_x", "FCCAnalyses::MCParticle::get_vertex_x(Pion)")
            .Define("Pion_y", "FCCAnalyses::MCParticle::get_vertex_y(Pion)")
            .Define("Pion_z", "FCCAnalyses::MCParticle::get_vertex_z(Pion)")
            .Define("Pion_e", "FCCAnalyses::MCParticle::get_e(Pion)")
            .Define("Pion_m", "FCCAnalyses::MCParticle::get_mass(Pion)")
        )

        return dfProcessed

    @staticmethod
    def output():
        quantities = ("theta", "phi", "PDG", "x", "y", "z", "e", "m")
        return [
            f"{particle}_{quantity}"
            for particle in ("Lb", "Gamma", "Proton", "Pion")
            for quantity in quantities
        ]

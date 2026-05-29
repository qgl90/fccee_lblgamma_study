from __future__ import annotations

# Minimal FCCAnalyses treemaker for:
#   Lambda_b0 -> Lambda0(p pi) gamma
#
# Strategy:
# - Find truth decay products (stable final state) with MCParticle::get_indices
# - Match those MC particles to reco objects using MCRecoAssociations
# - Store a few sanity-check kinematics and reconstructed invariant masses

import os

import ROOT


# -----------------------------------------------------------------------------
# FCCAnalyses steering knobs (kept for compatibility with common examples)

processList = {"Lb2LambdaGamma": {"fraction": 1.0}}
analysisName = "Lb2LambdaGamma"
outputDir = "outputs/analysis"
nCPUS = 4
runBatch = False
batchQueue = "longlunch"

inputDir = "./"
procDict = "FCCee_procDict_winter2023_IDEA.json"


SELF_CONJUGATE_PDGS = {
    21, 22, 23, 25,
    111, 113, 115, 117,
    221, 223, 225, 227,
    331, 333, 335, 337,
    441, 443, 445,
}


def _parse_env_int(name: str) -> int:
    value = os.environ.get(name)
    if value is None or not value.strip():
        raise RuntimeError(f"Environment variable {name} must be set")
    try:
        return int(value.strip())
    except ValueError as exc:
        raise RuntimeError(f"Environment variable {name} must be an integer, got {value!r}") from exc


def _parse_env_int_list(name: str) -> list[int]:
    value = os.environ.get(name)
    if value is None or not value.strip():
        raise RuntimeError(f"Environment variable {name} must be set")
    try:
        parsed = [int(item.strip()) for item in value.split(",") if item.strip()]
    except ValueError as exc:
        raise RuntimeError(
            f"Environment variable {name} must be a comma-separated integer list, got {value!r}"
        ) from exc
    if not parsed:
        raise RuntimeError(f"Environment variable {name} must contain at least one PDG ID")
    return parsed


def _charge_conjugate_pdg(pdg: int) -> int:
    return pdg if abs(pdg) in SELF_CONJUGATE_PDGS else -pdg


def _cpp_vector(values: list[int]) -> str:
    return "{" + ", ".join(str(value) for value in values) + "}"


ROOT.gInterpreter.Declare("""
using namespace FCCAnalyses;
using namespace FCCAnalyses::MCParticle;

// return one MC leg corresponding to the Bs decay
// note: the sizxe of the vector is always zero or one. I return a ROOT::VecOps::RVec for convenience
struct selMC_leg{
  selMC_leg( int idx );
  int m_idx;
  ROOT::VecOps::RVec<edm4hep::MCParticleData> operator() (ROOT::VecOps::RVec<int> list_of_indices,
							  ROOT::VecOps::RVec<edm4hep::MCParticleData> in) ;
};


// To retrieve a given MC leg corresponding to the Bs decay
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
  else {
	std::cout << "   !!!  in selMC_leg:  idx = " << m_idx << " but size of list_of_indices = " << list_of_indices.size() << std::endl;
  }
  return res;
}
""")
ROOT.gInterpreter.Declare("""
edm4hep::Vector3d MyMCDecayVertex(ROOT::VecOps::RVec<edm4hep::Vector3d> in1, ROOT::VecOps::RVec<edm4hep::Vector3d> in2) {
   edm4hep::Vector3d vertex(1e12, 1e12, 1e12);
   if ( in1.size() == 0 && in2.size()==0) {
      std::cout <<"no vtx " <<std::endl;
      return vertex;
   }
   vertex = in1[0];
   return vertex;
}
""")
ROOT.gInterpreter.Declare("""
float MyMinEnergy(ROOT::VecOps::RVec<edm4hep::ReconstructedParticleData> in) {
   float min=999999.;
   for (auto & p: in) {
    if (p.energy<min && p.energy>0) min=p.energy;
  }
  return min;
}
""")

class RDFanalysis:
    @staticmethod
    def analysers(df):
        pdg_mother = _parse_env_int("FCC_SIG_PDG_MOTHER")
        pdg_daughters = _parse_env_int_list("FCC_SIG_PDG_DAUGHTERS")
        pdg_mothers = [pdg_mother, _charge_conjugate_pdg(pdg_mother)]
        pdg_daughter_sets = [
            pdg_daughters,
            [_charge_conjugate_pdg(daughter) for daughter in pdg_daughters],
        ]
        lb_pdg_daughters_cpp = [_cpp_vector(daughters) for daughters in pdg_daughter_sets]

        print("Configured signal mother PDGs:", pdg_mothers)
        print("Configured signal daughter PDGs:", lb_pdg_daughters_cpp)
        # cdecay
        dfProcessed = (
                #############################################
                ##          Aliases for # in python        ##
                #############################################
                df
                # .Alias("Particle0", "Particle#0.index")
                .Alias("Particle1", "Particle#1.index")
                .Alias("MCRecoAssociations0", "MCRecoAssociations#0.index")
                .Alias("MCRecoAssociations1", "MCRecoAssociations#1.index")
                # MC event primary vertex ( arg_genstatus = 21 means ? )
                .Define("MC_PrimaryVertex",  "FCCAnalyses::MCParticle::get_EventPrimaryVertex(21)( Particle )" )
                # Nb of tracks
                .Define("ntracks","ReconstructedParticle2Track::getTK_n(EFlowTrack_1)")
                # Retrieve the decay vertex of all MC particles
                .Define("MC_DecayVertices",  "FCCAnalyses::MCParticle::get_endPoint( Particle, Particle1)" )
                # Extract Lb    , p+  pi- gamma indices for Lb
                .Define("LbToPPiGamma_indices",     f"FCCAnalyses::MCParticle::get_indices_ExclusiveDecay(  {pdg_mothers[0]} , {lb_pdg_daughters_cpp[0]}, true, false)( Particle, Particle1)")
                # Extract Lbbar , p-~ pi+ gamma indices for Lb~
                .Define("LbToPPiGamma_indices_bar", f"FCCAnalyses::MCParticle::get_indices_ExclusiveDecay(  {pdg_mothers[1]} , {lb_pdg_daughters_cpp[1]}, true, false)( Particle, Particle1)")
                .Filter("LbToPPiGamma_indices.size()==4 || LbToPPiGamma_indices_bar.size()==4")

                .Define("Lambda_b", "selMC_leg(0)   ( LbToPPiGamma_indices.size() !=0 ?  LbToPPiGamma_indices : LbToPPiGamma_indices_bar , Particle)")
                .Define("Proton",   "selMC_leg(1)   ( LbToPPiGamma_indices.size() !=0 ?  LbToPPiGamma_indices : LbToPPiGamma_indices_bar , Particle)" )
                .Define("Pion",     "selMC_leg(2)   ( LbToPPiGamma_indices.size() !=0 ?  LbToPPiGamma_indices : LbToPPiGamma_indices_bar , Particle)" )
                .Define("Gamma",    "selMC_leg(3)   ( LbToPPiGamma_indices.size() !=0 ?  LbToPPiGamma_indices : LbToPPiGamma_indices_bar , Particle)" )

                .Define("LambdaMCDecayVertex",   "MyMCDecayVertex(FCCAnalyses::MCParticle::get_vertex(Proton),FCCAnalyses::MCParticle::get_vertex(Pion))")
                .Define("LambdabMCDecayVertex",  "MyMCDecayVertex(FCCAnalyses::MCParticle::get_vertex(Gamma),FCCAnalyses::MCParticle::get_vertex(Gamma))")
                # Kinematics of the Lambda_b :
                .Define("Lb_theta", "FCCAnalyses::MCParticle::get_theta( Lambda_b )")
                .Define("Lb_phi",   "FCCAnalyses::MCParticle::get_phi( Lambda_b )")
                .Define("Lb_PDG",   "FCCAnalyses::MCParticle::get_pdg(Lambda_b)")
                .Define("Lb_x",     "FCCAnalyses::MCParticle::get_vertex_x(Lambda_b)")
                .Define("Lb_y",     "FCCAnalyses::MCParticle::get_vertex_y(Lambda_b)")
                .Define("Lb_z",     "FCCAnalyses::MCParticle::get_vertex_z(Lambda_b)")
                .Define("Lb_e",     "FCCAnalyses::MCParticle::get_e(Lambda_b)")
                .Define("Lb_m",     "FCCAnalyses::MCParticle::get_mass(Lambda_b)")

                .Define("Gamma_theta", "FCCAnalyses::MCParticle::get_theta( Gamma )")
                .Define("Gamma_phi",   "FCCAnalyses::MCParticle::get_phi( Gamma )")
                .Define("Gamma_PDG",   "FCCAnalyses::MCParticle::get_pdg(Gamma)")
                .Define("Gamma_x",     "FCCAnalyses::MCParticle::get_vertex_x(Gamma)")
                .Define("Gamma_y",     "FCCAnalyses::MCParticle::get_vertex_y(Gamma)")
                .Define("Gamma_z",     "FCCAnalyses::MCParticle::get_vertex_z(Gamma)")
                .Define("Gamma_e",     "FCCAnalyses::MCParticle::get_e(Gamma)")
                .Define("Gamma_m",     "FCCAnalyses::MCParticle::get_mass(Gamma)")


                .Define("Proton_theta", "FCCAnalyses::MCParticle::get_theta( Proton )")
                .Define("Proton_phi",   "FCCAnalyses::MCParticle::get_phi( Proton )")
                .Define("Proton_PDG",   "FCCAnalyses::MCParticle::get_pdg(Proton)")
                .Define("Proton_x",     "FCCAnalyses::MCParticle::get_vertex_x(Proton)")
                .Define("Proton_y",     "FCCAnalyses::MCParticle::get_vertex_y(Proton)")
                .Define("Proton_z",     "FCCAnalyses::MCParticle::get_vertex_z(Proton)")
                .Define("Proton_e",     "FCCAnalyses::MCParticle::get_e(Proton)")
                .Define("Proton_m",     "FCCAnalyses::MCParticle::get_mass(Proton)")

                .Define("Pion_theta", "FCCAnalyses::MCParticle::get_theta( Pion )")
                .Define("Pion_phi",   "FCCAnalyses::MCParticle::get_phi( Pion )")
                .Define("Pion_PDG",   "FCCAnalyses::MCParticle::get_pdg(Pion)")
                .Define("Pion_x",     "FCCAnalyses::MCParticle::get_vertex_x(Pion)")
                .Define("Pion_y",     "FCCAnalyses::MCParticle::get_vertex_y(Pion)")
                .Define("Pion_z",     "FCCAnalyses::MCParticle::get_vertex_z(Pion)")
                .Define("Pion_e",     "FCCAnalyses::MCParticle::get_e(Pion)")
                .Define("Pion_m",     "FCCAnalyses::MCParticle::get_mass(Pion)")

        )
        return dfProcessed

    @staticmethod
    def output():
        vars = []
        for part in ["Lb","Gamma","Proton","Pion"] :
            vars += [
                f"{part}_theta",
                f"{part}_phi",
                f"{part}_PDG",
                f"{part}_x",
                f"{part}_y",
                f"{part}_z",
                f"{part}_e",
                f"{part}_m"
            ]
        for _ in vars :
            print( f"Snapshot : {_}")
        return vars

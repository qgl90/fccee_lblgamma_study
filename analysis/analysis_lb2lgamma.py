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

inputDir = "/afs/cern.ch/user/r/rquaglia/work/fcc_ee/fccee_lblgamma_study/outputs/delphes/"
procDict = "FCCee_procDict_winter2023_IDEA.json"


import ROOT
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
        # Lb -> Lambda0( p pi) gamma
        pdg_mother    =  ["5122",          "-5122"]        # Lambdab
        pdg_daughters =  ["2212,-211,22" , "-2212,211,22" ]# ppi , gamma                
        lb_pdg_daughters = pdg_mother        
        lb_pdg_daughters_cpp = ["{" + ", ".join(str(x) for x in dau.split(",")) + "}" for dau in pdg_daughters]        
        
        print( lb_pdg_daughters)
        print( lb_pdg_daughters_cpp)
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
                .Define("LbToPPiGamma_indices",     f"FCCAnalyses::MCParticle::get_indices_ExclusiveDecay(  {pdg_mother[0]} , {lb_pdg_daughters_cpp[0]}, true, false)( Particle, Particle1)")                
                # Extract Lbbar , p-~ pi+ gamma indices for Lb~
                .Define("LbToPPiGamma_indices_bar", f"FCCAnalyses::MCParticle::get_indices_ExclusiveDecay(  {pdg_mother[1]} , {lb_pdg_daughters_cpp[1]}, true, false)( Particle, Particle1)")
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
        #         # .Define(
        #         #     "Lb_truth_idx_all",
        #         #     f"MCParticle::get_indices_ExclusiveDecay({pdg_mother}, {pdg_daughters_cpp}, true, true)(Particle, Particle1)",
        #         # )
        #         # df = df.Filter("Lb_truth_idx_all.size() >= 3", "Lb -> L gamma in truth decay")
                        
                
                
        # )
      
        
        # # Filter so that every event has as truth Lb->L gamma decays 
        # ##############################################
        # ##         Filter events so it has Lb truth ##
        # ##############################################   
       
        
        #        .Define("MC_PrimaryVertex",  "FCCAnalyses::MCParticle::get_EventPrimaryVertex(21)( Particle )" )

        
        # def define_pdg( node) : 
        #     # get all the MC particles to check for Ks 
        #     # get momenta & mass of all particles                                                                                                                                                                                                                                                        
        #     return node.Define("MC_pdg", "FCCAnalyses::MCParticle::get_pdg(Particle)")
        #                .Define("MC_p4", "FCCAnalyses::MCParticle::get_tlv(Particle)")
        #                .Define("MC_mass", "FCCAnalyses::MCParticle::get_mass(Particle)")
        
        # df = define_pdg( df )
                
        # df = df.Define("LambdabLambdagamma_indices", "FCCAnalyses::MCParticle::get_indices_ExclusiveDecay(5122, {2212,-211,22}, true, true) (Particle, Particle1)")                
        # df = df.Define("Lambda0ppi_indices", "FCCAnalyses::MCParticle::get_indices_ExclusiveDecay(        3122, {2212, -211}, true, true) (Particle, Particle1)")
        

       
       
        # df = df.Define("Lb_truth_idx", "ROOT::VecOps::Take(Lb_truth_idx_all, 3)")

        # # -----------------------------------------------------------------------------
        # # Truth-seeded reco matching (avoids combinatorics for the first iteration)
        # df = df.Define(
        #     "LbRecoParts",
        #     "ReconstructedParticle2MC::selRP_matched_to_list(Lb_truth_idx, MCRecoAssociations0, MCRecoAssociations1, ReconstructedParticles, Particle)",
        # )
        # df = df.Filter("LbRecoParts.size() == 3")

        # # -----------------------------------------------------------------------------
        # # Reco kinematics and masses
        # df = df.Define("p_tlv", "ReconstructedParticle::get_tlv(LbRecoParts, 0)")
        # df = df.Define("pi_tlv", "ReconstructedParticle::get_tlv(LbRecoParts, 1)")
        # df = df.Define("g_tlv", "ReconstructedParticle::get_tlv(LbRecoParts, 2)")

        # df = df.Define("lambda0_reco_m", "(p_tlv + pi_tlv).M()")
        # df = df.Define("lb_reco_m", "(p_tlv + pi_tlv + g_tlv).M()")

        # df = df.Define("p_reco_p", "p_tlv.P()")
        # df = df.Define("pi_reco_p", "pi_tlv.P()")
        # df = df.Define("g_reco_e", "g_tlv.E()")

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
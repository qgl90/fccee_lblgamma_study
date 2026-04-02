from __future__ import annotations

# Simple (very first-pass) combinatorial reconstruction for:
#   Lambda_b0 -> Lambda0(p pi) gamma
#
# Caveats:
# - No PID: assigns p/pi by charge pattern (+,-) or (-,+) and mass hypothesis.
# - Photon: picks the highest-energy neutral candidate with small mass.
# - This gives a background shape, but is not a final analysis.

import ROOT


processList = {
  "Lb2LambdaGamma": {"fraction": 1.0}
  
}
analysisName = "Lb2LambdaGamma"
outputDir = "./outputs/analysis"
nCPUS = 4
runBatch = False
batchQueue = "longlunch"

# FCCAnalyses runner compatibility:
# some setups require that at least one of `inputDir` or `prodTag` exists in the script
# even if you override inputs via `--input` / `--input-file-list`.
inputDir = "./"

# Process dictionary (used by many FCCAnalyses templates; resolved via $FCCDICTSDIR)
procDict = "FCCee_procDict_winter2023_IDEA.json"


ROOT.gInterpreter.Declare(
    r"""
    #include <cmath>
    #include <limits>
    #include <utility>

    #include "ROOT/RVec.hxx"
    #include "TLorentzVector.h"
    #include "edm4hep/ReconstructedParticleData.h"

    namespace lb2lgamma {
      using ROOT::VecOps::RVec;

      static constexpr double kMP = 0.938272081;     // GeV
      static constexpr double kMPi = 0.13957039;     // GeV
      static constexpr double kMLambda0 = 1.115683;  // GeV

      inline TLorentzVector tlv_from_p3m(double px, double py, double pz, double m) {
        const double e = std::sqrt(px * px + py * py + pz * pz + m * m);
        return TLorentzVector(px, py, pz, e);
      }

      inline TLorentzVector tlv_from_rp_mass(const edm4hep::ReconstructedParticleData &rp, double m) {
        return tlv_from_p3m(rp.momentum.x, rp.momentum.y, rp.momentum.z, m);
      }

      inline TLorentzVector tlv_from_rp_energy(const edm4hep::ReconstructedParticleData &rp) {
        return TLorentzVector(rp.momentum.x, rp.momentum.y, rp.momentum.z, rp.energy);
      }

      RVec<int> best_lambda_indices(const RVec<edm4hep::ReconstructedParticleData> &rps) {
        double best_score = std::numeric_limits<double>::infinity();
        int best_p = -1;
        int best_pi = -1;

        const int n = (int)rps.size();
        for (int i = 0; i < n; ++i) {
          const int qi = (int)std::round(rps[i].charge);
          if (qi == 0)
            continue;
          for (int j = i + 1; j < n; ++j) {
            const int qj = (int)std::round(rps[j].charge);
            if (qj == 0)
              continue;
            if (qi * qj >= 0)
              continue; // need opposite charge

            // Assign p/pi by charge pattern:
            //   (+,-) -> p+ pi- (Lambda0)
            //   (-,+) -> p- pi+ (anti-Lambda0)
            int idx_p = -1;
            int idx_pi = -1;
            if (qi > 0 && qj < 0) {
              idx_p = i;
              idx_pi = j;
            } else if (qi < 0 && qj > 0) {
              idx_p = i;   // antiproton (mass hypothesis still mp)
              idx_pi = j;  // pi+
            } else if (qj > 0 && qi < 0) {
              idx_p = j;
              idx_pi = i;
            } else if (qj < 0 && qi > 0) {
              idx_p = j;
              idx_pi = i;
            }

            if (idx_p < 0 || idx_pi < 0)
              continue;

            const auto p4p = tlv_from_rp_mass(rps[idx_p], kMP);
            const auto p4pi = tlv_from_rp_mass(rps[idx_pi], kMPi);
            const double m = (p4p + p4pi).M();
            const double score = std::abs(m - kMLambda0);
            if (score < best_score) {
              best_score = score;
              best_p = idx_p;
              best_pi = idx_pi;
            }
          }
        }

        return RVec<int>{best_p, best_pi};
      }

      float lambda_mass(const RVec<edm4hep::ReconstructedParticleData> &rps, const RVec<int> &idx) {
        if (idx.size() < 2 || idx[0] < 0 || idx[1] < 0)
          return -1.f;
        const auto p4p = tlv_from_rp_mass(rps[idx[0]], kMP);
        const auto p4pi = tlv_from_rp_mass(rps[idx[1]], kMPi);
        return (p4p + p4pi).M();
      }

      int best_gamma_index(const RVec<edm4hep::ReconstructedParticleData> &rps, float emin, float max_mass) {
        int best = -1;
        float best_e = -1.f;
        const int n = (int)rps.size();
        for (int i = 0; i < n; ++i) {
          const int q = (int)std::round(rps[i].charge);
          if (q != 0)
            continue;
          if (rps[i].energy < emin)
            continue;
          if (rps[i].mass > max_mass)
            continue;
          if (rps[i].energy > best_e) {
            best_e = rps[i].energy;
            best = i;
          }
        }
        return best;
      }

      float lb_mass(const RVec<edm4hep::ReconstructedParticleData> &rps, const RVec<int> &idx, int gidx) {
        if (idx.size() < 2 || idx[0] < 0 || idx[1] < 0 || gidx < 0)
          return -1.f;
        const auto p4p = tlv_from_rp_mass(rps[idx[0]], kMP);
        const auto p4pi = tlv_from_rp_mass(rps[idx[1]], kMPi);
        const auto p4g = tlv_from_rp_energy(rps[gidx]);
        return (p4p + p4pi + p4g).M();
      }
    } // namespace lb2lgamma
"""
)


class RDFanalysis:
    @staticmethod
    def analysers(df):
        # Basic candidate building from the full reconstructed-particle list
        df = df.Define("lambda_idx", "lb2lgamma::best_lambda_indices(ReconstructedParticles)")
        df = df.Filter("lambda_idx.size() == 2 && lambda_idx[0] >= 0 && lambda_idx[1] >= 0")

        # photon: highest-energy neutral with small mass
        df = df.Define("gamma_idx", "lb2lgamma::best_gamma_index(ReconstructedParticles, 1.0f, 0.05f)")
        df = df.Filter("gamma_idx >= 0")

        df = df.Define("lambda0_reco_m", "lb2lgamma::lambda_mass(ReconstructedParticles, lambda_idx)")
        df = df.Define("lb_reco_m", "lb2lgamma::lb_mass(ReconstructedParticles, lambda_idx, gamma_idx)")

        df = df.Define(
            "gamma_e",
            "ReconstructedParticles.at(gamma_idx).energy",
        )
        return df

    @staticmethod
    def output():
        return [
            "lambda0_reco_m",
            "lb_reco_m",
            "gamma_e",
        ]

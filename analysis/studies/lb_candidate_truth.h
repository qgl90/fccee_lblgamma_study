// Author: Renato Quagliani (rquaglia@cern.ch)
#ifndef LBLGAMMA_STUDIES_LB_CANDIDATE_TRUTH_H
#define LBLGAMMA_STUDIES_LB_CANDIDATE_TRUTH_H

#include <algorithm>
#include <cmath>
#include <vector>

#include "ROOT/RVec.hxx"
#include "edm4hep/MCParticleData.h"
#include "edm4hep/ReconstructedParticleData.h"
#include "lb_candidate_builder.h"

namespace FCCAnalyses::LbCandidateTruth {

using ROOT::VecOps::RVec;
using FCCAnalyses::LbCandidateBuilder::Result;

// This module only labels builder output. It never removes or changes a
// reconstructed candidate. All indices are slots of the original EDM4hep
// Particle or ReconstructedParticles collections within the event.
struct Labels {
  std::vector<int> reco_mc_index, reco_mc_pdg, reco_mc_n_parents;
  std::vector<int> reco_mc_parent_index, reco_mc_parent_pdg;
  std::vector<int> reco_mc_grandparent_index, reco_mc_grandparent_pdg;
  std::vector<int> reco_mc_greatgrandparent_index, reco_mc_greatgrandparent_pdg;
  std::vector<int> reco_mc_greatgreatgrandparent_index, reco_mc_greatgreatgrandparent_pdg;
  std::vector<float> reco_p, reco_energy, reco_mc_p, reco_mc_energy;
  std::vector<float> reco_mc_cos_opening;
  std::vector<float> reco_mc_pt, reco_mc_eta, reco_mc_vertex_rxy;
  // The mass-hypothesis flag tests particle identity only. It does not
  // require common ancestry, so it is distinct from the full truth match.
  std::vector<int> lambda_mass_hypothesis_correct;
  std::vector<int> lambda_truth_matched, lambda_truth_lambda_mc_index;
  std::vector<int> lb_mass_hypothesis_correct;
  std::vector<int> lb_truth_matched, lb_truth_lb_mc_index;
  std::vector<int> lb_truth_neutral_mc_index;
  // Only defined for a fully truth-matched candidate with the correct signed
  // proton hypothesis; -999 elsewhere. Compare with lb_cos_theta_p by slot.
  std::vector<float> lb_truth_cos_theta_p;
  int n_truth_matched_lb = 0;
};

inline std::vector<int> parents(int index,
                                const RVec<edm4hep::MCParticleData>& mc,
                                const RVec<int>& parent_indices) {
  std::vector<int> out;
  if (index < 0 || static_cast<size_t>(index) >= mc.size()) return out;
  const auto& particle = mc[index];
  for (unsigned j = particle.parents_begin; j < particle.parents_end; ++j) {
    if (j >= parent_indices.size()) continue;
    const int parent = parent_indices[j];
    if (parent >= 0 && static_cast<size_t>(parent) < mc.size())
      out.push_back(parent);
  }
  return out;
}

inline int shared_lambda(int proton, int pion,
                         const RVec<edm4hep::MCParticleData>& mc,
                         const RVec<int>& parent_indices) {
  if (proton < 0 || pion < 0) return -1;
  if (std::abs(mc[proton].PDG) != 2212 || std::abs(mc[pion].PDG) != 211)
    return -1;
  for (int pparent : parents(proton, mc, parent_indices)) {
    if (std::abs(mc[pparent].PDG) != 3122) continue;
    for (int piparent : parents(pion, mc, parent_indices)) {
      if (pparent == piparent) return pparent;
    }
  }
  return -1;
}

inline int shared_lb(int lambda, int neutral,
                     const RVec<edm4hep::MCParticleData>& mc,
                     const RVec<int>& parent_indices) {
  if (lambda < 0 || neutral < 0 ||
      (mc[neutral].PDG != 22 && mc[neutral].PDG != 221)) return -1;
  for (int lparent : parents(lambda, mc, parent_indices)) {
    if (std::abs(mc[lparent].PDG) != 5122) continue;
    for (int gparent : parents(neutral, mc, parent_indices)) {
      if (lparent == gparent) return lparent;
    }
  }
  return -1;
}

inline int shared_eta(int photon1, int photon2,
                      const RVec<edm4hep::MCParticleData>& mc,
                      const RVec<int>& parent_indices) {
  if (photon1 < 0 || photon2 < 0 || photon1 == photon2 ||
      mc[photon1].PDG != 22 || mc[photon2].PDG != 22) return -1;
  for (int first_parent : parents(photon1, mc, parent_indices)) {
    if (mc[first_parent].PDG != 221) continue;
    for (int second_parent : parents(photon2, mc, parent_indices)) {
      if (first_parent == second_parent) return first_parent;
    }
  }
  return -1;
}

inline LbCandidateBuilder::FourMomentum mc_four_momentum(
    const edm4hep::MCParticleData& particle) {
  const auto& p = particle.momentum;
  const double p2 = double(p.x) * p.x + double(p.y) * p.y +
                    double(p.z) * p.z;
  return {p.x, p.y, p.z,
          std::sqrt(p2 + double(particle.mass) * particle.mass)};
}

inline Labels label(const Result& candidates,
                    const RVec<edm4hep::ReconstructedParticleData>& reco,
                    const RVec<edm4hep::MCParticleData>& mc,
                    const RVec<int>& assoc_reco,
                    const RVec<int>& assoc_mc,
                    const RVec<int>& parent_indices) {
  Labels out;
  std::vector<int> reco_links(reco.size(), 0), mc_links(mc.size(), 0);
  std::vector<int> associated_mc(reco.size(), -1);
  const size_t n = std::min(assoc_reco.size(), assoc_mc.size());
  for (size_t j = 0; j < n; ++j) {
    const int r = assoc_reco[j], m = assoc_mc[j];
    if (r < 0 || m < 0 || static_cast<size_t>(r) >= reco.size() ||
        static_cast<size_t>(m) >= mc.size()) continue;
    ++reco_links[r];
    ++mc_links[m];
    associated_mc[r] = m;
  }

  // Reco-level truth fields are stored once and joined to a candidate by its
  // three reco indices. -1/-999 denote absent or non-unique association.
  out.reco_mc_index.reserve(reco.size());
  out.reco_mc_pdg.reserve(reco.size());
  out.reco_mc_n_parents.reserve(reco.size());
  out.reco_mc_parent_index.reserve(reco.size());
  out.reco_mc_parent_pdg.reserve(reco.size());
  out.reco_mc_grandparent_index.reserve(reco.size());
  out.reco_mc_grandparent_pdg.reserve(reco.size());
  out.reco_mc_greatgrandparent_index.reserve(reco.size());
  out.reco_mc_greatgrandparent_pdg.reserve(reco.size());
  out.reco_mc_greatgreatgrandparent_index.reserve(reco.size());
  out.reco_mc_greatgreatgrandparent_pdg.reserve(reco.size());
  out.reco_mc_pt.reserve(reco.size());
  out.reco_mc_eta.reserve(reco.size());
  out.reco_mc_vertex_rxy.reserve(reco.size());
  for (size_t r = 0; r < reco.size(); ++r) {
    const int m = associated_mc[r];
    const bool unique = reco_links[r] == 1 && m >= 0 && mc_links[m] == 1 &&
                        mc[m].generatorStatus == 1;
    out.reco_mc_index.push_back(unique ? m : -1);
    out.reco_mc_pdg.push_back(unique ? mc[m].PDG : 0);
    const auto pp = unique ? parents(m, mc, parent_indices) : std::vector<int>{};
    const int parent = pp.empty() ? -1 : pp.front();
    const auto gp = parent >= 0 ? parents(parent, mc, parent_indices) :
                                  std::vector<int>{};
    const int grandparent = gp.empty() ? -1 : gp.front();
    const auto ggp = grandparent >= 0 ? parents(grandparent, mc, parent_indices) :
                                         std::vector<int>{};
    const int greatgrandparent = ggp.empty() ? -1 : ggp.front();
    const auto gggp = greatgrandparent >= 0 ?
        parents(greatgrandparent, mc, parent_indices) : std::vector<int>{};
    const int greatgreatgrandparent = gggp.empty() ? -1 : gggp.front();
    out.reco_mc_n_parents.push_back(static_cast<int>(pp.size()));
    out.reco_mc_parent_index.push_back(parent);
    out.reco_mc_parent_pdg.push_back(parent >= 0 ? mc[parent].PDG : 0);
    out.reco_mc_grandparent_index.push_back(grandparent);
    out.reco_mc_grandparent_pdg.push_back(
        grandparent >= 0 ? mc[grandparent].PDG : 0);
    out.reco_mc_greatgrandparent_index.push_back(greatgrandparent);
    out.reco_mc_greatgrandparent_pdg.push_back(
        greatgrandparent >= 0 ? mc[greatgrandparent].PDG : 0);
    out.reco_mc_greatgreatgrandparent_index.push_back(greatgreatgrandparent);
    out.reco_mc_greatgreatgrandparent_pdg.push_back(
        greatgreatgrandparent >= 0 ? mc[greatgreatgrandparent].PDG : 0);
    const float px = unique ? mc[m].momentum.x : 0.f;
    const float py = unique ? mc[m].momentum.y : 0.f;
    const float pz = unique ? mc[m].momentum.z : 0.f;
    const float pt = std::hypot(px, py);
    const auto& rp = reco[r].momentum;
    const float rp_mag = std::hypot(std::hypot(rp.x, rp.y), rp.z);
    const float mc_mag = std::hypot(pt, pz);
    out.reco_p.push_back(rp_mag);
    out.reco_energy.push_back(reco[r].energy);
    out.reco_mc_p.push_back(unique ? mc_mag : -999.f);
    out.reco_mc_energy.push_back(unique ?
        std::sqrt(double(px) * px + double(py) * py + double(pz) * pz +
                  double(mc[m].mass) * mc[m].mass) : -999.f);
    out.reco_mc_pt.push_back(unique ? pt : -999.f);
    out.reco_mc_cos_opening.push_back(unique && rp_mag > 0.f && mc_mag > 0.f ?
        (double(rp.x) * px + double(rp.y) * py + double(rp.z) * pz) /
            (double(rp_mag) * mc_mag) : -999.f);
    out.reco_mc_eta.push_back(unique && pt > 0.f ? std::asinh(pz / pt) : -999.f);
    out.reco_mc_vertex_rxy.push_back(unique ?
        std::hypot(mc[m].vertex.x, mc[m].vertex.y) : -999.f);
  }

  for (size_t i = 0; i < candidates.lambda_mass.size(); ++i) {
    const int p = out.reco_mc_index[candidates.lambda_proton_index[i]];
    const int pi = out.reco_mc_index[candidates.lambda_pion_index[i]];
    const int sign = candidates.lambda_sign[i];
    const bool correct_hypothesis = p >= 0 && pi >= 0 &&
        mc[p].PDG == sign * 2212 && mc[pi].PDG == -sign * 211;
    out.lambda_mass_hypothesis_correct.push_back(correct_hypothesis ? 1 : 0);
    int lambda = correct_hypothesis ? shared_lambda(p, pi, mc, parent_indices) : -1;
    if (lambda >= 0 && mc[lambda].PDG != sign * 3122) lambda = -1;
    out.lambda_truth_matched.push_back(lambda >= 0 ? 1 : 0);
    out.lambda_truth_lambda_mc_index.push_back(lambda);
  }

  for (size_t i = 0; i < candidates.lb_mass.size(); ++i) {
    const int slot = candidates.lb_lambda_slot[i];
    out.lb_mass_hypothesis_correct.push_back(
        out.lambda_mass_hypothesis_correct[slot]);
    const int lambda = out.lambda_truth_lambda_mc_index[slot];
    const int photon1 = out.reco_mc_index[candidates.lb_photon_index[i]];
    const int photon2_slot = candidates.lb_photon2_index[i];
    const int neutral = photon2_slot < 0 ? photon1 :
        shared_eta(photon1, out.reco_mc_index[photon2_slot], mc, parent_indices);
    int lb = shared_lb(lambda, neutral, mc, parent_indices);
    if (lb >= 0 && ((candidates.lb_sign[i] > 0 && mc[lb].PDG != 5122) ||
                    (candidates.lb_sign[i] < 0 && mc[lb].PDG != -5122)))
      lb = -1;
    out.lb_truth_matched.push_back(lb >= 0 ? 1 : 0);
    out.lb_truth_lb_mc_index.push_back(lb);
    out.lb_truth_neutral_mc_index.push_back(lb >= 0 ? neutral : -1);
    const int proton = out.reco_mc_index[candidates.lb_proton_index[i]];
    out.lb_truth_cos_theta_p.push_back(lb >= 0 && proton >= 0 ?
        LbCandidateBuilder::cos_theta_p(mc_four_momentum(mc[lb]),
            mc_four_momentum(mc[lambda]), mc_four_momentum(mc[proton])) :
        -999.f);
    if (lb >= 0) ++out.n_truth_matched_lb;
  }
  return out;
}

}  // namespace FCCAnalyses::LbCandidateTruth

#endif

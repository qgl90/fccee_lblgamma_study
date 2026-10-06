#ifndef LBGAMMA_FLAVOUR_TAGGING_V5_H
#define LBGAMMA_FLAVOUR_TAGGING_V5_H

#include <ROOT/RVec.hxx>
#include <algorithm>
#include <cmath>
#include <cstddef>
#include <limits>
#include <vector>

namespace FCCAnalyses::FlavourTaggingV5 {

inline int count_candidates_above_energy(const std::vector<float>& energy,
                                         float minimum) {
  int count = 0;
  for (const auto value : energy)
    if (std::isfinite(value) && value >= minimum) ++count;
  return count;
}

// Assign each reconstructed candidate to the nearest event jet in 3D angle.
// This is an event-level association; it does not remove candidate daughters
// from the jet before the tagger runs.
inline int nearest_jet(float px, float py, float pz,
                       const ROOT::VecOps::RVec<float>& jet_theta,
                       const ROOT::VecOps::RVec<float>& jet_phi) {
  const auto candidate_norm = std::sqrt(px * px + py * py + pz * pz);
  if (!(candidate_norm > 0.)) return -1;
  const auto njet = std::min(jet_theta.size(), jet_phi.size());
  int best = -1;
  float best_dot = -std::numeric_limits<float>::infinity();
  for (std::size_t j = 0; j < njet; ++j) {
    const auto jet_sin = std::sin(jet_theta[j]);
    const auto dot = (px * jet_sin * std::cos(jet_phi[j]) +
                      py * jet_sin * std::sin(jet_phi[j]) +
                      pz * std::cos(jet_theta[j])) / candidate_norm;
    if (dot > best_dot) {
      best_dot = dot;
      best = static_cast<int>(j);
    }
  }
  return best;
}

inline std::vector<float> associated_score(
    const ROOT::VecOps::RVec<float>& px,
    const ROOT::VecOps::RVec<float>& py,
    const ROOT::VecOps::RVec<float>& pz,
    const ROOT::VecOps::RVec<float>& jet_theta,
    const ROOT::VecOps::RVec<float>& jet_phi,
    const ROOT::VecOps::RVec<float>& scores) {
  std::vector<float> out;
  out.reserve(px.size());
  for (std::size_t i = 0; i < px.size(); ++i) {
    const auto j = nearest_jet(px[i], py[i], pz[i], jet_theta, jet_phi);
    out.emplace_back(j >= 0 && static_cast<std::size_t>(j) < scores.size()
                         ? scores[j] : -1.f);
  }
  return out;
}

inline std::vector<float> other_jet_max_score(
    const ROOT::VecOps::RVec<float>& px,
    const ROOT::VecOps::RVec<float>& py,
    const ROOT::VecOps::RVec<float>& pz,
    const ROOT::VecOps::RVec<float>& jet_theta,
    const ROOT::VecOps::RVec<float>& jet_phi,
    const ROOT::VecOps::RVec<float>& scores) {
  std::vector<float> out;
  out.reserve(px.size());
  for (std::size_t i = 0; i < px.size(); ++i) {
    const auto associated = nearest_jet(px[i], py[i], pz[i], jet_theta, jet_phi);
    float best = -1.f;
    for (std::size_t j = 0; j < scores.size(); ++j) {
      if (static_cast<int>(j) != associated && scores[j] > best) best = scores[j];
    }
    out.emplace_back(best);
  }
  return out;
}

}  // namespace FCCAnalyses::FlavourTaggingV5

#endif

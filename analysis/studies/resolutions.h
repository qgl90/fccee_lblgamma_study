#ifndef LBLGAMMA_STUDIES_RESOLUTIONS_H
#define LBLGAMMA_STUDIES_RESOLUTIONS_H

#include <algorithm>
#include <cmath>
#include <vector>

#include "ROOT/RVec.hxx"
#include "edm4hep/MCParticleData.h"
#include "edm4hep/ReconstructedParticleData.h"

namespace FCCAnalyses::ResolutionStudy {

using ROOT::VecOps::RVec;

// One vector entry per stable generated charged particle or photon. Missing or
// ambiguous reco matches have index -1 and kMissing in reco/residual columns.
constexpr float kMissing = -999.f;

template <typename Momentum>
float pt(const Momentum& v) {
  return std::hypot(v.x, v.y);
}

template <typename Momentum>
float p(const Momentum& v) {
  return std::hypot(pt(v), static_cast<float>(v.z));
}

template <typename Momentum>
float eta(const Momentum& v) {
  const float transverse = pt(v);
  return transverse > 0.f ? std::asinh(v.z / transverse) : kMissing;
}

template <typename Momentum>
float phi(const Momentum& v) {
  return std::atan2(v.y, v.x);
}

struct Result {
  int n_reco_track_candidates = 0;
  int n_reco_photon_candidates = 0;
  int n_selected_photons = 0;

  std::vector<int> track_mc_index, track_pdg, track_reco_index, track_n_links;
  std::vector<int> track_matched;
  std::vector<float> track_truth_charge, track_truth_p, track_truth_pt, track_truth_eta;
  std::vector<float> track_truth_rxy;
  std::vector<float> track_reco_charge, track_reco_p, track_reco_pt, track_reco_eta;
  std::vector<float> track_dp_rel, track_dpt_rel, track_dqoverpt;

  std::vector<int> gamma_mc_index, gamma_reco_index, gamma_n_links;
  std::vector<int> gamma_matched, gamma_selected, gamma_signal;
  std::vector<float> gamma_truth_e, gamma_truth_pt, gamma_truth_eta, gamma_truth_phi;
  std::vector<float> gamma_reco_e, gamma_reco_pt, gamma_reco_eta, gamma_reco_phi;
  std::vector<float> gamma_dE_rel;
};

inline Result make(const RVec<edm4hep::MCParticleData>& mc,
                   const RVec<edm4hep::ReconstructedParticleData>& reco,
                   const RVec<int>& reco_indices,
                   const RVec<int>& mc_indices,
                   const RVec<int>& selected_photon_indices,
                   const RVec<int>& daughter_indices) {
  Result out;
  std::vector<int> track_index(mc.size(), -1), track_links(mc.size(), 0);
  std::vector<int> gamma_index(mc.size(), -1), gamma_links(mc.size(), 0);
  std::vector<bool> selected(reco.size(), false);
  std::vector<bool> signal_gamma(mc.size(), false);

  // Direct gamma from Lambda_b -> Lambda0 gamma, including charge conjugates.
  // EDM4hep Particle#1.index maps each parent daughter-range entry to an MC slot.
  for (size_t i = 0; i < mc.size(); ++i) {
    if (std::abs(mc[i].PDG) != 5122) continue;
    bool has_lambda = false;
    std::vector<int> photons;
    for (unsigned j = mc[i].daughters_begin; j < mc[i].daughters_end; ++j) {
      if (j >= daughter_indices.size()) continue;
      const int index = daughter_indices[j];
      if (index < 0 || static_cast<size_t>(index) >= mc.size()) continue;
      if (std::abs(mc[index].PDG) == 3122) has_lambda = true;
      if (mc[index].PDG == 22) photons.push_back(index);
    }
    if (has_lambda) for (int index : photons) signal_gamma[index] = true;
  }

  for (int index : selected_photon_indices) {
    if (index >= 0 && static_cast<size_t>(index) < reco.size()) selected[index] = true;
  }
  out.n_selected_photons = static_cast<int>(selected_photon_indices.size());

  for (const auto& candidate : reco) {
    if (std::abs(candidate.charge) > 0.5f &&
        candidate.tracks_end > candidate.tracks_begin) ++out.n_reco_track_candidates;
    if (candidate.type == 22 && candidate.charge == 0.f)
      ++out.n_reco_photon_candidates;
  }

  // The two MCRecoAssociations index columns have matching row order.
  const size_t n_associations = std::min(reco_indices.size(), mc_indices.size());
  for (size_t i = 0; i < n_associations; ++i) {
    const int r = reco_indices[i], m = mc_indices[i];
    if (r < 0 || m < 0 || static_cast<size_t>(r) >= reco.size() ||
        static_cast<size_t>(m) >= mc.size()) continue;
    const auto& candidate = reco[r];
    if (std::abs(candidate.charge) > 0.5f &&
        candidate.tracks_end > candidate.tracks_begin) {
      track_index[m] = r;
      ++track_links[m];
    }
    if (candidate.type == 22 && candidate.charge == 0.f) {
      gamma_index[m] = r;
      ++gamma_links[m];
    }
  }

  for (size_t i = 0; i < mc.size(); ++i) {
    const auto& truth = mc[i];
    if (truth.generatorStatus != 1) continue;

    if (std::abs(truth.charge) > 0.5f) {
      const float truth_p = p(truth.momentum);
      const float truth_pt = pt(truth.momentum);
      const bool matched = track_links[i] == 1;
      const auto* candidate = matched ? &reco[track_index[i]] : nullptr;
      const float reco_p = candidate ? p(candidate->momentum) : kMissing;
      const float reco_pt = candidate ? pt(candidate->momentum) : kMissing;

      out.track_mc_index.push_back(static_cast<int>(i));
      out.track_pdg.push_back(truth.PDG);
      out.track_reco_index.push_back(matched ? track_index[i] : -1);
      out.track_n_links.push_back(track_links[i]);
      out.track_matched.push_back(matched ? 1 : 0);
      out.track_truth_charge.push_back(truth.charge);
      out.track_truth_p.push_back(truth_p);
      out.track_truth_pt.push_back(truth_pt);
      out.track_truth_eta.push_back(eta(truth.momentum));
      out.track_truth_rxy.push_back(std::hypot(truth.vertex.x, truth.vertex.y));
      out.track_reco_charge.push_back(candidate ? candidate->charge : kMissing);
      out.track_reco_p.push_back(reco_p);
      out.track_reco_pt.push_back(reco_pt);
      out.track_reco_eta.push_back(candidate ? eta(candidate->momentum) : kMissing);
      out.track_dp_rel.push_back(candidate && truth_p > 0.f
                                     ? (reco_p - truth_p) / truth_p : kMissing);
      out.track_dpt_rel.push_back(candidate && truth_pt > 0.f
                                      ? (reco_pt - truth_pt) / truth_pt : kMissing);
      out.track_dqoverpt.push_back(candidate && truth_pt > 0.f && reco_pt > 0.f
                                       ? candidate->charge / reco_pt - truth.charge / truth_pt
                                       : kMissing);
    }

    if (truth.PDG == 22) {
      const float truth_p = p(truth.momentum);
      const float truth_e = std::hypot(truth_p, static_cast<float>(truth.mass));
      const bool matched = gamma_links[i] == 1;
      const auto* candidate = matched ? &reco[gamma_index[i]] : nullptr;
      out.gamma_mc_index.push_back(static_cast<int>(i));
      out.gamma_reco_index.push_back(matched ? gamma_index[i] : -1);
      out.gamma_n_links.push_back(gamma_links[i]);
      out.gamma_matched.push_back(matched ? 1 : 0);
      out.gamma_selected.push_back(candidate && selected[gamma_index[i]] ? 1 : 0);
      out.gamma_signal.push_back(signal_gamma[i] ? 1 : 0);
      out.gamma_truth_e.push_back(truth_e);
      out.gamma_truth_pt.push_back(pt(truth.momentum));
      out.gamma_truth_eta.push_back(eta(truth.momentum));
      out.gamma_truth_phi.push_back(phi(truth.momentum));
      out.gamma_reco_e.push_back(candidate ? candidate->energy : kMissing);
      out.gamma_reco_pt.push_back(candidate ? pt(candidate->momentum) : kMissing);
      out.gamma_reco_eta.push_back(candidate ? eta(candidate->momentum) : kMissing);
      out.gamma_reco_phi.push_back(candidate ? phi(candidate->momentum) : kMissing);
      out.gamma_dE_rel.push_back(candidate && truth_e > 0.f
                                      ? (candidate->energy - truth_e) / truth_e : kMissing);
    }
  }
  return out;
}

}  // namespace FCCAnalyses::ResolutionStudy

#endif

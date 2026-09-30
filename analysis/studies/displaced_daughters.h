#ifndef LBLGAMMA_STUDIES_DISPLACED_DAUGHTERS_H
#define LBLGAMMA_STUDIES_DISPLACED_DAUGHTERS_H

#include <cmath>
#include <vector>

#include "resolutions.h"

namespace FCCAnalyses::DisplacedDaughters {

using ROOT::VecOps::RVec;

// One row per stable direct charged daughter of Lambda0 or K0S. The source
// label is the MC parent's absolute PDG; 3122 -> Lambda0, 310 -> K0S.
// Parent relationships use Particle#0.index, never the MC array slot directly.
struct Result {
  std::vector<int> mc_index, parent_pdg, pdg, matched, n_links, reco_index;
  std::vector<float> truth_p, truth_pt, truth_eta, truth_phi;
  std::vector<float> vertex_x, vertex_y, vertex_z, vertex_rxy;
  std::vector<float> reco_p, reco_pt, reco_eta, dp_rel, dpt_rel, dqoverpt;
};

inline Result make(const RVec<edm4hep::MCParticleData>& mc,
                   const RVec<edm4hep::ReconstructedParticleData>& reco,
                   const RVec<int>& reco_indices, const RVec<int>& mc_indices,
                   const RVec<int>& parent_indices) {
  const RVec<int> no_photons;
  const auto all = ResolutionStudy::make(mc, reco, reco_indices, mc_indices,
                                         no_photons, no_photons);
  Result out;
  for (size_t j = 0; j < all.track_mc_index.size(); ++j) {
    const int index = all.track_mc_index[j];
    const auto& particle = mc[index];
    const int abs_pdg = std::abs(particle.PDG);
    if (abs_pdg != 2212 && abs_pdg != 211) continue;

    int parent_pdg = 0;
    for (unsigned k = particle.parents_begin; k < particle.parents_end; ++k) {
      if (k >= parent_indices.size()) continue;
      const int parent = parent_indices[k];
      if (parent < 0 || static_cast<size_t>(parent) >= mc.size()) continue;
      const int abs_parent = std::abs(mc[parent].PDG);
      if ((abs_parent == 3122 && (abs_pdg == 2212 || abs_pdg == 211)) ||
          (abs_parent == 310 && abs_pdg == 211)) {
        parent_pdg = abs_parent;
        break;
      }
    }
    if (!parent_pdg) continue;

    out.mc_index.push_back(index);
    out.parent_pdg.push_back(parent_pdg);
    out.pdg.push_back(particle.PDG);
    out.matched.push_back(all.track_matched[j]);
    out.n_links.push_back(all.track_n_links[j]);
    out.reco_index.push_back(all.track_reco_index[j]);
    out.truth_p.push_back(all.track_truth_p[j]);
    out.truth_pt.push_back(all.track_truth_pt[j]);
    out.truth_eta.push_back(all.track_truth_eta[j]);
    out.truth_phi.push_back(ResolutionStudy::phi(particle.momentum));
    out.vertex_x.push_back(particle.vertex.x);
    out.vertex_y.push_back(particle.vertex.y);
    out.vertex_z.push_back(particle.vertex.z);
    out.vertex_rxy.push_back(std::hypot(particle.vertex.x, particle.vertex.y));
    out.reco_p.push_back(all.track_reco_p[j]);
    out.reco_pt.push_back(all.track_reco_pt[j]);
    out.reco_eta.push_back(all.track_reco_eta[j]);
    out.dp_rel.push_back(all.track_dp_rel[j]);
    out.dpt_rel.push_back(all.track_dpt_rel[j]);
    out.dqoverpt.push_back(all.track_dqoverpt[j]);
  }
  return out;
}

}  // namespace FCCAnalyses::DisplacedDaughters

#endif

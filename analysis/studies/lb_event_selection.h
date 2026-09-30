#ifndef LBLGAMMA_STUDIES_LB_EVENT_SELECTION_H
#define LBLGAMMA_STUDIES_LB_EVENT_SELECTION_H

#include <cmath>

#include "ROOT/RVec.hxx"
#include "edm4hep/ReconstructedParticleData.h"
#include "FCCAnalyses/VertexingUtils.h"

namespace FCCAnalyses::LbEventSelection {

struct InputCounts {
  int has_pv = 0;
  int n_photons = 0;
  int n_charged_tracks = 0;
  int n_positive_tracks = 0;
  int n_negative_tracks = 0;
};

// Event-level prerequisites only. The same object definitions are used by
// LbCandidateBuilder; no MC truth or particle-ID assignment is consulted.
inline InputCounts inspect(
    const ROOT::VecOps::RVec<edm4hep::ReconstructedParticleData>& particles,
    const VertexingUtils::FCCAnalysesVertex& pv,
    const ROOT::VecOps::RVec<int>& selected_photons) {
  InputCounts out;
  const auto& pos = pv.vertex.position;
  out.has_pv = pv.vertex.primary == 1 && pv.ntracks >= 2 &&
               std::isfinite(pos.x) && std::isfinite(pos.y) &&
               std::isfinite(pos.z);
  for (const auto& p : particles) {
    if (p.tracks_end <= p.tracks_begin) continue;
    if (p.charge > 0.5f) ++out.n_positive_tracks;
    else if (p.charge < -0.5f) ++out.n_negative_tracks;
  }
  for (int index : selected_photons) {
    if (index >= 0 && static_cast<size_t>(index) < particles.size() &&
        particles[index].type == 22 && particles[index].charge == 0.f)
      ++out.n_photons;
  }
  out.n_charged_tracks = out.n_positive_tracks + out.n_negative_tracks;
  return out;
}

}  // namespace FCCAnalyses::LbEventSelection

#endif

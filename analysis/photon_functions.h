#ifndef PHOTON_FUNCTIONS_H
#define PHOTON_FUNCTIONS_H

#include <cmath>
#include <algorithm>
#include "TLorentzVector.h"
#include "ROOT/RVec.hxx"
#include "edm4hep/ReconstructedParticleData.h"
#include "edm4hep/MCParticleData.h"
#include "edm4hep/CalorimeterHitData.h"

namespace FCCAnalyses {
namespace PhotonCheck {

using namespace ROOT::VecOps;
using Vec_rp  = RVec<edm4hep::ReconstructedParticleData>;
using Vec_mc  = RVec<edm4hep::MCParticleData>;
using Vec_hit = RVec<edm4hep::CalorimeterHitData>;
using Vec_f   = RVec<float>;
using Vec_i   = RVec<int>;

inline float p3(const edm4hep::Vector3f& m) {
  return std::sqrt(m.x * m.x + m.y * m.y + m.z * m.z);
}

inline float energy_of(const edm4hep::MCParticleData& p) {
  const float mom = p3(p.momentum);
  return std::sqrt(mom * mom + p.mass * p.mass);
}

inline float energy_of(const edm4hep::ReconstructedParticleData& p) {
  if (p.energy > 0.f) return p.energy;
  const float mom = p3(p.momentum);
  return std::sqrt(mom * mom + p.mass * p.mass);
}

inline TLorentzVector tlv_mc(const edm4hep::MCParticleData& p) {
  TLorentzVector v;
  v.SetXYZM(p.momentum.x, p.momentum.y, p.momentum.z, p.mass);
  return v;
}

inline TLorentzVector tlv_rp(const edm4hep::ReconstructedParticleData& p) {
  TLorentzVector v;
  v.SetXYZM(p.momentum.x, p.momentum.y, p.momentum.z, p.mass);
  return v;
}

// Truth photon that is a direct daughter of Lambda_b (PDG +/-5122).
// Particle1 = Particle#1.index  (daughter table in pre-edm4hep1)
inline Vec_i lb_gamma_indices(const Vec_mc& mc, const Vec_i& daughter_idx) {
  Vec_i out;
  for (size_t i = 0; i < mc.size(); ++i) {
    if (std::abs(mc[i].PDG) != 5122) continue;
    for (unsigned j = mc[i].daughters_begin; j < mc[i].daughters_end; ++j) {
      if (j >= daughter_idx.size()) continue;
      const int idau = daughter_idx[j];
      if (idau < 0 || idau >= (int)mc.size()) continue;
      if (mc[idau].PDG == 22) out.push_back(idau);
    }
  }
  return out;
}

inline Vec_mc sel_by_indices(const Vec_i& idx, const Vec_mc& mc) {
  Vec_mc out;
  for (int i : idx) {
    if (i >= 0 && i < (int)mc.size()) out.push_back(mc[i]);
  }
  return out;
}

struct MatchedPhoton {
  Vec_f reco_e, reco_p, reco_theta, reco_phi;
  Vec_f truth_e, truth_p, truth_theta, truth_phi;
  Vec_f dR, resp;
  Vec_f x, y, z, R;
  Vec_f hit_x, hit_y, hit_z, hit_e, hit_dR;
  Vec_i hit_found;
};

// xyz comes only from Delphes CalorimeterHits (tower X,Y,Z written by k4SimDelphes).
inline void fill_closest_hit(float px, float py, float pz,
                             const Vec_hit& hits,
                             float& hx, float& hy, float& hz, float& he,
                             float& hdR, int& found) {
  hx = hy = hz = he = 0.f;
  hdR = -1.f;
  found = 0;
  const float p = std::sqrt(px * px + py * py + pz * pz);
  if (p <= 0.f || hits.empty()) return;
  const float gx = px / p, gy = py / p, gz = pz / p;
  float best = 1.e9f;
  for (const auto& h : hits) {
    const float hr = std::sqrt(h.position.x * h.position.x +
                               h.position.y * h.position.y +
                               h.position.z * h.position.z);
    if (hr < 1.f) continue;
    const float cang = (h.position.x * gx + h.position.y * gy + h.position.z * gz) / hr;
    const float dR = std::acos(std::max(-1.f, std::min(1.f, cang)));
    if (dR < best) {
      best = dR;
      hx = h.position.x; hy = h.position.y; hz = h.position.z;
      he = h.energy;
      found = 1;
    }
  }
  if (found) hdR = best;
}

inline MatchedPhoton match_lb_photons(const Vec_rp& reco_photons,
                                      const Vec_mc& truth_photons,
                                      const Vec_hit& hits,
                                      float dRmax = 0.05f) {
  MatchedPhoton o;
  RVec<int> used(reco_photons.size(), 0);
  for (const auto& t : truth_photons) {
    const TLorentzVector tv = tlv_mc(t);
    float best = 1.e9f;
    int besti = -1;
    for (size_t i = 0; i < reco_photons.size(); ++i) {
      if (used[i]) continue;
      const float dR = tv.DeltaR(tlv_rp(reco_photons[i]));
      if (dR < best) { best = dR; besti = (int)i; }
    }
    if (besti < 0 || best > dRmax) continue;
    used[besti] = 1;
    const auto& r = reco_photons[besti];
    const TLorentzVector rv = tlv_rp(r);
    const float re = energy_of(r);
    const float te = energy_of(t);

    o.reco_e.push_back(re);
    o.reco_p.push_back(rv.P());
    o.reco_theta.push_back(rv.Theta());
    o.reco_phi.push_back(rv.Phi());
    o.truth_e.push_back(te);
    o.truth_p.push_back(tv.P());
    o.truth_theta.push_back(tv.Theta());
    o.truth_phi.push_back(tv.Phi());
    o.dR.push_back(best);
    o.resp.push_back(te > 0.f ? re / te : -1.f);

    float hx, hy, hz, he, hdR;
    int hf;
    fill_closest_hit(r.momentum.x, r.momentum.y, r.momentum.z, hits,
                     hx, hy, hz, he, hdR, hf);
    o.x.push_back(hx);
    o.y.push_back(hy);
    o.z.push_back(hz);
    o.R.push_back(std::hypot(hx, hy));
    o.hit_x.push_back(hx);
    o.hit_y.push_back(hy);
    o.hit_z.push_back(hz);
    o.hit_e.push_back(he);
    o.hit_dR.push_back(hdR);
    o.hit_found.push_back(hf);
  }
  return o;
}

inline MatchedPhoton match_lb_photons(const Vec_rp& reco_photons,
                                      const Vec_mc& truth_photons,
                                      float dRmax = 0.05f) {
  return match_lb_photons(reco_photons, truth_photons, Vec_hit{}, dRmax);
}

} // namespace PhotonCheck
} // namespace FCCAnalyses

#endif

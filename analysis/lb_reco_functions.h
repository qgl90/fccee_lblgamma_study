#ifndef LB_RECO_FUNCTIONS_H
#define LB_RECO_FUNCTIONS_H

#include <cmath>
#include <algorithm>
#include <vector>
#include "TLorentzVector.h"
#include "TVector3.h"
#include "ROOT/RVec.hxx"
#include "edm4hep/ReconstructedParticleData.h"
#include "edm4hep/VertexData.h"
#include "edm4hep/TrackState.h"
#include "edm4hep/MCParticleData.h"
#include "FCCAnalyses/VertexingUtils.h"
#include "FCCAnalyses/VertexFitterSimple.h"

namespace FCCAnalyses {
namespace LbReco {

using namespace ROOT::VecOps;
using Vec_f = RVec<float>;
using Vec_i = RVec<int>;
using Vec_d = RVec<double>;
using Vtx  = VertexingUtils::FCCAnalysesVertex;
using V0s  = VertexingUtils::FCCAnalysesV0;

constexpr float M_LAMBDA = 1.115683f;
constexpr float M_LB     = 5.61960f;
constexpr float M_GAMMA  = 0.f;
constexpr float M_PION     = 0.13957039f;
constexpr float M_P      = 0.93827208f;

using Vec_tr = RVec<edm4hep::TrackState>;
using Vec_rp = RVec<edm4hep::ReconstructedParticleData>;
using Vec_mc = RVec<edm4hep::MCParticleData>;

struct LambdaV0 {
  Vec_f m, px, py, pz, x, y, z, chi2, flight, cosA;
};

inline TLorentzVector track_tlv_from_rp(const edm4hep::ReconstructedParticleData& p, float mass) {
  TLorentzVector v;
  v.SetXYZM(p.momentum.x, p.momentum.y, p.momentum.z, mass);
  return v;
}

inline int mc_to_rp(int imc, const Vec_i& recind, const Vec_i& mcind) {
  if (imc < 0) return -1;
  for (size_t i = 0; i < mcind.size(); ++i)
    if (mcind[i] == imc) return recind[i];
  return -1;
}

inline Vec_i indices_pdg(const Vec_i& pdg, int absid) {
  Vec_i o;
  for (int i = 0; i < (int)pdg.size(); ++i)
    if (std::abs(pdg[i]) == absid) o.push_back(i);
  return o;
}

// myUtils::get_MCpdgMotherMCVertex -> vector<vector<int>> (PDGs at each vertex)
inline Vec_i indices_pdg(const std::vector<std::vector<int>>& pdg, int absid) {
  Vec_i o;
  for (int i = 0; i < (int)pdg.size(); ++i) {
    if (i == 0) continue; // skip PV
    for (int p : pdg[i]) {
      if (std::abs(p) == absid) { o.push_back(i); break; }
    }
  }
  return o;
}

inline Vec_f take_at(const Vec_f& v, const Vec_i& idx) {
  Vec_f o;
  for (int i : idx) if (i >= 0 && i < (int)v.size()) o.push_back(v[i]);
  return o;
}

// Direct Lambda0 daughters of Lambda_b (PDG +/-3122).
inline Vec_i lb_lambda_indices(const Vec_mc& mc, const Vec_i& daughter_idx) {
  Vec_i out;
  for (size_t i = 0; i < mc.size(); ++i) {
    if (std::abs(mc[i].PDG) != 5122) continue;
    for (unsigned j = mc[i].daughters_begin; j < mc[i].daughters_end; ++j) {
      if (j >= daughter_idx.size()) continue;
      const int idau = daughter_idx[j];
      if (idau < 0 || idau >= (int)mc.size()) continue;
      if (std::abs(mc[idau].PDG) == 3122) out.push_back(idau);
    }
  }
  return out;
}

// Charged p / pi among (grand)daughters of a given MC Lambda.
inline void collect_ppi(int iL, const Vec_mc& mc, const Vec_i& daughter_idx,
                        Vec_i& ip, Vec_i& ipi, int depth = 0) {
  if (iL < 0 || iL >= (int)mc.size() || depth > 6) return;
  for (unsigned j = mc[iL].daughters_begin; j < mc[iL].daughters_end; ++j) {
    if (j >= daughter_idx.size()) continue;
    const int id = daughter_idx[j];
    if (id < 0 || id >= (int)mc.size()) continue;
    const int pdg = std::abs(mc[id].PDG);
    if (pdg == 2212) ip.push_back(id);
    else if (pdg == 211) ipi.push_back(id);
    else collect_ppi(id, mc, daughter_idx, ip, ipi, depth + 1);
  }
}

// No extra fit: MC p,pi 4-vectors + already-fitted myUtils vertex xyz.
inline LambdaV0 cheated_Lambda_p4(const Vec_mc& mc, const Vec_i& daughter_idx,
                                  const Vec_i& recind, const Vec_i& mcind,
                                  const Vec_rp& reco,
                                  const Vec_f& Lx, const Vec_f& Ly, const Vec_f& Lz,
                                  float PVx, float PVy, float PVz) {
  LambdaV0 o;
  const TVector3 PV(PVx, PVy, PVz);
  const Vec_i iLs = lb_lambda_indices(mc, daughter_idx);
  for (size_t k = 0; k < iLs.size(); ++k) {
    Vec_i ips, ipis;
    collect_ppi(iLs[k], mc, daughter_idx, ips, ipis);
    if (ips.empty() || ipis.empty()) continue;
    const int irp_p  = mc_to_rp(ips[0], recind, mcind);
    const int irp_pi = mc_to_rp(ipis[0], recind, mcind);
    if (irp_p < 0 || irp_pi < 0 || irp_p >= (int)reco.size() || irp_pi >= (int)reco.size())
      continue;
    const TLorentzVector P = track_tlv_from_rp(reco[irp_p], M_P)
                           + track_tlv_from_rp(reco[irp_pi], M_PION);
    const float xx = (k < Lx.size()) ? Lx[k] : 0.f;
    const float yy = (k < Ly.size()) ? Ly[k] : 0.f;
    const float zz = (k < Lz.size()) ? Lz[k] : 0.f;
    o.m.push_back((float)P.M());
    o.px.push_back((float)P.Px());
    o.py.push_back((float)P.Py());
    o.pz.push_back((float)P.Pz());
    o.x.push_back(xx); o.y.push_back(yy); o.z.push_back(zz);
    o.chi2.push_back(-1.f);
    o.flight.push_back((float)(TVector3(xx, yy, zz) - PV).Mag());
    o.cosA.push_back(0.f);
  }
  return o;
}

// Truth 4-vectors of the MC p and pi from Lb's Lambda. No reco, no vertex.
inline LambdaV0 cheated_Lambda_mc_p4(const Vec_mc& mc, const Vec_i& daughter_idx) {
  LambdaV0 o;
  const Vec_i iLs = lb_lambda_indices(mc, daughter_idx);
  for (int iL : iLs) {
    Vec_i ips, ipis;
    collect_ppi(iL, mc, daughter_idx, ips, ipis);
    if (ips.empty() || ipis.empty()) continue;
    const auto& p  = mc[ips[0]];
    const auto& pi = mc[ipis[0]];
    TLorentzVector Pp, Ppi;
    Pp.SetXYZM(p.momentum.x, p.momentum.y, p.momentum.z, M_P);
    Ppi.SetXYZM(pi.momentum.x, pi.momentum.y, pi.momentum.z, M_PION);
    const TLorentzVector P = Pp + Ppi;
    o.m.push_back((float)P.M());
    o.px.push_back((float)P.Px());
    o.py.push_back((float)P.Py());
    o.pz.push_back((float)P.Pz());
    o.x.push_back(0.f); o.y.push_back(0.f); o.z.push_back(0.f);
    o.chi2.push_back(-1.f);
    o.flight.push_back(0.f);
    o.cosA.push_back(0.f);
  }
  return o;
}

// Cheated Lambda: take MC p,pi from Lb's Lambda, match to reco tracks, vertex-fit.
inline LambdaV0 cheated_Lambda_from_Lb(const Vec_mc& mc, const Vec_i& daughter_idx,
                                       const Vec_i& recind, const Vec_i& mcind,
                                       const Vec_rp& reco, const Vec_tr& tracks,
                                       const Vtx& PVobj) {
  LambdaV0 o;
  const auto& PVpos = PVobj.vertex.position;
  const TVector3 PV(PVpos.x, PVpos.y, PVpos.z);
  const Vec_i iLs = lb_lambda_indices(mc, daughter_idx);
  for (int iL : iLs) {
    Vec_i ips, ipis;
    collect_ppi(iL, mc, daughter_idx, ips, ipis);
    if (ips.empty() || ipis.empty()) continue;
    const int irp_p  = mc_to_rp(ips[0], recind, mcind);
    const int irp_pi = mc_to_rp(ipis[0], recind, mcind);
    if (irp_p < 0 || irp_pi < 0 || irp_p >= (int)reco.size() || irp_pi >= (int)reco.size())
      continue;
    Vec_rp legs;
    legs.push_back(reco[irp_p]);
    legs.push_back(reco[irp_pi]);
    const Vtx vtx = VertexFitterSimple::VertexFitter(2, legs, tracks);
    const TVector3 r(vtx.vertex.position.x, vtx.vertex.position.y, vtx.vertex.position.z);
    const TLorentzVector Pp  = track_tlv_from_rp(reco[irp_p], M_P);
    const TLorentzVector Ppi = track_tlv_from_rp(reco[irp_pi], M_PION);
    const TLorentzVector P = Pp + Ppi;
    o.m.push_back((float)P.M());
    o.px.push_back((float)P.Px());
    o.py.push_back((float)P.Py());
    o.pz.push_back((float)P.Pz());
    o.x.push_back((float)r.X());
    o.y.push_back((float)r.Y());
    o.z.push_back((float)r.Z());
    o.chi2.push_back(vtx.vertex.chi2);
    o.flight.push_back((float)(r - PV).Mag());
    o.cosA.push_back(0.f);
  }
  return o;
}

inline TLorentzVector track_tlv(const edm4hep::TrackState& tr, float mass) {
  const float om = tr.omega;
  const float pt = (std::abs(om) > 1e-12f) ? 1.f / std::abs(om) : 0.f;
  const float px = pt * std::cos(tr.phi);
  const float py = pt * std::sin(tr.phi);
  const float pz = pt * tr.tanLambda;
  TLorentzVector v;
  v.SetXYZM(px, py, pz, mass);
  return v;
}

inline float qsign(const edm4hep::TrackState& tr) {
  return (tr.omega >= 0.f) ? 1.f : -1.f;
}

// Drop-in V0 finder: opposite-charge pairs among non-primary tracks,
// VertexFitter_Tk(2), Lambda mass hypotheses p+pi- and pibar+pi+.
inline LambdaV0 find_Lambda_pairs(const Vec_tr& tracks, const Vtx& PVobj,
                                  float mlow = 1.100f, float mhigh = 1.130f,
                                  float chi2max = 9.f, float min_flight = 0.3f) {
  LambdaV0 o;
  const auto& PVpos = PVobj.vertex.position;
  const TVector3 PV(PVpos.x, PVpos.y, PVpos.z);
  const int n = (int)tracks.size();
  for (int i = 0; i < n; ++i) {
    for (int j = i + 1; j < n; ++j) {
      if (qsign(tracks[i]) * qsign(tracks[j]) >= 0.f) continue;
      Vec_tr pair;
      pair.push_back(tracks[i]);
      pair.push_back(tracks[j]);
      const Vtx vtx = VertexFitterSimple::VertexFitter_Tk(2, pair);
      const float chi2 = vtx.vertex.chi2;
      if (chi2 < 0.f || chi2 > chi2max) continue;
      const TVector3 r(vtx.vertex.position.x, vtx.vertex.position.y, vtx.vertex.position.z);
      const TVector3 fl = r - PV;
      const float Lxyz = (float)fl.Mag();
      if (Lxyz < min_flight) continue;

      const TLorentzVector A_ppi = track_tlv(tracks[i], M_P) + track_tlv(tracks[j], M_PION);
      const TLorentzVector A_pip = track_tlv(tracks[i], M_PION) + track_tlv(tracks[j], M_P);
      const float m1 = (float)A_ppi.M();
      const float m2 = (float)A_pip.M();
      const bool ok1 = (m1 > mlow && m1 < mhigh);
      const bool ok2 = (m2 > mlow && m2 < mhigh);
      if (!ok1 && !ok2) continue;
      const TLorentzVector& P = (!ok2 || (ok1 && std::abs(m1 - M_LAMBDA) <= std::abs(m2 - M_LAMBDA)))
                                    ? A_ppi : A_pip;
      const float mL = (float)P.M();
      TVector3 p = P.Vect();
      float cosa = 0.f;
      if (Lxyz > 0.f && p.Mag() > 0.f) cosa = (float)fl.Unit().Dot(p.Unit());
      if (cosa < 0.f) continue;

      o.m.push_back(mL);
      o.px.push_back((float)P.Px());
      o.py.push_back((float)P.Py());
      o.pz.push_back((float)P.Pz());
      o.x.push_back((float)r.X());
      o.y.push_back((float)r.Y());
      o.z.push_back((float)r.Z());
      o.chi2.push_back(chi2);
      o.flight.push_back(Lxyz);
      o.cosA.push_back(cosa);
    }
  }
  return o;
}

// Perfect-PID path: pair protons with pions (opposite charge), optional 2-track fit.
inline LambdaV0 find_Lambda_ppi_rp(const Vec_rp& protons, const Vec_rp& pions,
                                   const Vec_tr& tracks,
                                   float PVx, float PVy, float PVz,
                                   float mlow = 1.100f, float mhigh = 1.130f,
                                   bool do_fit = true) {
  LambdaV0 o;
  const TVector3 PV(PVx, PVy, PVz);
  for (const auto& pr : protons) {
    for (const auto& pi : pions) {
      if (pr.charge * pi.charge >= 0.f) continue;
      const TLorentzVector P = track_tlv_from_rp(pr, M_P) + track_tlv_from_rp(pi, M_PION);
      const float mL = (float)P.M();
      if (mL < mlow || mL > mhigh) continue;
      TVector3 r(pr.referencePoint.x, pr.referencePoint.y, pr.referencePoint.z);
      float chi2 = -1.f;
      if (do_fit) {
        Vec_rp legs; legs.push_back(pr); legs.push_back(pi);
        const Vtx vtx = VertexFitterSimple::VertexFitter(2, legs, tracks);
        r = TVector3(vtx.vertex.position.x, vtx.vertex.position.y, vtx.vertex.position.z);
        chi2 = vtx.vertex.chi2;
      }
      o.m.push_back(mL);
      o.px.push_back((float)P.Px());
      o.py.push_back((float)P.Py());
      o.pz.push_back((float)P.Pz());
      o.x.push_back((float)r.X());
      o.y.push_back((float)r.Y());
      o.z.push_back((float)r.Z());
      o.chi2.push_back(chi2);
      o.flight.push_back((float)(r - PV).Mag());
      o.cosA.push_back(0.f);
    }
  }
  return o;
}

// Keep only V0s tagged as Lambda (PDG 3122) if pdg is filled; else mass window.
inline Vec_i lambda_indices(const V0s& v0, float mlow = 1.100f, float mhigh = 1.130f) {
  Vec_i idx;
  const int n = VertexingUtils::get_n_SV(v0);
  auto masses = VertexingUtils::get_invM_V0(v0);
  auto pdgs   = VertexingUtils::get_pdg_V0(v0);
  for (int i = 0; i < n; ++i) {
    bool isL = false;
    if (i < (int)pdgs.size() && std::abs(pdgs[i]) == 3122) isL = true;
    if (i < (int)masses.size() && masses[i] > mlow && masses[i] < mhigh) isL = true;
    if (isL) idx.push_back(i);
  }
  return idx;
}

inline Vec_f take_f(const Vec_d& v, const Vec_i& idx) {
  Vec_f o;
  for (int i : idx) if (i >= 0 && i < (int)v.size()) o.push_back((float)v[i]);
  return o;
}

inline Vec_f take_pos(const RVec<TVector3>& v, const Vec_i& idx, int comp) {
  Vec_f o;
  for (int i : idx) {
    if (i < 0 || i >= (int)v.size()) continue;
    if (comp == 0) o.push_back((float)v[i].X());
    if (comp == 1) o.push_back((float)v[i].Y());
    if (comp == 2) o.push_back((float)v[i].Z());
  }
  return o;
}

// Combine each Lambda V0 with each matched Lb-photon into an Lb candidate.
// Photons: reco_e, reco px/py/pz from matched photon 3-momentum
// (use reco_p * direction from theta/phi stored earlier, or pass px,py,pz).
struct LbCand {
  Vec_f m, p, energy;
  Vec_f L_m, L_px, L_py, L_pz, L_x, L_y, L_z;
  Vec_f g_e, g_px, g_py, g_pz;
  Vec_i iL, ig;
};

inline LbCand combine_Lambda_gamma(const Vec_f& Lm, const Vec_f& Lpx, const Vec_f& Lpy,
                                   const Vec_f& Lpz, const Vec_f& Lx, const Vec_f& Ly,
                                   const Vec_f& Lz, const Vec_f& ge, const Vec_f& gpx,
                                   const Vec_f& gpy, const Vec_f& gpz) {
  LbCand o;
  for (size_t i = 0; i < Lpx.size(); ++i) {
    TLorentzVector L;
    const float eL = std::sqrt(Lpx[i]*Lpx[i] + Lpy[i]*Lpy[i] + Lpz[i]*Lpz[i]
                               + (Lm.empty() ? M_LAMBDA*M_LAMBDA : Lm[i]*Lm[i]));
    L.SetPxPyPzE(Lpx[i], Lpy[i], Lpz[i],
                 Lm.size()==Lpx.size()
                   ? std::sqrt(Lpx[i]*Lpx[i]+Lpy[i]*Lpy[i]+Lpz[i]*Lpz[i]+Lm[i]*Lm[i])
                   : eL);
    for (size_t j = 0; j < ge.size(); ++j) {
      TLorentzVector g;
      g.SetPxPyPzE(gpx[j], gpy[j], gpz[j], ge[j]);
      const TLorentzVector Lb = L + g;
      o.m.push_back((float)Lb.M());
      o.p.push_back((float)Lb.P());
      o.energy.push_back((float)Lb.E());
      o.L_m.push_back(Lm.size()==Lpx.size() ? Lm[i] : M_LAMBDA);
      o.L_px.push_back(Lpx[i]); o.L_py.push_back(Lpy[i]); o.L_pz.push_back(Lpz[i]);
      o.L_x.push_back(Lx[i]); o.L_y.push_back(Ly[i]); o.L_z.push_back(Lz[i]);
      o.g_e.push_back(ge[j]); o.g_px.push_back(gpx[j]); o.g_py.push_back(gpy[j]); o.g_pz.push_back(gpz[j]);
      o.iL.push_back((int)i); o.ig.push_back((int)j);
    }
  }
  return o;
}

// Closest approach of two lines:
//   PV + a * thrust_hat
//   Lvtx + b * pL_hat
// Stored for the later "photon origin = intercept" stage.
struct Intercept {
  Vec_f x, y, z, dist, a, b;
};

inline Intercept thrust_lambda_intercept(float PVx, float PVy, float PVz,
                                         float tx, float ty, float tz,
                                         const Vec_f& Lx, const Vec_f& Ly, const Vec_f& Lz,
                                         const Vec_f& Lpx, const Vec_f& Lpy, const Vec_f& Lpz) {
  Intercept o;
  TVector3 T(tx, ty, tz);
  if (T.Mag() > 0) T *= 1. / T.Mag();
  TVector3 PV(PVx, PVy, PVz);
  for (size_t i = 0; i < Lx.size(); ++i) {
    TVector3 L0(Lx[i], Ly[i], Lz[i]);
    TVector3 D(Lpx[i], Lpy[i], Lpz[i]);
    if (D.Mag() > 0) D *= 1. / D.Mag();
    const TVector3 w0 = PV - L0;
    const double a = T.Dot(T), b = T.Dot(D), c = D.Dot(D);
    const double d = T.Dot(w0), e = D.Dot(w0);
    const double den = a * c - b * b;
    double s = 0, tpar = 0;
    if (std::abs(den) > 1e-12) {
      s = (b * e - c * d) / den;
      tpar = (a * e - b * d) / den;
    }
    const TVector3 p1 = PV + s * T;
    const TVector3 p2 = L0 + tpar * D;
    const TVector3 mid = 0.5 * (p1 + p2);
    o.x.push_back((float)mid.X());
    o.y.push_back((float)mid.Y());
    o.z.push_back((float)mid.Z());
    o.dist.push_back((float)(p1 - p2).Mag());
    o.a.push_back((float)s);
    o.b.push_back((float)tpar);
  }
  return o;
}

// Correct photon 3-momentum so that its origin is `orig` and it still
// points to the calorimeter impact `hit`. Energy kept as reco energy.
inline void photon_from_origin(float ox, float oy, float oz,
                               float hx, float hy, float hz, float e,
                               float& px, float& py, float& pz) {
  TVector3 dir(hx - ox, hy - oy, hz - oz);
  if (dir.Mag() <= 0) { px = py = pz = 0; return; }
  dir *= e / dir.Mag();   // massless: |p| = E
  px = (float)dir.X(); py = (float)dir.Y(); pz = (float)dir.Z();
}

// Same 2-body combiner, but photon direction is
//   cluster_hit - intercept(Lambda flight, thrust through PV)
// Energy stays the reconstructed calorimeter energy.
inline LbCand combine_Lambda_gamma_corr(const Vec_f& Lm, const Vec_f& Lpx, const Vec_f& Lpy,
                                        const Vec_f& Lpz, const Vec_f& Lx, const Vec_f& Ly,
                                        const Vec_f& Lz,
                                        const Vec_f& itx, const Vec_f& ity, const Vec_f& itz,
                                        const Vec_f& ge,
                                        const Vec_f& gx, const Vec_f& gy, const Vec_f& gz,
                                        const Vec_f& gpx0, const Vec_f& gpy0, const Vec_f& gpz0) {
  LbCand o;
  for (size_t i = 0; i < Lpx.size(); ++i) {
    TLorentzVector L;
    const float mL = (Lm.size() == Lpx.size()) ? Lm[i] : M_LAMBDA;
    L.SetXYZM(Lpx[i], Lpy[i], Lpz[i], mL);
    const float ox = (i < itx.size()) ? itx[i] : 0.f;
    const float oy = (i < ity.size()) ? ity[i] : 0.f;
    const float oz = (i < itz.size()) ? itz[i] : 0.f;
    for (size_t j = 0; j < ge.size(); ++j) {
      float gpx = 0, gpy = 0, gpz = 0;
      const bool has_hit = (j < gx.size()) && (gx[j]*gx[j] + gy[j]*gy[j] + gz[j]*gz[j] > 1.f);
      if (has_hit)
        photon_from_origin(ox, oy, oz, gx[j], gy[j], gz[j], ge[j], gpx, gpy, gpz);
      else if (j < gpx0.size()) {
        gpx = gpx0[j]; gpy = gpy0[j]; gpz = gpz0[j];
      }
      TLorentzVector g;
      g.SetPxPyPzE(gpx, gpy, gpz, ge[j]);
      const TLorentzVector Lb = L + g;
      o.m.push_back((float)Lb.M());
      o.p.push_back((float)Lb.P());
      o.energy.push_back((float)Lb.E());
      o.L_m.push_back(mL);
      o.L_px.push_back(Lpx[i]); o.L_py.push_back(Lpy[i]); o.L_pz.push_back(Lpz[i]);
      o.L_x.push_back(Lx[i]); o.L_y.push_back(Ly[i]); o.L_z.push_back(Lz[i]);
      o.g_e.push_back(ge[j]); o.g_px.push_back(gpx); o.g_py.push_back(gpy); o.g_pz.push_back(gpz);
      o.iL.push_back((int)i); o.ig.push_back((int)j);
    }
  }
  return o;
}

} // namespace LbReco
} // namespace FCCAnalyses

#endif

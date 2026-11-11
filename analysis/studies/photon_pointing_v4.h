#ifndef LBLGAMMA_PHOTON_POINTING_V4_H
#define LBLGAMMA_PHOTON_POINTING_V4_H
#include <array>
#include <limits>
#include "lb_candidate_truth.h"
namespace FCCAnalyses::PhotonPointingV4 {
// Effective IDEA surface, audited on 200 events. Units mm and GeV.
constexpr double R=2250., Z=2500., Rin=249.55392417205682, Rout=2250.;
constexpr double missing=std::numeric_limits<double>::quiet_NaN();
struct Hit { double x=missing,y=missing,z=missing,path=missing; int region=0; };
inline Hit intersect(double x,double y,double z,double px,double py,double pz) {
  Hit h;
  const double norm=std::sqrt(px*px+py*py+pz*pz);
  if (!(norm>0) || !std::isfinite(norm+x+y+z)) return h;
  px/=norm; py/=norm; pz/=norm;
  auto accept=[&](double t,int region) {
    if (!(t>0) || !std::isfinite(t)) return;
    double hx=x+t*px,hy=y+t*py,hz=z+t*pz,r=std::hypot(hx,hy);
    if (region==1 ? std::abs(hz)>Z+1e-8 : (r<Rin-1e-8 || r>Rout+1e-8)) return;
    if (h.region && t>=h.path) return;
    h={hx,hy,hz,t,region};
  };
  double a=px*px+py*py,b=x*px+y*py,c=x*x+y*y-R*R,d=b*b-a*c;
  if(a>0 && d>=0) { accept((-b-std::sqrt(d))/a,1); accept((-b+std::sqrt(d))/a,1); }
  if(pz!=0) { accept((Z-z)/pz,2); accept((-Z-z)/pz,2); }
  return h;
}
struct Labels {
  std::vector<double> mc_index;
  std::vector<double> match_status;
  std::vector<double> truth_px;
  std::vector<double> truth_py;
  std::vector<double> truth_pz;
  std::vector<double> truth_energy;
  std::vector<double> truth_vx;
  std::vector<double> truth_vy;
  std::vector<double> truth_vz;
  std::vector<double> truth_hit_x;
  std::vector<double> truth_hit_y;
  std::vector<double> truth_hit_z;
  std::vector<double> truth_hit_path;
  std::vector<double> truth_hit_region;
  std::vector<double> reco_hit_x;
  std::vector<double> reco_hit_y;
  std::vector<double> reco_hit_z;
  std::vector<double> reco_hit_path;
  std::vector<double> reco_hit_region;
  std::vector<double> geometry_version;
  std::vector<double> barrel_radius;
  std::vector<double> endcap_abs_z;
  std::vector<double> endcap_inner_radius;
  std::vector<double> endcap_outer_radius;
  std::vector<double> pv_x;
  std::vector<double> pv_y;
  std::vector<double> pv_z;
  std::vector<double> pv_valid;
};
inline Labels label(const LbCandidateBuilder::Result& c,
 const LbCandidateTruth::Labels& truth,
 const ROOT::VecOps::RVec<edm4hep::ReconstructedParticleData>& reco,
 const ROOT::VecOps::RVec<edm4hep::MCParticleData>& mc) {
 Labels o;
 for (int ri : c.lb_photon_index) {
   int mi=(ri>=0 && ri<int(truth.reco_mc_index.size()))?truth.reco_mc_index[ri]:-1;
   bool matched=mi>=0 && mi<int(mc.size());
   int status=matched?(mc[mi].PDG==22?1:2):0;
   double tx=missing,ty=missing,tz=missing,te=missing,vx=missing,vy=missing,vz=missing;
   Hit th,rh;
   if(ri>=0 && ri<int(reco.size())) {
     const auto& r=reco[ri]; rh=intersect(0,0,0,r.momentum.x,r.momentum.y,r.momentum.z);
   }
   if(status==1) {
     const auto& m=mc[mi]; tx=m.momentum.x; ty=m.momentum.y; tz=m.momentum.z;
     te=std::sqrt(tx*tx+ty*ty+tz*tz+m.mass*m.mass);
     vx=m.vertex.x; vy=m.vertex.y; vz=m.vertex.z;
     th=intersect(vx,vy,vz,tx,ty,tz);
   }
   o.mc_index.push_back(mi);
   o.match_status.push_back(status);
   o.truth_px.push_back(tx);
   o.truth_py.push_back(ty);
   o.truth_pz.push_back(tz);
   o.truth_energy.push_back(te);
   o.truth_vx.push_back(vx);
   o.truth_vy.push_back(vy);
   o.truth_vz.push_back(vz);
   o.truth_hit_x.push_back(th.x);
   o.truth_hit_y.push_back(th.y);
   o.truth_hit_z.push_back(th.z);
   o.truth_hit_path.push_back(th.path);
   o.truth_hit_region.push_back(th.region);
   o.reco_hit_x.push_back(rh.x);
   o.reco_hit_y.push_back(rh.y);
   o.reco_hit_z.push_back(rh.z);
   o.reco_hit_path.push_back(rh.path);
   o.reco_hit_region.push_back(rh.region);
   o.geometry_version.push_back(4);
   o.barrel_radius.push_back(R);
   o.endcap_abs_z.push_back(Z);
   o.endcap_inner_radius.push_back(Rin);
   o.endcap_outer_radius.push_back(Rout);
   o.pv_x.push_back(c.pv_x);
   o.pv_y.push_back(c.pv_y);
   o.pv_z.push_back(c.pv_z);
   o.pv_valid.push_back(c.pv_valid);
 }
 return o;
}
}
#endif

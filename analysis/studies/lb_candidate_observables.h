// Author: Renato Quagliani (rquaglia@cern.ch)
#ifndef LBLGAMMA_STUDIES_LB_CANDIDATE_OBSERVABLES_H
#define LBLGAMMA_STUDIES_LB_CANDIDATE_OBSERVABLES_H

// Candidate-level diagnostics added AFTER the existing Lambda+photon builder.
// These functions never inspect truth labels and impose no candidate cuts.
// ROE and its thrust axis are computed afresh after removing p, pi and gamma.

#include <algorithm>
#include <array>
#include <cmath>
#include <limits>
#include <vector>

#include "ROOT/RVec.hxx"
#include "edm4hep/ReconstructedParticleData.h"
#include "FCCAnalyses/Algorithms.h"
#include "lb_candidate_builder.h"

namespace FCCAnalyses::LbCandidateObservables {

using ROOT::VecOps::RVec;
using LbCandidateBuilder::FourMomentum;
constexpr float kMissing = -999.f;

struct Config {
  double ecm_gev = 91.2;
  double lb_mass_gev = 5.6196;
  double lambda_mass_gev = 1.115683;
  double pi0_mass_gev = 0.1349768;
  double cone_r02 = 0.2, cone_r03 = 0.3, cone_r05 = 0.5;
  double cone_r07 = 0.7, cone_r10 = 1.0, cone_r20 = 2.0;
};

struct Result {
  std::vector<float> iso_delphes, iso_R02, iso_R03, iso_R05;
  std::vector<float> iso_R02_E, iso_R03_E, iso_R05_E;
  std::vector<float> iso_R03_noLambda, iso_R05_noLambda;
  std::vector<float> iso_R03_noLambda_E, iso_R05_noLambda_E;
  std::vector<float> iso_charged, iso_neutral;
  std::vector<float> iso_charged_E, iso_neutral_E;
  std::vector<int> iso_delphes_available, n_photons_DR03, n_photons_DR05;
  std::vector<float> m_gg_best, dm_gg_pi0, E_gamma2, dr_gg;
  std::vector<int> gamma2_index;
  std::vector<std::vector<float>> gamma_combo_other_gamma_mass;
  std::vector<std::vector<int>> gamma_combo_other_gamma_index;
  std::vector<std::vector<float>> gamma_combo_same_hemi_all_mass;
  std::vector<std::vector<int>> gamma_combo_same_hemi_all_index;
  std::vector<std::vector<float>> gamma_combo_same_hemi_selected_mass;
  std::vector<std::vector<int>> gamma_combo_same_hemi_selected_index;
  std::vector<float> m_LamGam, m_rec, dm_rec, m_rec_all;
  std::vector<float> deltaE, px_bal, py_bal, pz_bal, deltaP;
  // Original event-thrust hemisphere, fitted Lambda side defines signal side.
  // The candidate and the opposite-side ROE form a partial Z-closure proxy.
  std::vector<float> opp_hemi_px, opp_hemi_py, opp_hemi_pz;
  std::vector<float> opp_hemi_p, opp_hemi_energy;
  std::vector<int> opp_hemi_n;
  std::vector<float> z_partial_deltaE, z_partial_px, z_partial_py;
  std::vector<float> z_partial_pz, z_partial_deltaP;
  // All remaining reconstructed objects plus the fitted candidate.
  std::vector<float> z_full_deltaE, z_full_px, z_full_py;
  std::vector<float> z_full_pz, z_full_deltaP;
  std::vector<float> cos_rec_sig, Estar_gamma, Estar_gamma_rec;
  std::vector<float> dEstar, dEstar_rec, E_same, m_same;
  std::vector<float> dca_Lam_gamma, Lxyz_implied, cos_dir_implied;
  // Lambda trajectory relative to PV: distinct from displacement significance.
  std::vector<float> lambda_pv_cos, lambda_pv_dca;
  std::vector<float> roe_thrust_x, roe_thrust_y, roe_thrust_z;
  std::vector<int> roe_n_other, roe_n_same;
  // [cone R02/R03/R05/R07/R10/R20][all/charged/neutral]. The iso_* fields
  // are photon-centered; lambda_iso_* fields are fitted-Lambda-centered.
  std::array<std::array<std::vector<float>,3>,6> iso_activity_px;
  std::array<std::array<std::vector<float>,3>,6> iso_activity_py;
  std::array<std::array<std::vector<float>,3>,6> iso_activity_pz;
  std::array<std::array<std::vector<float>,3>,6> iso_activity_p;
  std::array<std::array<std::vector<float>,3>,6> iso_activity_energy;
  std::array<std::array<std::vector<int>,3>,6> iso_activity_n;
  // d0 to the fitted PV in mm for charged objects with a linked track.
  std::array<std::vector<float>,6> iso_charged_d0_min, iso_charged_d0_max;
  std::array<std::vector<float>,6> iso_charged_absd0_min, iso_charged_absd0_max;
  std::array<std::vector<int>,6> iso_charged_n_d0;
  std::array<std::array<std::vector<float>,3>,6> lambda_iso_activity_px;
  std::array<std::array<std::vector<float>,3>,6> lambda_iso_activity_py;
  std::array<std::array<std::vector<float>,3>,6> lambda_iso_activity_pz;
  std::array<std::array<std::vector<float>,3>,6> lambda_iso_activity_p;
  std::array<std::array<std::vector<float>,3>,6> lambda_iso_activity_energy;
  std::array<std::array<std::vector<int>,3>,6> lambda_iso_activity_n;
  std::array<std::vector<float>,6> lambda_iso_charged_d0_min, lambda_iso_charged_d0_max;
  std::array<std::vector<float>,6> lambda_iso_charged_absd0_min, lambda_iso_charged_absd0_max;
  std::array<std::vector<int>,6> lambda_iso_charged_n_d0;
  std::vector<float> arm_alpha, arm_qt;
};

struct Activity {
  double px=0., py=0., pz=0., energy=0.;
  int n=0, n_d0=0;
  double min_d0=std::numeric_limits<double>::infinity();
  double max_d0=-std::numeric_limits<double>::infinity();
  double min_absd0=std::numeric_limits<double>::infinity();
  double max_absd0=-std::numeric_limits<double>::infinity();
};

inline FourMomentum particle_p4(const edm4hep::ReconstructedParticleData& p) {
  return {p.momentum.x, p.momentum.y, p.momentum.z, p.energy};
}
inline FourMomentum subtract(const FourMomentum& a, const FourMomentum& b) {
  return {a.px-b.px, a.py-b.py, a.pz-b.pz, a.energy-b.energy};
}
inline double norm3(const FourMomentum& p) {
  return std::sqrt(p.px*p.px+p.py*p.py+p.pz*p.pz);
}
inline double dot3(const FourMomentum& a, const FourMomentum& b) {
  return a.px*b.px+a.py*b.py+a.pz*b.pz;
}
inline float positive_mass(const FourMomentum& p) {
  const double m2 = p.energy*p.energy-dot3(p,p);
  return std::isfinite(m2) && m2 >= 0. ? static_cast<float>(std::sqrt(m2)) : kMissing;
}
inline float cosine(const FourMomentum& a, const FourMomentum& b) {
  const double d = norm3(a)*norm3(b);
  return d > 0. ? static_cast<float>(std::clamp(dot3(a,b)/d,-1.,1.)) : kMissing;
}
inline double eta(const FourMomentum& p) {
  const double pt = std::hypot(p.px,p.py);
  return pt > 0. ? std::asinh(p.pz/pt) : std::numeric_limits<double>::quiet_NaN();
}
inline double delta_r(const FourMomentum& a, const FourMomentum& b) {
  const double ea=eta(a), eb=eta(b);
  if (!std::isfinite(ea) || !std::isfinite(eb))
    return std::numeric_limits<double>::infinity();
  const double dphi=std::atan2(std::sin(std::atan2(a.py,a.px)-std::atan2(b.py,b.px)),
                                std::cos(std::atan2(a.py,a.px)-std::atan2(b.py,b.px)));
  return std::hypot(ea-eb,dphi);
}
inline float estar(const FourMomentum& photon, const FourMomentum& parent) {
  const float m=positive_mass(parent);
  if (!(m > 0.f) || !(parent.energy > 0.)) return kMissing;
  const double value=(parent.energy*photon.energy-dot3(parent,photon))/m;
  return std::isfinite(value) ? static_cast<float>(value) : kMissing;
}

// Use the pinned FCCAnalyses thrust implementation on ROE after candidate
// removal. The existing event thrust includes daughters and is deliberately
// not reused here. This is a hemisphere split, not a kinematic fit.
inline FourMomentum roe_thrust_axis(const std::vector<FourMomentum>& roe) {
  if (roe.size()<2) return {};
  RVec<float> px,py,pz;
  px.reserve(roe.size());py.reserve(roe.size());pz.reserve(roe.size());
  for (const auto& p:roe) {
    px.push_back(p.px);py.push_back(p.py);pz.push_back(p.pz);
  }
  const auto result=Algorithms::calculate_thrust()(px,py,pz);
  if (result.size()<4 || !(result[0]>=0.f) ||
      !std::isfinite(result[1]) || !std::isfinite(result[2]) ||
      !std::isfinite(result[3])) return {};
  return {result[1],result[2],result[3],0.};
}

// Back-project the Lambda flight line from its SV and the photon direction
// from the PV. A neutral-photon origin is not measured by this Delphes output;
// this is an explicitly approximate pointing diagnostic, not a vertex fit.
inline std::array<float,3> pointing_proxy(const FourMomentum& lambda,
    const FourMomentum& gamma, const FourMomentum& lb,
    float pv_x,float pv_y,float pv_z,float sv_x,float sv_y,float sv_z) {
  const double ln=norm3(lambda), gn=norm3(gamma);
  if (!(ln>0. && gn>0.) || !std::isfinite(sv_x) || sv_x<=-998.)
    return {kMissing,kMissing,kMissing};
  const double ux=lambda.px/ln,uy=lambda.py/ln,uz=lambda.pz/ln;
  const double vx=gamma.px/gn,vy=gamma.py/gn,vz=gamma.pz/gn;
  const double wx=sv_x-pv_x,wy=sv_y-pv_y,wz=sv_z-pv_z;
  const double c=ux*vx+uy*vy+uz*vz, denom=1.-c*c;
  if (denom<1.e-6) return {kMissing,kMissing,kMissing};
  // Closest points on infinite lines: SV - t*u and PV + s*v.
  const double a=wx*ux+wy*uy+wz*uz, b=wx*vx+wy*vy+wz*vz;
  const double t=(a-c*b)/denom, s=(b-c*a)/denom;
  const double lx=wx-t*ux,ly=wy-t*uy,lz=wz-t*uz;
  const double gx=s*vx,gy=s*vy,gz=s*vz;
  const double dca=std::sqrt((lx-gx)*(lx-gx)+(ly-gy)*(ly-gy)+(lz-gz)*(lz-gz));
  const FourMomentum flight{(lx+gx)/2.,(ly+gy)/2.,(lz+gz)/2.,0.};
  return {static_cast<float>(dca),static_cast<float>(norm3(flight)),cosine(flight,lb)};
}

inline Result compute(const LbCandidateBuilder::Result& candidates,
    const RVec<edm4hep::ReconstructedParticleData>& particles,
    const RVec<edm4hep::TrackState>& tracks,
    const RVec<int>& selected_photons,const Config& config) {
  Result out;
  const FourMomentum pz{0.,0.,0.,config.ecm_gev};
  const double expected_est=(config.lb_mass_gev*config.lb_mass_gev-
      config.lambda_mass_gev*config.lambda_mass_gev)/(2.*config.lb_mass_gev);
  std::vector<bool> photon_mask(particles.size(),false);
  for (int index:selected_photons)
    if (index>=0 && static_cast<size_t>(index)<particles.size())
      photon_mask[index]=true;
  for (size_t slot=0;slot<candidates.lb_mass.size();++slot) {
    const int ip=candidates.lb_proton_index[slot];
    const int ii=candidates.lb_pion_index[slot];
    const int ig=candidates.lb_photon_index[slot];
    const int il=candidates.lb_lambda_slot[slot];
    const auto gamma=particle_p4(particles[ig]);
    // The fitted Lambda momentum is saved by the existing builder at the
    // same point as the Lambda_b mass calculation. Never fall back to raw
    // track momenta for these mass and recoil diagnostics.
    FourMomentum lambda{candidates.lb_lambda_px[slot],
                        candidates.lb_lambda_py[slot],
                        candidates.lb_lambda_pz[slot],0.};
    const double lambda_p2=dot3(lambda,lambda);
    lambda.energy=std::sqrt(lambda_p2+
        double(candidates.lb_lambda_mass[slot])*candidates.lb_lambda_mass[slot]);
    const auto sig=lambda+gamma;
    out.m_LamGam.push_back(candidates.lb_mass[slot]);
    const double gamma_pt=std::hypot(gamma.px,gamma.py);
    std::array<double,3> sumpt{},sumE{};
    double noL03=0.,noL05=0.,noL03E=0.,noL05E=0.;
    double charged=0.,neutral=0.,chargedE=0.,neutralE=0.;
    int n03=0,n05=0,best_index=-1;
    std::vector<float> other_gamma_masses;
    std::vector<int> other_gamma_indices;
    std::vector<float> same_hemi_all_masses,same_hemi_selected_masses;
    std::vector<int> same_hemi_all_indices,same_hemi_selected_indices;
    std::array<std::array<Activity,3>,6> activity{},lambda_activity{};
    const std::array<double,6> radii={config.cone_r02,config.cone_r03,
        config.cone_r05,config.cone_r07,config.cone_r10,config.cone_r20};
    const double lambda_event_side=candidates.thrust_x*lambda.px+
        candidates.thrust_y*lambda.py+candidates.thrust_z*lambda.pz;
    double best_dm=std::numeric_limits<double>::infinity();
    float best_mass=kMissing,best_dr=kMissing,best_energy=kMissing;
    FourMomentum roe_all{};
    FourMomentum original_opp{};
    int original_opp_n=0;
    std::vector<FourMomentum> roe;
    roe.reserve(particles.size());
    for (size_t j=0;j<particles.size();++j) {
      if (static_cast<int>(j)==ig) continue;
      const auto q=particle_p4(particles[j]);
      if (particles[j].type == 22) {
        const float pair_mass=positive_mass(gamma + q);
        other_gamma_masses.push_back(pair_mass);
        other_gamma_indices.push_back(static_cast<int>(j));
        const double partner_side=candidates.thrust_x*q.px+
            candidates.thrust_y*q.py+candidates.thrust_z*q.pz;
        if (lambda_event_side*partner_side>0. && pair_mass>=0.f) {
          same_hemi_all_masses.push_back(pair_mass);
          same_hemi_all_indices.push_back(static_cast<int>(j));
          if (photon_mask[j]) {
            same_hemi_selected_masses.push_back(pair_mass);
            same_hemi_selected_indices.push_back(static_cast<int>(j));
          }
        }
      }
      if (static_cast<int>(j)!=ip && static_cast<int>(j)!=ii) {
        roe_all=roe_all+q;
        if (norm3(q)>0. && std::isfinite(q.energy)) roe.push_back(q);
        const double other_side=candidates.thrust_x*q.px+
            candidates.thrust_y*q.py+candidates.thrust_z*q.pz;
        if (lambda_event_side*other_side<0. && std::isfinite(q.px) &&
            std::isfinite(q.py) && std::isfinite(q.pz) &&
            std::isfinite(q.energy)) {
          original_opp=original_opp+q;
          ++original_opp_n;
        }
      }
      const double dr=delta_r(gamma,q);
      const double partner_side=candidates.thrust_x*q.px+
          candidates.thrust_y*q.py+candidates.thrust_z*q.pz;
      // Both isolation centers use the fitted Lambda hemisphere. Charged
      // activity excludes the Lambda daughters, neutral activity excludes
      // the candidate photon, and all activity excludes all three daughters.
      // Legacy ratio branches below retain their old definition.
      if (lambda_event_side*partner_side>0. && std::isfinite(q.px) &&
          std::isfinite(q.py) && std::isfinite(q.pz) &&
          std::isfinite(q.energy)) {
        const bool charged_object=particles[j].charge!=0.f;
        const bool include_charged=charged_object &&
            static_cast<int>(j)!=ip && static_cast<int>(j)!=ii;
        const bool include_neutral=!charged_object && static_cast<int>(j)!=ig;
        const bool include_all=static_cast<int>(j)!=ip &&
            static_cast<int>(j)!=ii && static_cast<int>(j)!=ig;
        const std::array<double,2> center_dr={dr,delta_r(lambda,q)};
        for (size_t center=0;center<center_dr.size();++center) {
          auto& center_activity=center==0 ? activity : lambda_activity;
          for (size_t cone=0;cone<radii.size();++cone) {
            if (!(center_dr[center]<radii[cone])) continue;
            for (int cls=0;cls<3;++cls) {
              if ((cls==0 && !include_all) ||
                  (cls==1 && !include_charged) ||
                  (cls==2 && !include_neutral)) continue;
              auto& item=center_activity[cone][cls];
              item.px+=q.px;item.py+=q.py;item.pz+=q.pz;
              item.energy+=q.energy;++item.n;
            }
            if (include_charged && candidates.pv_valid &&
                particles[j].tracks_end>particles[j].tracks_begin &&
                particles[j].tracks_begin<tracks.size()) {
              const auto& track=tracks[particles[j].tracks_begin];
              const double d0=track.D0+candidates.pv_x*std::sin(track.phi)-
                  candidates.pv_y*std::cos(track.phi);
              if (std::isfinite(d0)) {
                auto& charged_activity=center_activity[cone][1];
                const double absolute=std::abs(d0);
                charged_activity.min_d0=std::min(charged_activity.min_d0,d0);
                charged_activity.max_d0=std::max(charged_activity.max_d0,d0);
                charged_activity.min_absd0=std::min(charged_activity.min_absd0,absolute);
                charged_activity.max_absd0=std::max(charged_activity.max_absd0,absolute);
                ++charged_activity.n_d0;
              }
            }
          }
        }
      }
      const double pt=std::hypot(q.px,q.py);
      if (dr<config.cone_r05) {
        sumpt[2]+=pt; sumE[2]+=q.energy;
        if (static_cast<int>(j)!=ip && static_cast<int>(j)!=ii) {
          noL05+=pt; noL05E+=q.energy;
        }
        if (dr<config.cone_r03) {
          sumpt[1]+=pt;sumE[1]+=q.energy;
          if (static_cast<int>(j)!=ip && static_cast<int>(j)!=ii) {
            noL03+=pt;noL03E+=q.energy;
            if (particles[j].charge==0.f) {neutral+=pt;neutralE+=q.energy;}
            else {charged+=pt;chargedE+=q.energy;}
          }
          if (photon_mask[j]) ++n03;
          if (dr<config.cone_r02) {sumpt[0]+=pt;sumE[0]+=q.energy;}
        }
        if (photon_mask[j]) ++n05;
      }
      // A pi0 partner must be selected and in the fitted-Lambda thrust
      // hemisphere; it may lie outside the isolation cones.
      if (photon_mask[j]) {
        const float mass=positive_mass(gamma+q);
        if (lambda_event_side*partner_side>0. && mass>=0.f &&
            std::abs(mass-config.pi0_mass_gev)<best_dm) {
          best_dm=std::abs(mass-config.pi0_mass_gev);
          best_index=static_cast<int>(j);best_mass=mass;
          best_dr=static_cast<float>(dr);best_energy=q.energy;
        }
      }
    }
    const auto ratio=[&](double numerator,double denominator) {
      return denominator>0. && std::isfinite(numerator) ?
          static_cast<float>(numerator/denominator) : kMissing;
    };
    // The EDM4hep output of the pinned IDEA card has no IsolationVar branch.
    // Keep an explicit unavailable flag rather than equating it with zero.
    out.iso_delphes.push_back(kMissing);out.iso_delphes_available.push_back(0);
    out.iso_R02.push_back(ratio(sumpt[0],gamma_pt));
    out.iso_R03.push_back(ratio(sumpt[1],gamma_pt));
    out.iso_R05.push_back(ratio(sumpt[2],gamma_pt));
    out.iso_R02_E.push_back(ratio(sumE[0],gamma.energy));
    out.iso_R03_E.push_back(ratio(sumE[1],gamma.energy));
    out.iso_R05_E.push_back(ratio(sumE[2],gamma.energy));
    out.iso_R03_noLambda.push_back(ratio(noL03,gamma_pt));
    out.iso_R05_noLambda.push_back(ratio(noL05,gamma_pt));
    out.iso_R03_noLambda_E.push_back(ratio(noL03E,gamma.energy));
    out.iso_R05_noLambda_E.push_back(ratio(noL05E,gamma.energy));
    out.iso_charged.push_back(ratio(charged,gamma_pt));
    out.iso_neutral.push_back(ratio(neutral,gamma_pt));
    out.iso_charged_E.push_back(ratio(chargedE,gamma.energy));
    out.iso_neutral_E.push_back(ratio(neutralE,gamma.energy));
    out.n_photons_DR03.push_back(n03);out.n_photons_DR05.push_back(n05);
    out.m_gg_best.push_back(best_mass);
    out.dm_gg_pi0.push_back(best_index>=0 ? best_dm : kMissing);
    out.E_gamma2.push_back(best_energy);out.dr_gg.push_back(best_dr);
    out.gamma2_index.push_back(best_index);
    out.gamma_combo_other_gamma_mass.push_back(std::move(other_gamma_masses));
    out.gamma_combo_other_gamma_index.push_back(std::move(other_gamma_indices));
    out.gamma_combo_same_hemi_all_mass.push_back(std::move(same_hemi_all_masses));
    out.gamma_combo_same_hemi_all_index.push_back(std::move(same_hemi_all_indices));
    out.gamma_combo_same_hemi_selected_mass.push_back(std::move(same_hemi_selected_masses));
    out.gamma_combo_same_hemi_selected_index.push_back(std::move(same_hemi_selected_indices));

    for (size_t center=0;center<2;++center) {
      const auto& center_activity=center==0 ? activity : lambda_activity;
      auto& px=center==0 ? out.iso_activity_px : out.lambda_iso_activity_px;
      auto& py=center==0 ? out.iso_activity_py : out.lambda_iso_activity_py;
      auto& pz=center==0 ? out.iso_activity_pz : out.lambda_iso_activity_pz;
      auto& p=center==0 ? out.iso_activity_p : out.lambda_iso_activity_p;
      auto& energy=center==0 ? out.iso_activity_energy : out.lambda_iso_activity_energy;
      auto& count=center==0 ? out.iso_activity_n : out.lambda_iso_activity_n;
      auto& d0_min=center==0 ? out.iso_charged_d0_min : out.lambda_iso_charged_d0_min;
      auto& d0_max=center==0 ? out.iso_charged_d0_max : out.lambda_iso_charged_d0_max;
      auto& absd0_min=center==0 ? out.iso_charged_absd0_min : out.lambda_iso_charged_absd0_min;
      auto& absd0_max=center==0 ? out.iso_charged_absd0_max : out.lambda_iso_charged_absd0_max;
      auto& n_d0=center==0 ? out.iso_charged_n_d0 : out.lambda_iso_charged_n_d0;
      for (size_t cone=0;cone<center_activity.size();++cone) {
        for (size_t cls=0;cls<3;++cls) {
          const auto& item=center_activity[cone][cls];
          px[cone][cls].push_back(static_cast<float>(item.px));
          py[cone][cls].push_back(static_cast<float>(item.py));
          pz[cone][cls].push_back(static_cast<float>(item.pz));
          p[cone][cls].push_back(static_cast<float>(
              std::sqrt(item.px*item.px+item.py*item.py+item.pz*item.pz)));
          energy[cone][cls].push_back(static_cast<float>(item.energy));
          count[cone][cls].push_back(item.n);
        }
        const auto& charged_activity=center_activity[cone][1];
        d0_min[cone].push_back(charged_activity.n_d0 ?
            static_cast<float>(charged_activity.min_d0) : kMissing);
        d0_max[cone].push_back(charged_activity.n_d0 ?
            static_cast<float>(charged_activity.max_d0) : kMissing);
        absd0_min[cone].push_back(charged_activity.n_d0 ?
            static_cast<float>(charged_activity.min_absd0) : kMissing);
        absd0_max[cone].push_back(charged_activity.n_d0 ?
            static_cast<float>(charged_activity.max_absd0) : kMissing);
        n_d0[cone].push_back(charged_activity.n_d0);
      }
    }

    const FourMomentum proton{candidates.lb_proton_px[slot],
        candidates.lb_proton_py[slot],candidates.lb_proton_pz[slot],0.};
    const FourMomentum pion{candidates.lb_pion_px[slot],
        candidates.lb_pion_py[slot],candidates.lb_pion_pz[slot],0.};
    const FourMomentum pair=proton+pion;
    const double pair_p2=dot3(pair,pair);
    const double proton_p2=dot3(proton,proton),pion_p2=dot3(pion,pion);
    out.arm_alpha.push_back(pair_p2>0. ? static_cast<float>(
        candidates.lb_sign[slot]*(proton_p2-pion_p2)/pair_p2) : kMissing);
    const double cx=proton.py*pion.pz-proton.pz*pion.py;
    const double cy=proton.pz*pion.px-proton.px*pion.pz;
    const double cz=proton.px*pion.py-proton.py*pion.px;
    out.arm_qt.push_back(pair_p2>0. ? static_cast<float>(
        std::sqrt(cx*cx+cy*cy+cz*cz)/std::sqrt(pair_p2)) : kMissing);

    const auto axis=roe_thrust_axis(roe);
    FourMomentum same{},other{};
    int nsame=0,nother=0;
    const double lambda_side=dot3(lambda,axis);
    for (const auto& q:roe) {
      if (lambda_side*dot3(q,axis)>=0.) {same=same+q;++nsame;}
      else {other=other+q;++nother;}
    }
    const auto rec=subtract(pz,other);
    const auto rec_all=subtract(pz,roe_all);
    const auto balance=subtract(sig+other,pz);
    const auto partial_balance=subtract(sig+original_opp,pz);
    const auto full_balance=subtract(sig+roe_all,pz);
    out.opp_hemi_px.push_back(original_opp.px);
    out.opp_hemi_py.push_back(original_opp.py);
    out.opp_hemi_pz.push_back(original_opp.pz);
    out.opp_hemi_p.push_back(norm3(original_opp));
    out.opp_hemi_energy.push_back(original_opp.energy);
    out.opp_hemi_n.push_back(original_opp_n);
    out.z_partial_deltaE.push_back(partial_balance.energy);
    out.z_partial_px.push_back(partial_balance.px);
    out.z_partial_py.push_back(partial_balance.py);
    out.z_partial_pz.push_back(partial_balance.pz);
    out.z_partial_deltaP.push_back(norm3(partial_balance));
    out.z_full_deltaE.push_back(full_balance.energy);
    out.z_full_px.push_back(full_balance.px);
    out.z_full_py.push_back(full_balance.py);
    out.z_full_pz.push_back(full_balance.pz);
    out.z_full_deltaP.push_back(norm3(full_balance));
    out.m_rec.push_back(positive_mass(rec));
    out.dm_rec.push_back(out.m_rec.back()>=0.f ?
        out.m_rec.back()-config.lb_mass_gev : kMissing);
    out.m_rec_all.push_back(positive_mass(rec_all));
    out.deltaE.push_back(balance.energy);
    out.px_bal.push_back(balance.px);out.py_bal.push_back(balance.py);
    out.pz_bal.push_back(balance.pz);out.deltaP.push_back(norm3(balance));
    out.cos_rec_sig.push_back(cosine(rec,sig));
    out.Estar_gamma.push_back(estar(gamma,sig));
    out.Estar_gamma_rec.push_back(estar(gamma,rec));
    out.dEstar.push_back(out.Estar_gamma.back()>=0.f ?
        out.Estar_gamma.back()-expected_est : kMissing);
    out.dEstar_rec.push_back(out.Estar_gamma_rec.back()>=0.f ?
        out.Estar_gamma_rec.back()-expected_est : kMissing);
    out.E_same.push_back(same.energy);out.m_same.push_back(positive_mass(same));
    const auto pointing=pointing_proxy(lambda,gamma,sig,candidates.pv_x,
        candidates.pv_y,candidates.pv_z,candidates.lambda_vertex_x[il],
        candidates.lambda_vertex_y[il],candidates.lambda_vertex_z[il]);
    out.dca_Lam_gamma.push_back(pointing[0]);
    out.Lxyz_implied.push_back(pointing[1]);
    out.cos_dir_implied.push_back(pointing[2]);
    const FourMomentum flight{candidates.lambda_vertex_x[il]-candidates.pv_x,
                              candidates.lambda_vertex_y[il]-candidates.pv_y,
                              candidates.lambda_vertex_z[il]-candidates.pv_z,0.};
    out.lambda_pv_cos.push_back(cosine(flight,lambda));
    const double lp=norm3(lambda);
    const double parallel=lp>0. ? dot3(flight,lambda)/lp : 0.;
    const double impact2=dot3(flight,flight)-parallel*parallel;
    out.lambda_pv_dca.push_back(lp>0. && std::isfinite(impact2) ?
        static_cast<float>(std::sqrt(std::max(0.,impact2))) : kMissing);
    out.roe_thrust_x.push_back(axis.px);out.roe_thrust_y.push_back(axis.py);
    out.roe_thrust_z.push_back(axis.pz);
    out.roe_n_other.push_back(nother);out.roe_n_same.push_back(nsame);
  }
  return out;
}

} // namespace FCCAnalyses::LbCandidateObservables
#endif

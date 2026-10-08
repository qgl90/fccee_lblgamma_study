"""Shared plotting style and labels for v3 offline candidate inspection."""

# Author: Renato Quagliani (rquaglia@cern.ch)

import mplhep as hep
import matplotlib.pyplot as plt
from cycler import cycler


plt.style.use(hep.style.LHCb1)
plt.rcParams["axes.prop_cycle"] = cycler(
    color=plt.rcParams["axes.prop_cycle"].by_key()["color"])
# The LHCb style requests Times New Roman, which is absent on the CERN worker.
# Keep the LHCb layout while choosing an installed serif font.
plt.rcParams["font.family"] = "DejaVu Serif"
plt.rcParams.update({
    "font.size": 11,
    "axes.titlesize": 11,
    "axes.labelsize": 10,
    "xtick.labelsize": 9,
    "ytick.labelsize": 9,
    "legend.fontsize": 9,
    "figure.titlesize": 13,
    "lines.marker": "",
})

DIAGNOSTIC_LABELS = {
    "d_pi0": "Closest same-hemisphere photon pair to π⁰ mass",
    "d_eta": "Closest same-hemisphere photon pair to η mass",
    "min_pair": "Lowest same-hemisphere photon-pair mass",
}


def diagnostic_axis_label(name):
    if name == "d_pi0":
        return "min over partners |m(γγ) − m(π⁰)| [GeV]"
    if name == "d_eta":
        return "min over partners |m(γγ) − m(η)| [GeV]"
    if name == "min_pair":
        return "min over partners m(γγ) [GeV]"
    return None

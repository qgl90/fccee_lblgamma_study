source /cvmfs/sw.hsf.org/spackages6/key4hep-stack/2022-12-23/x86_64-centos7-gcc11.2.0-opt/ll3gi/setup.sh
wget https://raw.githubusercontent.com/HEP-FCC/FCC-config/winter2023/FCCee/Generator/Pythia8/p8_ee_Zbb_ecm91_EVTGEN.cmd
wget https://raw.githubusercontent.com/HEP-FCC/FCC-config/winter2023/FCCee/Delphes/card_IDEA.tcl
wget https://raw.githubusercontent.com/HEP-FCC/FCC-config/winter2023/FCCee/Delphes/edm4hep_IDEA.tcl
wget https://raw.githubusercontent.com/HEP-FCC/FCC-config/winter2023/FCCee/Generator/EvtGen/DECAY.DEC
wget https://raw.githubusercontent.com/HEP-FCC/FCC-config/winter2023/FCCee/Generator/EvtGen/evt.pdl
wget https://raw.githubusercontent.com/HEP-FCC/FCC-config/winter2023/FCCee/Generator/EvtGen/Bu2TauNuTAUHADNU.dec
DelphesPythia8EvtGen_EDM4HEP_k4Interface card_IDEA.tcl edm4hep_IDEA.tcl \
p8_ee_Zbb_ecm91_EVTGEN.cmd Bu2TauNuTAUHADNU.root DECAY.DEC evt.pdl \
Bu2TauNuTAUHADNU.dec 521 Bu_SIGNAL 1

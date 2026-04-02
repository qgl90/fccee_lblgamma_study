From ```https://hep-fcc.github.io/fcc-tutorials/main/fast-sim-and-analysis/k4simdelphes/doc/starterkit/FccFastSimDelphes/Readme.html```


```source /cvmfs/sw.hsf.org/spackages6/key4hep-stack/2022-12-23/x86_64-centos7-gcc11.2.0-opt/ll3gi/setup.sh```

which DelphesPythia8EvtGen_EDM4HEP_k4Interface should show :
```/cvmfs/sw.hsf.org/spackages6/k4simdelphes/00-03-00/x86_64-centos7-gcc11.2.0-opt/pqqvt/bin/DelphesPythia8EvtGen_EDM4HEP_k4Interface```

Get locally some stuff needed
```
wget https://raw.githubusercontent.com/HEP-FCC/FCC-config/winter2023/FCCee/Generator/Pythia8/p8_ee_Zbb_ecm91_EVTGEN.cmd
wget https://raw.githubusercontent.com/HEP-FCC/FCC-config/winter2023/FCCee/Generator/Pythia8/p8_ee_ZH_ecm240.cmd
wget https://raw.githubusercontent.com/HEP-FCC/FCC-config/winter2023/FCCee/Generator/Pythia8/p8_ee_ZZ_ecm240.cmd
wget https://raw.githubusercontent.com/HEP-FCC/FCC-config/winter2023/FCCee/Generator/Pythia8/p8_ee_WW_ecm240.cmd
wget https://raw.githubusercontent.com/HEP-FCC/FCC-config/winter2023/FCCee/Delphes/card_IDEA.tcl
```

```
Usage: DelphesPythia8config_file output_config_file pythia_card output_file
config_file - configuration file in Tcl format,
output_config_file - configuration file steering the content of the edm4hep output in Tcl format,
pythia_card - Pythia8 configuration file,
output_file - output file in ROOT format.
```

```
wget https://raw.githubusercontent.com/HEP-FCC/FCC-config/winter2023/FCCee/Delphes/edm4hep_IDEA.tcl
```

The following commands will run Pythia8 and Delphes and produce the relevant signal and background samples:
```
DelphesPythia8_EDM4HEP card_IDEA.tcl edm4hep_IDEA.tcl p8_ee_ZH_ecm240.cmd p8_ee_ZH_ecm240_edm4hep.root
DelphesPythia8_EDM4HEP card_IDEA.tcl edm4hep_IDEA.tcl p8_ee_ZZ_ecm240.cmd p8_ee_ZZ_ecm240_edm4hep.root
DelphesPythia8_EDM4HEP card_IDEA.tcl edm4hep_IDEA.tcl p8_ee_WW_ecm240.cmd p8_ee_WW_ecm240_edm4hep.root
```



For custom evtgen:




```
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
```









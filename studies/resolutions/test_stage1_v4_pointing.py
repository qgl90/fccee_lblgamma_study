"""C++ geometry boundary tests and deterministic offline response checks."""
from pathlib import Path
import subprocess
import tempfile
import unittest
import numpy as np
import pyarrow as pa
from smear_stage1_v4_pointing import augment, PREFIX

class V4PointingTest(unittest.TestCase):
    def test_production_cpp_geometry(self):
        # Compile the actual pure geometry section without requiring ROOT/EDM4hep.
        header=(Path(__file__).resolve().parents[2]/'analysis/studies/photon_pointing_v4.h').read_text()
        geometry=header.split('constexpr double R=',1)[1].split('struct Labels',1)[0]
        code='#include <cmath>\n#include <limits>\n#include <cassert>\nconstexpr double R='+geometry+'''
int main() {
 auto h=intersect(2,3,4,1,0,0);
 assert(h.region==1 && std::abs(h.x-std::sqrt(R*R-9))<1e-9 && h.y==3 && h.z==4);
 assert(intersect(0,0,0,0,0,1).region==0); // central hole
 assert(intersect(0,0,0,300,0,2500).region==2);
 assert(intersect(0,0,0,300,0,-2500).z==-2500);
 assert(intersect(0,0,0,0,0,0).region==0);
 assert(intersect(0,0,0,2250,0,2500).region==1); // seam tie
 assert(intersect(3000,0,0,1,0,0).region==0); // outward outside
 assert(intersect(3000,0,0,-1,0,0).region==1); // inward outside
 assert(intersect(0,0,0,std::numeric_limits<double>::quiet_NaN(),1,1).region==0);
}
'''
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp);(path/'test.cc').write_text(code)
            subprocess.run(['g++','-std=c++17',str(path/'test.cc'),'-o',str(path/'test')],check=True)
            subprocess.run([str(path/'test')],check=True)

    def test_reused_photon_and_missing_match(self):
        data={'source_id':[1,1,1],'event_entry':[2,2,3],'photon_reco_index':[4,4,5],'lb_photon_energy':[10.,10.,10.]}
        values={'truth_px':10.,'truth_py':0.,'truth_pz':0.,'truth_hit_x':2250.,'truth_hit_y':3.,'truth_hit_z':4.,'pv_x':0.,'pv_y':0.,'pv_z':0.,'match_status':1.,'truth_hit_region':1.,'pv_valid':1.}
        data.update({PREFIX+k:[v,v,v] for k,v in values.items()})
        data[PREFIX+'match_status'][-1]=0
        table=pa.table(data);result=augment(table,'test')
        assert len(augment(table.slice(0,0),'test'))==0
        assert result['pointing_valid'].to_pylist()==[True,True,False]
        for key in result.column_names[len(table.column_names)+1:]:
            a=result[key].to_numpy();assert a[0]==a[1] and np.isnan(a[2])
        split=augment(table.slice(1,1),'test')
        assert split['photon_d0_abs_mm_0p5mrad'][0].as_py()==result['photon_d0_abs_mm_0p5mrad'][1].as_py()

if __name__=='__main__':unittest.main()

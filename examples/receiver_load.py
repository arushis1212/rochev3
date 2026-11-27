"""Reconstruct unilateral receiver and hook reactions for one stationary shared-load pose."""
import json
from pathlib import Path
import numpy as np
from scipy.optimize import nnls
from physics.roche_rod import energy_gradient


def replay(path=None):
    with np.load(path or Path(__file__).with_suffix('.npz'),allow_pickle=False) as d:
        q,s = d['q_mm'],d['yarn_s_mm']
        augmented=np.vstack((d['ghost_mm'][0],q,d['ghost_mm'][1]))
        _,gradient=energy_gradient(augmented,d['rest_mm'],d['EA_N'],d['B_Nmm2'])
        gradient[1:-1,2]+=d['weight_N']
        forces=gradient[2:-2].ravel()
        rows=[]; needle_gap=[]
        for mark,n,name in zip(d['contact_s_mm'],d['normal'],d['member']):
            j=np.searchsorted(s,mark,side='right')-1
            j=min(j,len(s)-2)
            t=(mark-s[j])/(s[j+1]-s[j])
            if not (0 <= t <= 1): raise ValueError('Unregistered contact')
            jac=np.zeros_like(q);jac[j]=(1-t)*n;jac[j+1]=t*n
            rows.append(jac[1:-1].ravel())
            if name=='fork':
                delta=(1-t)*q[j]+t*q[j+1]-d['needle_origin_mm']
                axial=delta@d['needle_axis']
                if not 0 < axial < d['needle_length_mm']: raise ValueError('Outside bearing span')
                radial=delta-axial*d['needle_axis']
                needle_gap.append(np.linalg.norm(radial)-d['needle_radius_mm']-d['yarn_radius_mm'])
        mat=np.array(rows).T
        pressure,_=nnls(mat,forces,maxiter=30000)
        return dict(gate_opening_mm=float(d['opening_mm']),
                    free_force_residual_nN=1e9*float(max(abs(forces-mat@pressure))),
                    needle_force_mN=1e3*float(pressure[d['member']=='fork'].sum()),
                    hook_body_force_mN=1e3*float(pressure[d['member']=='TOOL_H01_hook_body'].sum()),
                    main_gate_force_mN=1e3*float(pressure[d['member']=='TOOL_H02_gate'].sum()),
                    needle_skin_gap_mm=float(min(needle_gap)),free_nodes=len(q)-2)


if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pose",type=Path,nargs="?")
    print(json.dumps(replay(parser.parse_args().pose),indent=2))

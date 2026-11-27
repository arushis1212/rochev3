"""Reconstruct the mutual yarn contact and receiving-needle force in a transient handoff."""
import json
from pathlib import Path

import numpy as np
from scipy.optimize import nnls
from scipy.sparse import csr_matrix

from physics.roche_contact3d import closest_segments


def yarn_contact(x, nodes, radius):
    """Finite-segment normal and its force weights on both strands."""
    a,b,c,d=x[nodes]
    dist, normal, u, v = closest_segments(a[None],b[None],c[None],d[None])
    if dist[0] <= 0:
        raise ValueError("A zero-length contact normal has no direction")
    n=normal[0]/dist[0]
    row=np.zeros_like(x)
    np.add.at(row,nodes,np.array([1-u[0],u[0],v[0]-1,-v[0]])[:,None]*n)
    return row, float(dist[0]-2*radius)


def replay(path=None):
    with np.load(path or Path(__file__).with_suffix(".npz"),allow_pickle=False) as z:
        t=z["time_s"];xyz=z["coords_mm"];dt=np.diff(t)
        if not np.isfinite(dt).all() or np.any(dt<=0):
            raise ValueError("Increasing physical timestamps required")
        work=int(z["work_node_count"]); mass=z["mass_Ns2_mm"][:,None]
        v=np.concatenate([z["initial_velocity_mm_s"][None],np.diff(xyz,axis=0)/dt[:,None,None]])
        force=z["gradient_N"] + mass[None]*np.diff(v,axis=0)/dt[:,None,None]
        start=z["active_start"]; radii=float(z["radius_mm"])
        labels=z["member"]; ids=z["indices"]
        saved=csr_matrix((z["coefficient"],z["column"],z["row_start"]),shape=(len(labels),xyz.shape[1]*3))
        loads=np.zeros((len(dt),2)); peak_error=0.;worst_gap=0.;paired_force_error=0.
        for k,(lo,hi) in enumerate(zip(start,start[1:])):
            A=saved[lo:hi].toarray();kind=labels[lo:hi]
            for j in np.flatnonzero(kind=="yarn"):
                nodes=ids[lo+j]
                if not (np.all(nodes[:2]>=work) and np.all((nodes[2:]>=0)&(nodes[2:]<work))):
                    raise ValueError("Reciprocal yarn row does not span the two free material domains")
                J,g=yarn_contact(xyz[k+1],nodes,radii)
                if abs(g)>1.1e-7:
                    raise ValueError("A contact declared active is separated")
                A[j]=J.ravel();worst_gap=max(worst_gap,abs(g))
            rhs=force[k].ravel()
            reaction,_=nnls(A.T,rhs,maxiter=3000)
            loads[k]=[reaction[kind==i].sum() for i in ("yarn","needle")]
            peak_error=max(peak_error,float(np.max(abs(A.T@reaction-rhs))))
            for j in np.flatnonzero(kind=="yarn"):
                paired_force_error=max(paired_force_error,float(np.linalg.norm(A[j].reshape(-1,3).sum(0)*reaction[j])))
        def arrival(col):
            hits=np.flatnonzero(loads[:,col]>1e-9)
            return float(1e3*t[hits[0]+1]) if len(hits) else None
        def movement(q):
            return float(np.linalg.norm(q-q[0],axis=2).max())
        return dict(working_nodes=work,foundation_nodes=xyz.shape[1]-work,accepted_steps=len(dt),
                    start_ms=float(t[0]*1000),end_ms=float(t[-1]*1000),first_strand_contact_ms=arrival(0),
                    first_needle_contact_ms=arrival(1),end_needle_load_mN=float(1e3*loads[-1,1]),
                    needle_impulse_uNs=float(1e6*dt@loads[:,1]),yarn_normal_impulse_uNs=float(1e6*dt@loads[:,0]),
                    maximum_free_residual_uN=float(1e6*peak_error),maximum_active_yarn_gap_error_mm=worst_gap,
                    maximum_reciprocal_force_error_N=paired_force_error,
                    maximum_foundation_displacement_mm=movement(xyz[:,work:]),maximum_working_displacement_mm=movement(xyz[:,:work]))


if __name__=="__main__":
    print(json.dumps(replay(),indent=2))

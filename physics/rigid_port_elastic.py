"""Ideal rigid interface condensation for an elastic component sensitivity.

The port imposes rigid displacement on every selected interface node. It is
deliberately not a unilateral or frictional joint model.
"""
import time
import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.linalg import splu


def port_map(basis, fixed_dofs, port_dofs, origin_mm):
    n=basis.N
    def validated_dofs(value):
        array=np.asarray(value)
        if array.ndim!=1 or array.dtype.kind not in 'iu' or array.size==0:
            raise ValueError('Nonempty one-dimensional integer, non-bool DOFs required')
        if array.min()<0 or array.max()>=n:
            raise ValueError('DOFs outside displacement space')
        return np.unique(array.astype(np.int64))
    fixed=validated_dofs(fixed_dofs);port=validated_dofs(port_dofs)
    origin=np.asarray(origin_mm,float)
    if origin.shape!=(3,) or not np.isfinite(origin).all():
        raise ValueError('Finite origin and nonempty valid interfaces required')
    if len(np.intersect1d(fixed,port)):raise ValueError('Support and port overlap')
    components=basis.split_indices()
    coordinates=basis.doflocs[:,components[0]].T
    if any(not np.array_equal(coordinates,basis.doflocs[:,c].T)for c in components):
        raise ValueError('Three collocated displacement components required')
    nodes=np.flatnonzero(np.isin(components[0],port))
    if set(np.concatenate([c[nodes]for c in components]))!=set(port):
        raise ValueError('Every port node must contain all three displacement components')
    remainder=np.setdiff1d(np.arange(n),np.r_[fixed,port])
    rows=remainder.tolist();cols=list(range(len(remainder)));values=[1.]*len(remainder);blocks=[]
    for node in nodes:
        x,y,z=coordinates[node]-origin
        H=np.array([[1,0,0,0,z,-y],[0,1,0,-z,0,x],[0,0,1,y,-x,0]],float)
        blocks.append(H)
        for axis in range(3):
            for col in np.flatnonzero(H[axis]):
                rows.append(int(components[axis][node]));cols.append(len(remainder)+int(col));values.append(H[axis,col])
    stacked=np.vstack(blocks);scale=max(1.,float(np.max(np.linalg.norm(coordinates[nodes]-origin,axis=1))))
    if np.linalg.matrix_rank(stacked/np.array([1,1,1,scale,scale,scale]))<6:
        raise ValueError('Port geometry does not constrain six rigid modes')
    Q=coo_matrix((values,(rows,cols)),shape=(n,len(remainder)+6)).tocsr()
    return Q,dict(fixed_dofs=fixed,port_dofs=port,interior_dofs=remainder,
        port_origin_mm=origin,components=components,coordinates_mm=coordinates)


def factor_port(basis,stiffness,fixed_dofs,port_dofs,origin_mm):
    started=time.monotonic()
    Q,meta=port_map(basis,fixed_dofs,port_dofs,origin_mm)
    reduced=(Q.T@stiffness@Q).tocsc();assembled=time.monotonic();lu=splu(reduced)
    meta['factorization_statistics']=dict(full_dofs=int(basis.N),reduced_dofs=int(reduced.shape[0]),
        stiffness_nnz=int(stiffness.nnz),reduced_nnz=int(reduced.nnz),
        L_nnz=int(lu.L.nnz),U_nnz=int(lu.U.nnz),
        condensation_s=assembled-started,factor_s=time.monotonic()-assembled)

    def solve(body_load=None,port_wrench=None):
        body=np.zeros(basis.N)if body_load is None else np.asarray(body_load,float)
        wrench=np.zeros(6)if port_wrench is None else np.asarray(port_wrench,float)
        if body.shape!=(basis.N,) or wrench.shape!=(6,) or not np.isfinite(np.r_[body,wrench]).all():
            raise ValueError('Finite body vector and six-component port wrench required')
        rhs=Q.T@body;rhs[-6:]+=wrench
        v=lu.solve(rhs);u=Q@v
        residual=reduced@v-rhs
        bound=1e-8*max(1.,float(np.linalg.norm(rhs,ord=1)))
        if not np.isfinite(v).all() or abs(residual).max()>bound:raise ValueError('Unbalanced reduced solve')
        nodal=stiffness@u-body
        reaction=np.zeros_like(nodal);reaction[meta['fixed_dofs']]=nodal[meta['fixed_dofs']]
        xyz=meta['coordinates_mm'];components=meta['components']
        vector=lambda f:np.array([f[c]for c in components]).T
        applied=vector(body);r=vector(reaction)
        force=applied.sum(0)+r.sum(0)+wrench[:3]
        moment=np.cross(xyz,applied+r).sum(0)+np.cross(meta['port_origin_mm'],wrench[:3])+wrench[3:]
        energy=float(.5*u@(stiffness@u));work=float(body@u+wrench@v[-6:])
        if np.linalg.norm(force)>1e-7*max(1.,np.linalg.norm(rhs,1)) or np.linalg.norm(moment)>1e-6*max(1.,np.linalg.norm(rhs,1)):
            raise ValueError('Physical force or moment balance failed')
        if abs(2*energy-work)>1e-7*max(1.,abs(work)):raise ValueError('Energy/work mismatch')
        return dict(displacement=u,port_displacement=v[-6:],report=dict(
            reduced_residual_inf=float(abs(residual).max()),force_balance_N=force.tolist(),
            moment_balance_Nmm=moment.tolist(),strain_energy_Nmm=energy,external_work_Nmm=work,
            maximum_displacement_mm=float(np.linalg.norm(vector(u),axis=1).max()),
            ideal_joint_only=True,physical_admission=False))
    return solve,meta

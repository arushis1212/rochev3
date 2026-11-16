"""Safeguarded Newton for a local rod interior plus a small rigid-clamp border."""
import numpy as np
from scipy.linalg import cholesky_banded,cho_solve_banded,cho_factor,cho_solve
from physics.banded_newton import banded_hessian

def bordered_hessian(evaluate,x,interior,bandwidth=8,step=1e-6):
    def inner(y):
        E,g=evaluate(np.concatenate([y,x[interior:]]));return E,g[:interior]
    A=banded_hessian(inner,x[:interior],bandwidth,step)
    columns=[]
    for j in range(interior,len(x)):
        p=x.copy();m=x.copy();p[j]+=step;m[j]-=step
        columns.append((evaluate(p)[1]-evaluate(m)[1])/(2*step))
    border=np.column_stack(columns);B=border[:interior];C=border[interior:];C=(C+C.T)/2
    return A,B,C

def bordered_direction(A,B,C,gradient,damping=0.):
    H=A.copy();H[0]+=damping;factor=cholesky_banded(H,lower=True,check_finite=True)
    m=A.shape[1];z=cho_solve_banded((factor,True),gradient[:m]);W=cho_solve_banded((factor,True),B)
    S=C+damping*np.eye(len(C))-B.T@W;S=(S+S.T)/2
    cb=cho_solve(cho_factor(S,lower=True,check_finite=True),-gradient[m:]+B.T@z)
    return np.concatenate([-z-W@cb,cb])

def minimize_bordered(evaluate,start,interior,local_safe,gtol=1e-8,maxiter=200,step=1e-6,max_step=.25,callback=None):
    x=start.copy();E,g=evaluate(x);iterations=0;reason='iteration_limit';largest_damping=0.;fallbacks=0
    for iteration in range(maxiter):
        if np.max(abs(g))<=gtol:reason='force_residual';break
        local=local_safe(x)
        if local:A,B,C=bordered_hessian(evaluate,x,interior,8,step);scale=max(1.,float(np.max(abs(A[0]))),float(np.max(abs(np.diag(C)))))
        else:A=banded_hessian(evaluate,x,len(x)-1,step);scale=max(1.,float(np.max(abs(A[0]))));fallbacks+=1
        damping=0.;accepted=False
        for attempt in range(18):
            try:
                if local:direction=bordered_direction(A,B,C,g,damping)
                else:
                    H=A.copy();H[0]+=damping;factor=cholesky_banded(H,lower=True);direction=cho_solve_banded((factor,True),-g)
            except np.linalg.LinAlgError:
                damping=scale*1e-10 if damping==0 else damping*10;continue
            length=float(np.max(abs(direction)))
            if length>max_step:direction*=max_step/length
            slope=float(g@direction)
            if slope>=0:damping=scale*1e-10 if damping==0 else damping*10;continue
            alpha=1.
            for line in range(35):
                candidate=x+alpha*direction
                try:En,gn=evaluate(candidate)
                except ValueError:En=float('inf')
                if np.isfinite(En) and En<=E+1e-4*alpha*slope:accepted=True;break
                alpha*=.5
            if accepted:break
            damping=scale*1e-10 if damping==0 else damping*10
        if not accepted:reason='line_search';break
        x,E,g=candidate,En,gn;iterations+=1;largest_damping=max(largest_damping,damping)
        if callback is not None:callback(x,{'iterations':iterations,'energy_Nmm':float(E),'residual_N':float(np.max(abs(g)))})
    residual=float(np.max(abs(g)))
    return x,{'optimizer_success':residual<=gtol,'message':'force_residual' if residual<=gtol else reason,'iterations':iterations,'energy_Nmm':float(E),'free_node_residual_N':residual,'max_solver_damping_N_per_mm':largest_damping,'full_hessian_fallbacks':fallbacks}

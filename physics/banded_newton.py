"""Safeguarded Newton minimization for a verified local banded energy.
The caller must supply the true half-bandwidth. Damping is not added to energy.
"""
import numpy as np
from scipy.linalg import cholesky_banded,cho_solve_banded

def banded_hessian(evaluate,x,bandwidth,step=1e-5):
    n=len(x);b=min(bandwidth,n-1);H=np.zeros((2*b+1,n))
    # Rows influenced by two columns of one color are disjoint.
    for color in range(min(n,2*b+1)):
        columns=np.arange(color,n,2*b+1);plus=x.copy();minus=x.copy()
        plus[columns]+=step;minus[columns]-=step
        delta=(evaluate(plus)[1]-evaluate(minus)[1])/(2*step)
        for j in columns:
            rows=np.arange(max(0,j-b),min(n,j+b+1));H[b+rows-j,j]=delta[rows]
    lower=np.zeros((b+1,n));lower[0]=H[b]
    for d in range(1,b+1):lower[d,:n-d]=.5*(H[b+d,:n-d]+H[b-d,d:])
    return lower

def minimize_banded(evaluate,start,bandwidth,gtol=1e-7,maxiter=300,step=1e-5,max_step=.25):
    x=start.copy();E,g=evaluate(x);trace=[];reason='iteration_limit'
    for it in range(maxiter):
        residual=float(np.max(np.abs(g)))
        if residual<=gtol:reason='force_residual';break
        active_bandwidth=bandwidth(x) if callable(bandwidth) else bandwidth
        H=banded_hessian(evaluate,x,active_bandwidth,step);scale=max(1.,float(np.max(np.abs(H[0]))));damping=0.
        accepted=False
        for attempt in range(18):
            A=H.copy();A[0]+=damping
            try:
                C=cholesky_banded(A,lower=True,check_finite=True);direction=cho_solve_banded((C,True),-g)
            except np.linalg.LinAlgError:
                damping=scale*1e-10 if damping==0 else damping*10;continue
            length=float(np.max(np.abs(direction)))
            if length>max_step:direction*=max_step/length
            slope=float(np.dot(g,direction));alpha=1.
            if slope>=0:damping=scale*1e-10 if damping==0 else damping*10;continue
            for line in range(35):
                candidate=x+alpha*direction
                try:En,gn=evaluate(candidate)
                except ValueError:En=float('inf')
                if np.isfinite(En) and En<=E+1e-4*alpha*slope:
                    accepted=True;break
                alpha*=.5
            if accepted:break
            damping=scale*1e-10 if damping==0 else damping*10
        if not accepted:reason='line_search';break
        trace.append({'energy_Nmm':float(En),'residual_N':float(np.max(np.abs(gn))),'damping_N_per_mm':damping,'alpha':alpha})
        x,E,g=candidate,En,gn
    residual=float(np.max(np.abs(g)));success=residual<=gtol
    return x,{'optimizer_success':success,'message':'force_residual' if success else reason,'iterations':len(trace),'energy_Nmm':float(E),'free_node_residual_N':residual,'max_solver_damping_N_per_mm':max((t['damping_N_per_mm'] for t in trace),default=0),'energy_monotone':all(trace[i]['energy_Nmm']<=trace[i-1]['energy_Nmm']+1e-13 for i in range(1,len(trace)))}

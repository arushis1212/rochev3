"""Safeguarded Newton for a local rod interior plus a small rigid-clamp border."""
import numpy as np
from scipy.linalg import cholesky_banded,cho_solve_banded,cho_factor,cho_solve
from physics.banded_newton import banded_hessian
from physics.trust_damping import damping_from_config

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

def minimize_bordered(evaluate,start,interior,local_safe,gtol=1e-8,maxiter=200,step=1e-6,max_step=.25,callback=None,spectral=False,step_admissible=None,contact_event_limiter=None,damping_control=None,quasi_newton=None):
    if spectral not in (False,True,'absolute','absolute_damped'):raise ValueError('Unknown spectral search metric')
    from physics.guarded_bfgs import options_from_config,minimize_guarded_bfgs
    qn_options=options_from_config(quasi_newton)
    if qn_options is not None:
        if spectral!='absolute_damped':raise ValueError('Guarded BFGS requires the absolute_damped initial metric')
        def dense_hessian(y):
            local=local_safe(y)
            if local:A,B,C=bordered_hessian(evaluate,y,interior,8,step)
            else:A=banded_hessian(evaluate,y,len(y)-1,step)
            dense=np.zeros((len(y),len(y)));block=A.shape[1]
            for k in range(A.shape[0]):
                j=np.arange(block-k);dense[j+k,j]=A[k,:block-k];dense[j,j+k]=A[k,:block-k]
            if local:dense[:interior,interior:]=B;dense[interior:,:interior]=B.T;dense[interior:,interior:]=C
            return dense
        return minimize_guarded_bfgs(evaluate,start,dense_hessian,gtol=gtol,maxiter=maxiter,max_step=max_step,callback=callback,step_admissible=step_admissible,contact_event_limiter=contact_event_limiter,damping_control=damping_control,**qn_options)
    control=damping_from_config(damping_control)
    if control is not None and spectral!='absolute_damped':raise ValueError('Persistent damping requires the absolute_damped metric')
    x=start.copy();E,g=evaluate(x);iterations=0;reason='iteration_limit';largest_damping=0.;fallbacks=0
    for iteration in range(maxiter):
        if np.max(abs(g))<=gtol:reason='force_residual';break
        local=local_safe(x)
        if local:A,B,C=bordered_hessian(evaluate,x,interior,8,step);scale=max(1.,float(np.max(abs(A[0]))),float(np.max(abs(np.diag(C)))))
        else:A=banded_hessian(evaluate,x,len(x)-1,step);scale=max(1.,float(np.max(abs(A[0]))));fallbacks+=1
        spectral_direction=None
        if spectral:
            n=len(x);dense=np.zeros((n,n));block=A.shape[1]
            for k in range(A.shape[0]):
                j=np.arange(block-k);dense[j+k,j]=A[k,:block-k];dense[j,j+k]=A[k,:block-k]
            if local:dense[:interior,interior:]=B;dense[interior:,:interior]=B.T;dense[interior:,interior:]=C
            eig,V=np.linalg.eigh(dense);floor=max(1e-9,1e-12*float(np.max(abs(eig))));metric=np.maximum(np.abs(eig) if spectral in ('absolute','absolute_damped') else eig,floor);projected=V.T@g;spectral_direction=-V@(projected/metric)
        damping=control.next_damping if control is not None else 0.;accepted=False
        for attempt in range(18):
            try:
                if spectral=='absolute_damped':direction=-V@(projected/(metric+damping))
                elif spectral_direction is not None:direction=spectral_direction/(1+damping)
                elif local:direction=bordered_direction(A,B,C,g,damping)
                else:
                    H=A.copy();H[0]+=damping;factor=cholesky_banded(H,lower=True);direction=cho_solve_banded((factor,True),-g)
            except np.linalg.LinAlgError:
                damping=scale*1e-10 if damping==0 else damping*10;continue
            length=float(np.max(abs(direction)))
            if length>max_step:
                if spectral=='absolute_damped':
                    damping=scale*1e-10 if damping==0 else damping*10;continue
                direction*=max_step/length
            slope=float(g@direction)
            if slope>=0:damping=scale*1e-10 if damping==0 else damping*10;continue
            event=None;alpha=1.
            if contact_event_limiter is not None:
                event=contact_event_limiter(x,direction);alpha=float(event['alpha'])
                if not np.isfinite(alpha) or not 0<alpha<=1:raise ValueError('Contact event step fraction must be finite in (0,1]')
            for line in range(35):
                candidate=x+alpha*direction
                try:En,gn=evaluate(candidate)
                except ValueError:En=float('inf')
                roundoff=32*np.finfo(float).eps*max(1.,abs(E))
                force_improved=np.max(abs(g))<=1e-6 and np.max(abs(gn))<np.max(abs(g)) if np.isfinite(En) else False
                if np.isfinite(En) and (En<=E+1e-4*alpha*slope or (force_improved and En<=E+roundoff)):
                    if step_admissible is None or step_admissible(x,candidate):accepted=True;break
                alpha*=.5
            if accepted:break
            damping=scale*1e-10 if damping==0 else damping*10
        if not accepted:reason='line_search';break
        trust_update=None
        if control is not None:
            displacement=alpha*direction;coordinates=V.T@displacement
            # Use the original physical Hessian, not the absolute/damped metric,
            # to measure model agreement. Its eigenpairs are already available.
            predicted=-float(g@displacement)-.5*float(eig@(coordinates*coordinates))
            trust_update=control.update(used=damping,old_energy=E,new_energy=En,
                                        predicted_reduction=predicted,accepted_alpha=alpha,
                                        proposed_cap_alpha=event['alpha'] if event is not None else 1.,
                                        numerical_floor=floor,hessian_scale=scale)
        x,E,g=candidate,En,gn;iterations+=1;largest_damping=max(largest_damping,damping)
        if callback is not None:
            info={'iterations':iterations,'energy_Nmm':float(E),'residual_N':float(np.max(abs(g)))}
            if event is not None:
                # A capped trial still has to pass the original energy and path
                # checks. Backtracking can stop before the buffered event. Every
                # following outer iteration builds a fresh Hessian at accepted x.
                info['contact_event']={**event,'accepted_alpha':float(alpha),
                                       'accepted_at_event_cap':bool(event.get('event_found')and alpha==event['alpha']),
                                       'next_iteration_rebuilds_hessian':True}
            if trust_update is not None:info['damping_control']=trust_update
            callback(x,info)
    residual=float(np.max(abs(g)))
    result={'optimizer_success':residual<=gtol,'message':'force_residual' if residual<=gtol else reason,'iterations':iterations,'energy_Nmm':float(E),'free_node_residual_N':residual,'max_solver_damping_N_per_mm':largest_damping,'full_hessian_fallbacks':fallbacks}
    if control is not None:result['damping_control']=control.summary()
    return x,result

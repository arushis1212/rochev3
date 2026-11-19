"""Material-preserving nested refinement of a piecewise-linear yarn route."""
import numpy as np

def refine_material(q,rest,split,factor):
 q=np.asarray(q,dtype=float);rest=np.asarray(rest,dtype=float)
 if isinstance(factor,bool) or not isinstance(factor,(int,np.integer)) or factor<1:raise ValueError('factor must be a positive integer')
 if q.ndim!=2 or q.shape[1]!=3 or rest.shape!=(len(q)-1,)or not 0<split<len(q)-1 or np.any(rest<=0)or not np.isfinite(q).all()or not np.isfinite(rest).all():raise ValueError('invalid material chain')
 t=np.arange(factor)/factor
 new=(q[:-1,None,:]+t[None,:,None]*(q[1:]-q[:-1])[:,None,:]).reshape(-1,3)
 return np.vstack([new,q[-1]]),np.repeat(rest/factor,factor),split*factor

def refine_selected(q,rest,split,selected):
 """Bisect selected reference edges; retain every old material vertex exactly."""
 q=np.asarray(q,dtype=float);rest=np.asarray(rest,dtype=float)
 # Reuse the uniform routine's complete input validation without changing data.
 refine_material(q,rest,split,1)
 if any(isinstance(v,(bool,np.bool_))or not isinstance(v,(int,np.integer))or not 0<=v<len(rest)for v in selected):raise ValueError('selected edges must be valid integers')
 if len(set(selected))!=len(selected):raise ValueError('duplicate selected material edge')
 chosen=set(selected);points=[];lengths=[];old_index=[]
 for i in range(len(rest)):
  old_index.append(len(points));points.append(q[i])
  if i in chosen:points.append((q[i]+q[i+1])/2);lengths.extend([rest[i]/2,rest[i]/2])
  else:lengths.append(rest[i])
 old_index.append(len(points));points.append(q[-1])
 return np.asarray(points),np.asarray(lengths),old_index[split],np.array(old_index)

def refinement_indicators(q,rest,split,angle_degrees=5.,strain_threshold=.02,split_hinge=True):
 """A posteriori local angle/strain indicator, not a convergence certificate."""
 q=np.asarray(q);rest=np.asarray(rest);v=np.diff(q,axis=0);length=np.linalg.norm(v,axis=1);t=v/length[:,None];angle=np.arccos(np.clip(np.sum(t[:-1]*t[1:],axis=1),-1.,1.))
 if split_hinge:angle[split-1]=0.
 corners=np.flatnonzero(angle>np.deg2rad(angle_degrees));selected=set(int(i)for i in corners)|set(int(i+1)for i in corners);selected.update(int(i)for i in np.flatnonzero(abs(length/rest-1)>strain_threshold))
 return sorted(selected),{'maximum_turn_degrees':float(np.rad2deg(angle).max()),'maximum_absolute_strain':float(abs(length/rest-1).max()),'selected_edges':len(selected),'angle_threshold_degrees':angle_degrees,'strain_threshold':strain_threshold}

def remap_gripped_section(section,mapping,new_rest):
 """Refine only physical fixed spans; never attach newly inserted free-wrap nodes."""
 if 'gripped_edges'not in section:raise ValueError('Legacy fixed arc needs an explicit physical grip migration')
 mapping=np.asarray(mapping,dtype=int);fixed=dict(zip(section['indices'],section['body_xyz_mm']));new={int(mapping[i]):np.asarray(b,float)for i,b in fixed.items()};edges=[]
 for i in section['gripped_edges']:
  if i not in fixed or i+1 not in fixed:raise ValueError('Gripped edge must have both endpoints fixed')
  lo,hi=int(mapping[i]),int(mapping[i+1]);edges.extend(range(lo,hi))
  for j in range(lo+1,hi):new[j]=(1-(j-lo)/(hi-lo))*np.asarray(fixed[i])+(j-lo)/(hi-lo)*np.asarray(fixed[i+1])
 ids=sorted(new);s=np.r_[0.,np.cumsum(new_rest)]
 return{**section,'indices':ids,'body_xyz_mm':[new[i].tolist()for i in ids],'gripped_edges':edges,'material_coordinates_mm':s[ids].tolist()}

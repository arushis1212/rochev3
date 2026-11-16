"""Exact signed distance to the nominal concentric stock guide tubes."""
import numpy as np

def annular_cylinder(p,axis,origin,back,front,inner,outer):
    axis=np.asarray(axis,float);axis=axis/np.linalg.norm(axis);z=np.asarray(p)-origin;u=z@axis;radial=z-u[:,None]*axis;rho=np.linalg.norm(radial,axis=1)
    outside=rho-outer;inside=inner-rho;choose=outside>=inside;dr=np.maximum(outside,inside);nr=radial/np.maximum(rho[:,None],1e-14)*np.where(choose,1.,-1.)[:,None]
    da=np.abs(u-(back+front)/2)-(front-back)/2;na=np.where(u>=(back+front)/2,1.,-1.)[:,None]*axis
    d=np.column_stack([dr,da]);positive=np.maximum(d,0);length=np.linalg.norm(positive,axis=1);weights=np.zeros_like(d);ext=length>1e-14;weights[ext]=positive[ext]/length[ext,None];rows=np.flatnonzero(~ext);weights[rows,np.argmax(d[rows],axis=1)]=1
    return length+np.minimum(np.max(d,axis=1),0),weights[:,0,None]*nr+weights[:,1,None]*na

class GuidedContact:
    def __init__(self,base,tip,spec):
        self.base=base;self.tip=np.asarray(tip);a=np.deg2rad(spec['inclination_deg']);self.axis=np.array([0,-np.cos(a),-np.sin(a)])
        self.tubes=[(-spec['tube_length'],spec['inner_tube_front'],spec['tube_od']/2-spec['tube_wall'],spec['tube_od']/2)]
        for prefix in ['exit_insert','reducer','outer_tube']:
            self.tubes.append((spec[prefix+'_back'],spec[prefix+'_front'],spec[prefix+'_od']/2-spec[prefix+'_wall'],spec[prefix+'_od']/2))
    def tubes_distance(self,p):return [annular_cylinder(p,self.axis,self.tip,*tube) for tube in self.tubes]
    def edge_contact_terms(self,q,rest,counts,radius):
        from physics.edge_contact import edge_samples
        yield from self.base.edge_contact_terms(q,rest,counts,radius)
        for tube in self.tubes:
            back,front,inner,outer=tube
            ends=np.array([self.tip+back*self.axis,self.tip+front*self.axis]);extent=outer*np.sqrt(np.maximum(0,1-self.axis**2))
            edge,t,w,p=edge_samples(q,rest,counts,ends.min(axis=0)-extent,ends.max(axis=0)+extent,radius)
            if len(edge):
                d,g=annular_cylinder(p,self.axis,self.tip,*tube);yield edge,t,w,d,g
    def sparse_components(self,p,radius):
        from physics.sparse_contact import active_indices
        yield from self.base.sparse_components(p,radius)
        for tube in self.tubes:
            back,front,inner,outer=tube
            ends=np.array([self.tip+back*self.axis,self.tip+front*self.axis]);extent=outer*np.sqrt(np.maximum(0,1-self.axis**2))
            idx=active_indices(p,ends.min(axis=0)-extent,ends.max(axis=0)+extent,radius)
            if len(idx):
                d,g=annular_cylinder(p[idx],self.axis,self.tip,*tube);yield idx,d,g
    def components(self,p):return self.base.components(p)+self.tubes_distance(p)
    def contact_components(self,p,radius):return self.base.contact_components(p,radius)+self.tubes_distance(p)
    def distance(self,p):
        parts=self.components(p);d,g=parts[0]
        for x,n in parts[1:]:
            use=x<d;d[use]=x[use];g[use]=n[use]
        return d,g

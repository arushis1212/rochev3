"""Oriented crossings of an actual material-bound nonplanar triangle disk.

The virtual neck closure is reported explicitly. This is a diagnostic witness,
never a substitute for physical custody, forces or swept finite-yarn clearance.
"""
from dataclasses import dataclass
import numpy as np


def _material(q, s):
    q, s = np.asarray(q, float), np.asarray(s, float)
    if (q.ndim != 2 or q.shape[1] != 3 or s.shape != (len(q),)
            or len(q)<2 or not np.isfinite(q).all() or not np.isfinite(s).all()
            or np.any(np.diff(s)<=0)):
        raise ValueError('Finite ordered material coordinates and3D points required')
    return q, s


def _interval(q, s, interval):
    a,b = map(float,interval)
    if not np.isfinite([a,b]).all() or not s[0]<=a<b<=s[-1]:
        raise ValueError('Material interval must lie in the current reference domain')
    samples=np.r_[a,s[(s>a)&(s<b)],b]
    return np.column_stack([np.interp(samples,s,q[:,j])for j in range(3)]),samples


def _cross2(a,b):return float(a[0]*b[1]-a[1]*b[0])


def _point_segment(p,a,b):
    v=b-a;denom=float(v@v)
    if denom<=0:return float(np.linalg.norm(p-a))
    return float(np.linalg.norm(p-a-np.clip((p-a)@v/denom,0,1)*v))


def _barycentric(point,tri):
    u,v,w=tri[1]-tri[0],tri[2]-tri[0],point-tri[0]
    uu,uv,vv=float(u@u),float(u@v),float(v@v);denom=uu*vv-uv*uv
    if denom<=1e-30:return None
    b=(vv*(w@u)-uv*(w@v))/denom;c=(uu*(w@v)-uv*(w@u))/denom
    return np.array([1-b-c,b,c])


def _segments2(a,b,c,d,tol):
    """Closed segment intersections, including finite collinear overlap."""
    u,v=b-a,d-c;denom=_cross2(u,v)
    scale=max(np.linalg.norm(u),np.linalg.norm(v),1.)
    if abs(denom)>tol*scale:
        t=_cross2(c-a,v)/denom;w=_cross2(c-a,u)/denom
        if -tol<=t<=1+tol and -tol<=w<=1+tol:return [(float(np.clip(t,0,1)),a+np.clip(t,0,1)*u)]
        return []
    if abs(_cross2(c-a,u))>tol*scale:return []
    length=float(u@u)
    if length<=tol*tol:
        return [(0.,a)]if _point_segment(a,c,d)<=tol else []
    t0,t1=sorted((float((c-a)@u/length),float((d-a)@u/length)))
    lo,hi=max(0.,t0),min(1.,t1)
    if lo>hi+tol:return []
    return [(float(t),a+t*u)for t in (lo,hi)]


def _segment_triangle(a,b,tri,tol):
    """Return discrete hits or coplanar overlap, never silently ignore tangency."""
    n=np.cross(tri[1]-tri[0],tri[2]-tri[0]);norm=np.linalg.norm(n)
    if norm<=1e-20:return {'kind':'degenerate','points':[]}
    n/=norm;da,db=float((a-tri[0])@n),float((b-tri[0])@n)
    if abs(da)<=tol and abs(db)<=tol:
        axes=[j for j in range(3)if j!=int(np.argmax(abs(n)))];a2,b2=a[axes],b[axes];t2=tri[:,axes]
        parameters=[]
        for t,p in ((0.,a),(1.,b)):
            bary=_barycentric(p,tri)
            if bary is not None and np.min(bary)>=-tol:parameters.append(t)
        for c,d in zip(t2,np.roll(t2,-1,axis=0)):
            parameters.extend(t for t,_ in _segments2(a2,b2,c,d,tol))
        parameters=sorted(set(round(float(np.clip(t,0,1)),14)for t in parameters))
        return {'kind':'coplanar' if parameters else 'none',
                'points':[(t,a+t*(b-a),_barycentric(a+t*(b-a),tri))for t in parameters]}
    if (da>tol and db>tol)or(da<-tol and db<-tol):return {'kind':'none','points':[]}
    denominator=da-db
    if abs(denominator)<=1e-30:return {'kind':'none','points':[]}
    t=da/denominator
    if not -tol<=t<=1+tol:return {'kind':'none','points':[]}
    t=float(np.clip(t,0,1));point=a+t*(b-a);bary=_barycentric(point,tri)
    if bary is None or np.min(bary)<-tol:return {'kind':'none','points':[]}
    return {'kind':'hit','points':[(t,point,bary)],'sign':1 if db>da else -1}


def _ear_clip(points,tol):
    """Retain collinear boundary vertices; never introduce a virtual shortcut."""
    n=len(points);remaining=list(range(n));triangles=[]
    while len(remaining)>3:
        found=False
        for slot,index in enumerate(remaining):
            left,right=remaining[slot-1],remaining[(slot+1)%len(remaining)]
            a,b,c=points[[left,index,right]];area=_cross2(b-a,c-a)
            if area<=tol:continue
            blocked=False
            for other in remaining:
                if other in (left,index,right):continue
                p=points[other]
                if min(_cross2(b-a,p-a),_cross2(c-b,p-b),_cross2(a-c,p-c))>=-tol:
                    blocked=True;break
            if blocked:continue
            triangles.append((left,index,right));remaining.pop(slot);found=True;break
        if not found:raise ValueError('Reference boundary has no nondegenerate triangulation in selected projection')
    a,b,c=points[remaining]
    if _cross2(b-a,c-a)<=tol:raise ValueError('Degenerate final reference triangle')
    triangles.append(tuple(remaining));return np.asarray(triangles,dtype=int)


def _simple_polygon(points,tol):
    n=len(points)
    for i in range(n):
        if np.linalg.norm(points[(i+1)%n]-points[i])<=tol:return False
        for j in range(i+1,n):
            if j==i+1 or (i==0 and j==n-1):continue
            if _segments2(points[i],points[(i+1)%n],points[j],points[(j+1)%n],tol):return False
    return True


def _on_shared(point,vertices,shared,tol):
    if len(shared)==0:return False
    if len(shared)==1:return np.linalg.norm(point-vertices[shared[0]])<=tol
    if len(shared)==2:return _point_segment(point,vertices[shared[0]],vertices[shared[1]])<=tol
    return False


def surface_validation(vertices,triangles,*,position_tolerance=1e-8,minimum_double_area=1e-8):
    """Check every triangle pair, including overlap between adjacent faces."""
    vertices=np.asarray(vertices,float);triangles=np.asarray(triangles)
    if (vertices.ndim!=2 or vertices.shape[1]!=3 or not np.isfinite(vertices).all()
            or triangles.ndim!=2 or triangles.shape[1]!=3 or len(triangles)==0
            or triangles.dtype.kind not in 'iu' or np.any(triangles<0)or np.any(triangles>=len(vertices))
            or not np.isfinite([position_tolerance,minimum_double_area]).all()
            or min(position_tolerance,minimum_double_area)<=0):
        raise ValueError('Finite vertices, valid triangle indices and positive tolerances required')
    faces=vertices[triangles];areas=np.linalg.norm(np.cross(faces[:,1]-faces[:,0],faces[:,2]-faces[:,0]),axis=1)
    degenerate=np.flatnonzero(areas<=minimum_double_area).tolist()
    intersections=[];tol=position_tolerance
    lows,highs=faces.min(axis=1),faces.max(axis=1)
    if not degenerate:
        for i,ta in enumerate(faces):
            for j in range(i+1,len(faces)):
                if np.any(np.maximum(lows[i],lows[j])>np.minimum(highs[i],highs[j])+tol):continue
                shared=sorted(set(triangles[i])&set(triangles[j]));tb=faces[j];bad=[]
                for source,target in ((ta,tb),(tb,ta)):
                    for a,b in zip(source,np.roll(source,-1,axis=0)):
                        hits=_segment_triangle(a,b,target,tol)
                        for _,point,_ in hits['points']:
                            if not _on_shared(point,vertices,shared,tol*4):bad.append(point.tolist())
                if bad:intersections.append(dict(triangles=[i,j],points_mm=bad))
    return dict(valid=not degenerate and not intersections,minimum_double_area_mm2=float(areas.min()),
                degenerate_triangles=degenerate,self_intersections=intersections)


@dataclass
class MaterialAperture:
    boundary_s: np.ndarray
    triangles: np.ndarray
    orientation_normal: np.ndarray
    position_tolerance: float=1e-8
    minimum_double_area: float=1e-8
    boundary_tolerance: float=1e-8
    material_s_domain: tuple=None

    def __post_init__(self):
        self.boundary_s=np.array(self.boundary_s,float,copy=True)
        tri=np.asarray(self.triangles)
        if (self.boundary_s.ndim!=1 or len(self.boundary_s)<3 or not np.isfinite(self.boundary_s).all()
                or not(np.all(np.diff(self.boundary_s)>0)or np.all(np.diff(self.boundary_s)<0))
                or tri.ndim!=2 or tri.shape!=(len(self.boundary_s)-2,3)or tri.dtype.kind not in 'iu'
                or np.any(tri<0)or np.any(tri>=len(self.boundary_s))):
            raise ValueError('An oriented material boundary and a complete disk triangulation are required')
        directed={}
        for triangle in tri:
            if len(set(triangle))!=3:raise ValueError('Repeated triangle vertex')
            for a,b in zip(triangle,np.roll(triangle,-1)):
                edge=(int(a),int(b));directed[edge]=directed.get(edge,0)+1
        n=len(self.boundary_s)
        for a,b in directed:
            boundary=b==(a+1)%n
            opposite=a==(b+1)%n
            if boundary:
                if directed[a,b]!=1 or (b,a)in directed:raise ValueError('Invalid oriented disk boundary')
            elif opposite:raise ValueError('Reversed oriented boundary edge')
            elif directed[a,b]!=1 or directed.get((b,a))!=1:raise ValueError('Nonmanifold or inconsistent interior edge')
        if any((i,(i+1)%n)not in directed for i in range(n)):
            raise ValueError('Disk omits a physical boundary edge')
        for vertex in range(n):
            link={}
            for triangle in tri:
                if vertex not in triangle:continue
                a,b=[int(v)for v in triangle if v!=vertex]
                link.setdefault(a,set()).add(b);link.setdefault(b,set()).add(a)
            ends={(vertex-1)%n,(vertex+1)%n}
            if any(len(neighbors)!=(1 if node in ends else 2)for node,neighbors in link.items()):
                raise ValueError('Nonmanifold triangle fan at boundary material vertex')
            seen=set();pending=[next(iter(link))]
            while pending:
                node=pending.pop()
                if node in seen:continue
                seen.add(node);pending.extend(link[node]-seen)
            if len(seen)!=len(link):raise ValueError('Disconnected triangle fan at material vertex')
        normal=np.array(self.orientation_normal,float,copy=True)
        if normal.shape!=(3,)or not np.isfinite(normal).all()or np.linalg.norm(normal)<1e-12:
            raise ValueError('Finite orientation normal required')
        if not all(np.isfinite(v)and v>0 for v in(self.position_tolerance,self.minimum_double_area,self.boundary_tolerance)):
            raise ValueError('Positive finite geometry tolerances required')
        self.orientation_normal=normal/np.linalg.norm(normal);self.orientation_normal.setflags(write=False)
        if self.material_s_domain is not None:
            domain=np.asarray(self.material_s_domain,float)
            if domain.shape!=(2,)or not np.isfinite(domain).all()or not domain[0]<=min(self.boundary_s)<max(self.boundary_s)<=domain[1]:
                raise ValueError('Invalid material reference domain')
            self.material_s_domain=tuple(map(float,domain))
        self.triangles=np.array(tri,int,copy=True)
        self.boundary_s.setflags(write=False);self.triangles.setflags(write=False)

    @classmethod
    def bind(cls,reference_q,material_s,boundary_s_interval,orientation_normal,
             *,position_tolerance=1e-8,minimum_double_area=1e-8,boundary_tolerance=1e-8):
        q,s=_material(reference_q,material_s);boundary,bs=_interval(q,s,boundary_s_interval)
        normal=np.asarray(orientation_normal,float)
        if normal.shape!=(3,)or not np.isfinite(normal).all()or np.linalg.norm(normal)<1e-12:
            raise ValueError('Finite nonzero orientation normal required')
        if not all(np.isfinite(v)and v>0 for v in(position_tolerance,minimum_double_area,boundary_tolerance)):
            raise ValueError('Positive finite geometry tolerances required')
        normal/=np.linalg.norm(normal)
        axis=np.eye(3)[int(np.argmin(abs(normal)))];u=np.cross(axis,normal);u/=np.linalg.norm(u);v=np.cross(normal,u)
        points=np.column_stack([boundary@u,boundary@v])
        if not _simple_polygon(points,position_tolerance):raise ValueError('Reference projected boundary is not simple')
        area=sum(_cross2(a,b)for a,b in zip(points,np.roll(points,-1,axis=0)))
        if abs(area)<=minimum_double_area:raise ValueError('Reference aperture area vanishes')
        if area<0:points=points[::-1];boundary=boundary[::-1];bs=bs[::-1]
        triangles=_ear_clip(points,minimum_double_area)
        validity=surface_validation(boundary,triangles,position_tolerance=position_tolerance,minimum_double_area=minimum_double_area)
        if not validity['valid']:raise ValueError('Reference triangle disk is not embedded: '+str(validity))
        return cls(bs,triangles,normal,position_tolerance,minimum_double_area,boundary_tolerance,(float(s[0]),float(s[-1])))

    def vertices(self,q,material_s):
        q,s=_material(q,material_s)
        if self.material_s_domain is not None and not np.allclose([s[0],s[-1]],self.material_s_domain,rtol=0,atol=self.position_tolerance):
            raise ValueError('Material reference domain changed')
        if min(self.boundary_s)<s[0] or max(self.boundary_s)>s[-1]:raise ValueError('Aperture material domain lost')
        boundary=np.column_stack([np.interp(self.boundary_s,s,q[:,j])for j in range(3)])
        # New/remeshed material vertices must lie on the represented physical
        # boundary, otherwise this fixed surface has omitted a real bend.
        order=np.argsort(self.boundary_s);bs=self.boundary_s[order];bp=boundary[order]
        use=(s>=bs[0])&(s<=bs[-1]);represented=np.column_stack([np.interp(s[use],bs,bp[:,j])for j in range(3)])
        error=float(np.linalg.norm(represented-q[use],axis=1).max())
        if error>self.boundary_tolerance:raise ValueError('Remeshing introduced an unrepresented aperture boundary bend')
        return boundary

    def evaluate(self,q,material_s,passing_s_interval,*,centerline_margin_mm=.4,closure_margin_mm=.4):
        q,s=_material(q,material_s);vertices=self.vertices(q,s);tol=self.position_tolerance
        if not np.isfinite([centerline_margin_mm,closure_margin_mm]).all()or min(centerline_margin_mm,closure_margin_mm)<0:
            raise ValueError('Finite nonnegative witness margins required')
        validity=surface_validation(vertices,self.triangles,position_tolerance=tol,minimum_double_area=self.minimum_double_area)
        result=dict(surface=validity,crossings=[],ambiguities=[],incident_neck_endpoints=[],
                    virtual_closure=dict(material_s_endpoints=[float(self.boundary_s[-1]),float(self.boundary_s[0])],
                        points_mm=vertices[[-1,0]].tolist(),physical=False),
                    physical_custody_certified=False,continuous_history_certified=False)
        if not validity['valid']:
            result['witness_valid']=False;return result
        path,ps=_interval(q,s,passing_s_interval);hits=[];faces=vertices[self.triangles]
        from physics.roche_contact3d import closest_segments
        nseg=len(path)-1
        distances=closest_segments(path[:-1],path[1:],np.tile(vertices[-1],(nseg,1)),np.tile(vertices[0],(nseg,1)))[0]
        result['virtual_closure']['minimum_passing_path_distance_mm']=float(distances.min())
        result['virtual_closure']['path_separated']=bool(distances.min()>=closure_margin_mm)
        result['virtual_closure']['margin_required_mm']=float(closure_margin_mm)
        for edge,(a,b)in enumerate(zip(path[:-1],path[1:])):
            for triangle,face in enumerate(faces):
                if np.any(np.maximum(a,b)<face.min(axis=0)-tol)or np.any(np.minimum(a,b)>face.max(axis=0)+tol):continue
                found=_segment_triangle(a,b,face,tol)
                for fraction,point,bary in found['points']:
                    material=float(ps[edge]+fraction*(ps[edge+1]-ps[edge]))
                    # Exact shared material neck endpoints are incidences, not
                    # passages. No finite material interval is removed.
                    incident=any(abs(material-bs)<=tol and np.linalg.norm(point-vertex)<=tol
                                 for bs,vertex in zip(self.boundary_s[[0,-1]],vertices[[0,-1]]))
                    if incident:
                        result['incident_neck_endpoints'].append(material);continue
                    if abs(material-ps[0])<=tol or abs(material-ps[-1])<=tol:
                        result['ambiguities'].append(dict(kind='passing_interval_ends_on_surface',material_s_mm=material));continue
                    if found['kind']=='coplanar':
                        result['ambiguities'].append(dict(kind='coplanar',material_s_mm=material,triangle=triangle));continue
                    hits.append(dict(material_s_mm=material,point_mm=point.tolist(),sign=found['sign'],
                                     triangle=triangle,barycentric=bary.tolist()))
        hits.sort(key=lambda h:h['material_s_mm']);groups=[]
        for hit in hits:
            if groups and abs(hit['material_s_mm']-groups[-1][0]['material_s_mm'])<=tol:
                groups[-1].append(hit)
            else:groups.append([hit])
        for group in groups:
            signs=set(h['sign']for h in group);point=np.asarray(group[0]['point_mm']);material=group[0]['material_s_mm']
            physical=min(_point_segment(point,a,b)for a,b in zip(vertices[:-1],vertices[1:]))
            closure=_point_segment(point,vertices[-1],vertices[0])
            if len(signs)!=1:
                result['ambiguities'].append(dict(kind='tangent_or_mixed_seam',material_s_mm=material));continue
            if physical<centerline_margin_mm or closure<closure_margin_mm:
                result['ambiguities'].append(dict(kind='boundary_or_virtual_closure_margin',material_s_mm=material,
                    physical_boundary_distance_mm=physical,virtual_closure_distance_mm=closure));continue
            result['crossings'].append(dict(material_s_mm=material,point_mm=point.tolist(),sign=group[0]['sign'],
                triangles=sorted(set(h['triangle']for h in group)),barycentric=[h['barycentric']for h in group],
                physical_boundary_distance_mm=physical,virtual_closure_distance_mm=closure))
        result['incident_neck_endpoints']=sorted(set(result['incident_neck_endpoints']))
        result['witness_valid']=not result['ambiguities']
        return result

    def as_dict(self):
        return dict(schema='material-bound-aperture-v1',boundary_s_mm=self.boundary_s.tolist(),
                    triangles=self.triangles.tolist(),orientation_normal=self.orientation_normal.tolist(),
                    position_tolerance_mm=self.position_tolerance,minimum_double_area_mm2=self.minimum_double_area,
                    boundary_tolerance_mm=self.boundary_tolerance,material_s_domain=self.material_s_domain,
                    closure='Virtual neck chord; no physical custody')


def compare_passages(witness,expected_signs,*,material_s_windows=None,require_closure_path_clearance=True):
    """Check an event's declared passages, without awarding physical custody.

    An interval incident to a neck cannot claim global closure separation. Such
    a foundation-incidence diagnostic can be requested explicitly, but is not a
    separated working-bight passage certificate.
    """
    signs=list(expected_signs)
    if any(type(v)is not int or v not in(-1,1)for v in signs):raise ValueError('Oriented signs must be integer +/-1')
    crossings=witness['crossings'];actual=[h['sign']for h in crossings]
    reasons=[]
    if not witness['surface']['valid']or not witness['witness_valid']:reasons.append('invalid_or_ambiguous_surface_witness')
    if actual!=signs:reasons.append('oriented_passage_sequence_mismatch')
    if require_closure_path_clearance and not witness['virtual_closure'].get('path_separated',False):
        reasons.append('passing_material_not_separated_from_virtual_neck')
    if material_s_windows is not None:
        windows=np.asarray(material_s_windows,float)
        if windows.shape!=(len(signs),2)or not np.isfinite(windows).all()or np.any(windows[:,0]>windows[:,1]):
            raise ValueError('Finite ordered material windows must match expected passages')
        if len(crossings)!=len(windows)or any(not lo<=hit['material_s_mm']<=hi for hit,(lo,hi)in zip(crossings,windows)):
            reasons.append('material_identity_window_mismatch')
    return dict(passage_witness_passed=not reasons,reasons=reasons,expected_signs=signs,actual_signs=actual,
                closure_path_clearance_required=bool(require_closure_path_clearance),
                physical_custody_certified=False,continuous_history_certified=False)

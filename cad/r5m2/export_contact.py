"""Export exact line/circle planar CAD boundaries as bounded-error contact polygons."""
import sys,json,math,hashlib
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from cad.r5m2 import build as cad
from OCP.BRepTools import BRepTools_WireExplorer
from OCP.TopoDS import TopoDS

def wire_points(wire,axes,tol):
    exp=BRepTools_WireExplorer(wire.wrapped);points=[];segments=[]
    while exp.More():
        edge=cad.cq.Edge(TopoDS.Edge_s(exp.Current()));kind=edge.geomType()
        if kind=='LINE':n=1;bound=0.
        elif kind=='CIRCLE':
            radius=edge.radius();angle=edge.Length()/radius;n=max(1,math.ceil(angle/(2*math.acos(max(-1.,1-tol/radius)))));bound=radius*(1-math.cos(angle/(2*n)))
        else:raise ValueError('Unbounded curve tessellation:'+kind)
        pts=[edge.positionAt(i/n).toTuple() for i in range(n+1)]
        start=cad.cq.Vertex(exp.CurrentVertex()).Center().toTuple()
        if sum((a-b)**2 for a,b in zip(pts[-1],start))<sum((a-b)**2 for a,b in zip(pts[0],start)):pts.reverse()
        points.extend([[p[axes[0]],p[axes[1]]] for p in pts[:-1]]);segments.append({'curve':kind,'segments':n,'chord_error_bound_mm':bound});exp.Next()
    return {'points':points,'edges':segments}

def main():
    ps=cad.parts();tol=.001;profiles={}
    for name,normal_axis,axes in [('H01_hook_body',2,(0,1)),('H02_gate',1,(0,2))]:
        faces=[f for f in ps[name].faces().vals() if f.normalAt().toTuple()[normal_axis]>.999]
        face=max(faces,key=lambda f:f.Area());outer=wire_points(face.outerWire(),axes,tol);holes=[wire_points(w,axes,tol) for w in face.innerWires()]
        bb=ps[name].val().BoundingBox();bounds=[(bb.xmin,bb.xmax),(bb.ymin,bb.ymax),(bb.zmin,bb.zmax)]
        profiles[name]={'outer':outer,'holes':holes,'profile_axes':axes,'extrusion_axis':normal_axis,'extrusion_bounds_mm':bounds[normal_axis]}
    out=cad.ROOT/'cad/r5m2/generated/contact_profiles.json';out.write_text(json.dumps({'revision':cad.S['revision'],'spec_sha256':hashlib.sha256(cad.SPEC.read_bytes()).hexdigest(),'chord_error_bound_mm':tol,'profiles':profiles},indent=2)+'\n')
    print(json.dumps({k:{'outer_points':len(v['outer']['points']),'holes':len(v['holes'])} for k,v in profiles.items()}))
if __name__=='__main__':main()

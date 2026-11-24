"""Exact distributed normal reaction on a straight yarn segment at a planar face."""
import math


def segment_pressure(a, b, face_point, normal, radius, rest_length, stiffness):
    """Return (energy in N mm, forces on the two material nodes in N).

    The outward face normal has unit length. The centerline lies outside the solid
    and the contacting points project inside the finite plate face.
    """
    vectors = (a,b,face_point,normal)
    if any(len(v)!=3 or not all(math.isfinite(x) for x in v) for v in vectors):
        raise ValueError("Expected finite three-dimensional coordinates")
    if not math.isclose(sum(n*n for n in normal),1.0,rel_tol=1e-12):
        raise ValueError("Expected a unit normal")
    if not all(math.isfinite(x) and x>0 for x in (radius, rest_length, stiffness)):
        raise ValueError("Material parameters must be finite and positive")
    distances = [sum((x-p)*n for x,p,n in zip(end,face_point,normal)) for end in (a,b)]
    if min(distances)<0:
        raise ValueError("Centerline lies behind the face")
    ha, hb = (radius-d for d in distances)
    lo, hi = 0., 1.
    if max(ha,hb)<=0:
        return 0., ((0.,0.,0.),(0.,0.,0.))
    if ha<0:
        lo = -ha/(hb-ha)
    elif hb<0:
        hi = ha/(ha-hb)
    h0, h1 = max(ha,0.), max(hb,0.)
    width = hi-lo
    scale = stiffness*rest_length*width
    mean = (h0+h1)/2
    load = scale*mean
    # Integrate the linear shape functions times linear pressure on [lo, hi].
    at_b = scale*(lo*mean+width*(h0+2*h1)/6)
    energy = scale*(h0*h0+h0*h1+h1*h1)/6
    return energy, tuple(tuple(P*n for n in normal) for P in (load-at_b,at_b))

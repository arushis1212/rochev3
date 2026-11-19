"""Lower bound on yarn length through a circular guide, using only Python's stdlib."""
import json
import math
from pathlib import Path


def vector(values):
    values=tuple(values)
    if len(values)!=3 or not all(math.isfinite(x) for x in values):
        raise ValueError("Expected three finite coordinates")
    return values


def disk_distance(point, center, normal, radius):
    """Shortest Euclidean distance from a point to a filled disk."""
    point,center,normal=map(vector,(point,center,normal))
    mag=math.hypot(*normal)
    if mag==0 or not math.isfinite(radius) or radius<0:
        raise ValueError("The disk needs a nonzero normal and nonnegative radius")
    u=tuple(x/mag for x in normal)
    delta=tuple(p-c for p,c in zip(point,center))
    along=sum(d*n for d,n in zip(delta,u))
    radial=math.hypot(*(d-along*n for d,n in zip(delta,u)))
    return math.hypot(along,max(0.0,radial-radius))


def length_bound(anchors,center,normal,radius,position_uncertainty=0.0,roundoff_reserve=0.0):
    """Give a necessary length for two fixed points and a translated aperture."""
    if len(anchors)!=2 or any(not math.isfinite(x) or x<0 for x in (position_uncertainty,roundoff_reserve)):
        raise ValueError("Expected two anchors and nonnegative finite uncertainty")
    ends=[vector(p) for p in anchors]
    through=sum(disk_distance(p,center,normal,radius) for p in ends)
    # Translation of the disk changes each point's distance by at most its travel.
    return max(math.dist(*ends),through-2*position_uncertainty-roundoff_reserve)


def example():
    a=json.loads(Path(__file__).with_name("guide_travel.json").read_text())
    for label in ("start","end"):
        bound=length_bound(a["anchors"],a["disk_center_"+label],a["normal"],a["inner_radius"],
                           a["position_uncertainty"],a["roundoff_reserve"])
        print(f"{label}: minimum path {bound:.6f} mm, extra length above rest {max(0,bound-a['rest_length']):.6f} mm")


if __name__=="__main__":
    example()

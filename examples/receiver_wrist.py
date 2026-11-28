"""Replay continuous wrist clearance against STEP solids and installed component bounds."""
from pathlib import Path
import json

import cadquery as cq
import numpy as np
from scipy.spatial.transform import Rotation, Slerp

DATA = Path(__file__).resolve().parents[1] / "cad/receiver_wrist"


def components(path):
    return {name.rsplit("/",1)[-1]: shape.moved(location)
            for shape, name, location, _ in cq.Assembly.load(str(path))}


def bounds(shape):
    box = shape.BoundingBox()
    return np.array([[box.xmin, box.ymin, box.zmin], [box.xmax, box.ymax, box.zmax]])


def separation(left, right):
    return np.linalg.norm(np.maximum(0., np.maximum(left[0]-right[1], right[0]-left[1])))


def intervals_for(leg, rows):
    pieces = sorted(row["fractions"] for row in rows if row["leg"] == leg)
    start = 0.
    for low, high in pieces:
        if low != start or not low < high <= 1:
            raise ValueError("Wrist leg has incomplete or overlapping intervals")
        start = high
    if start != 1:
        raise ValueError("Wrist leg was not checked to its endpoint")
    return pieces


def replay(folder=DATA):
    data = json.loads((folder / "route.json").read_text())
    jaw = components(folder / "jaw.step")
    near = components(folder / "station.step")
    outside = data["other_component_bounds_mm"]
    if set(near) & set(outside) or len(near)+len(outside) != data["stock_count"]:
        raise ValueError("Installed component inventory differs")
    if set(jaw) != set(data["reference_radius_mm"]):
        raise ValueError("Moving component inventory differs")
    anchor = np.array(data["grip_local_mm"])
    radii = {name: np.linalg.norm(np.max(np.abs(bounds(sh)-anchor),axis=0)) for name,sh in jaw.items()}
    xyz = np.array(data["mark_xyz_mm"])
    envelope = np.array([xyz.min(0)-max(radii.values()), xyz.max(0)+max(radii.values())])
    vertical = set(data["vertically_mobile_components"])
    if not vertical <= set(outside):
        raise ValueError("Moving feeder components require their lateral bounds")
    far = min(separation(envelope[:,:2],np.array(box)[:,:2]) if name in vertical
              else separation(envelope,np.array(box)) for name,box in outside.items())
    rotation = Rotation.from_matrix([data["origin_basis"],data["destination_basis"]])
    slerp = Slerp([0.,1.],rotation)
    angle = (rotation[0].inv()*rotation[1]).magnitude()
    fractions = data["rotation_fraction"]
    if len(fractions)!=len(xyz) or fractions[0]!=0 or fractions[-1]!=1 or any(np.diff(fractions)<0):
        raise ValueError("Wrist rotation schedule differs")
    near_bounds = {name: bounds(sh) for name,sh in near.items()}
    guard = data["cad_guard_mm"]
    floor, count = far-guard, 0
    for leg, (a,b) in enumerate(zip(xyz,xyz[1:])):
        for low, high in intervals_for(leg, data["intervals"]):
            u = (low+high)/2
            h = high-low
            df = fractions[leg+1]-fractions[leg]
            basis = slerp([fractions[leg]+u*df]).as_matrix()[0]
            origin = a+u*(b-a)-basis@anchor
            location = cq.Location(cq.Plane(origin=tuple(origin),xDir=tuple(basis[:,0]),normal=tuple(basis[:,2])))
            for name, shape in jaw.items():
                posed = shape.moved(location)
                box = bounds(posed)
                # Maximum displacement of any point from the midpoint pose.
                pad = h*np.linalg.norm(b-a)/2 + 2*radii[name]*np.sin(h*df*angle/4) + guard
                for key, solid in near.items():
                    if separation(box,near_bounds[key])-pad < floor:
                        floor = min(floor, float(posed.distance(solid))-pad)
            count += 1
    if not np.isfinite(floor) or floor<=0:
        raise ValueError("Route lacks positive swept clearance")
    return dict(checked_components=len(near)+len(outside)+len(jaw), intervals=count,
                mark_path_length_mm=float(sum(np.linalg.norm(np.diff(xyz,axis=0),axis=1))),
                rotation_deg=float(np.rad2deg(angle)), minimum_swept_clearance_mm=float(floor))


if __name__ == "__main__":
    print(json.dumps(replay(),indent=2))

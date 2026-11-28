"""Replay the indexed cloth-support bearing against a registered, four-crossing yarn sample."""
from pathlib import Path
import json
import numpy as np

ASSETS = Path(__file__).resolve().parents[1] / 'cad' / 'indexed_latch'


def release_events(data, q, s):
    origin = np.asarray(data['opening_face_origin_mm'])
    axis = np.asarray(data['slide_axis'])
    lateral = np.asarray(data['tooth_axis'])
    normal = np.cross(axis, lateral)
    low, high = data['opening_axial_range_mm']
    events = []
    for name, (a, b) in data['material_ranges'].items():
        labels = np.r_[a, s[(s > a) & (s < b)], b]
        points = np.stack([np.interp(labels, s, v) for v in q.T], axis=1) - origin
        for i, (p, h) in enumerate(zip(points[:-1], np.diff(points, axis=0))):
            rate = h @ normal
            if abs(rate) < 1e-10:
                continue
            t = -(p @ normal) / rate
            where = p + t * h
            if (0 <= t < 1 and low < where @ axis < high
                    and 0 < where @ lateral < data['opening_span_mm']):
                events.append({'loop': name, 'stroke_mm': float(high - where @ axis),
                               'label_mm': float(labels[i] + t * (labels[i+1] - labels[i]))})
    return sorted(events, key=lambda event: event['stroke_mm'])


def replay_load(data):
    basis = np.column_stack([data['slide_axis'], data['tooth_axis'], data['swivel_axis']])
    gravity = (np.array([0., 0., -9.80665]) * data['rotor_mass_kg']) @ basis
    force = gravity.copy()
    moment = np.cross(data['rotor_centre_local_mm'], gravity)
    for contact in data['peak_load_case']['contacts']:
        f = np.asarray(contact['rotor_force_xyz_N']) @ basis
        force += f
        moment += np.cross(contact['surface_den_mm'], f)
    radius = data['dog_pitch_radius_mm']
    dog_force = -moment[2] / radius
    dog = np.array([0., dog_force, 0.])
    moment += np.cross([radius, 0., .2875], dog)
    thrust = np.array([0., 0., -force[2]])
    reaction = -force - dog - thrust
    a = data['radial_bearing_arm_mm']
    difference = np.array([-moment[1], moment[0], 0.]) / a
    front = (reaction + difference) / 2
    rear = (reaction - difference) / 2
    final_moment = moment + np.cross([0., 0., a], front - rear)
    peak_pressure = (2 * max(np.linalg.norm(front), np.linalg.norm(rear))
                     / (np.pi * data['journal_radius_mm'] * data['each_journal_length_mm']))
    return dict(dog_N=float(dog_force), max_radial_pressure_MPa=float(peak_pressure),
                force_error_N=float(np.linalg.norm(force + dog + thrust + front + rear)),
                moment_error_Nmm=float(np.linalg.norm(final_moment)))


def replay():
    data = json.loads((ASSETS / 'interface.json').read_text())
    with np.load(ASSETS / 'reference_yarn.npz') as z:
        events = release_events(data, z['positions_mm'], z['material_mm'])
    return dict(releases=events, load_case=replay_load(data))


def replay_brake(native=False):
    frame = json.loads((ASSETS / 'interface.json').read_text())
    spec = json.loads((ASSETS / 'brake' / 'configuration.json').read_text())
    basis = np.column_stack([frame['slide_axis'],frame['tooth_axis'],frame['swivel_axis']])
    masses, centres, parts = [], [], {}
    for item in spec['parts']:
        volume, center = item['volume_mm3'], item['cg_xyz_mm']
        if native:
            import cadquery as cq
            shape = cq.importers.importStep(str(ASSETS / item['file'])).val()
            volume, center = shape.Volume(), shape.Center().toTuple()
            parts[item['name']] = shape
        masses.append(volume * item['density_kg_mm3'])
        centres.append(center)
    eccentricity = (np.average(centres,axis=0,weights=masses) - spec['axis_point_mm']) @ basis
    signed, ejection = [], []
    for row in spec['sample_loads']:
        body = (np.array([0.,0.,-9.80665]) + row['slide_accel_mm_s2']*basis[:,0]/1000)
        moment = np.cross(spec['rotor_centre_den_mm'],(body*spec['rotor_mass_kg']) @ basis)
        for contact in row['yarn_contacts']:
            moment += np.cross(contact['surface_den_mm'],np.asarray(contact['rotor_force_xyz_N']) @ basis)
        pressure = -moment[2]/spec['index_pitch_radius_mm']
        signed.append(float(pressure))
        ejection.append(float(abs(pressure)*np.tan(np.deg2rad(spec['taper_half_angle_deg']))))
    area = np.pi * spec['rod_diameter_mm'] * spec['bond_engagement_mm']
    result = dict(moving_kg=float(sum(masses)), cam_design_kg=spec['nominal_cam_fork_mass_kg'],
                  transverse_centroid_error_mm=float(np.linalg.norm(eccentricity[1:])),
                  signed_pin_forces_N=signed, axial_ejection_forces_N=ejection,
                  pushrod_fivefold_average_bond_shear_MPa=float(5*spec['peak_rod_axial_force_N']/area))
    if native:
        origin = np.asarray(frame['origin_mm'])
        normal = basis[:,2]
        dog = parts['index_dog']
        rows = []
        for angle in (0.,-90.):
            rotor = parts['rotor'].rotate(tuple(origin),tuple(origin+normal),angle)
            def common_at(delta):
                part = rotor.rotate(tuple(origin),tuple(origin+normal),delta)
                return float(sum(v.Volume() for v in part.intersect(dog).Solids()))
            rows.append(dict(angle_deg=angle,common_mm3=common_at(0.),
                             plus_0p02_deg_mm3=common_at(.02),minus_0p02_deg_mm3=common_at(-.02),
                             released_gap_mm=rotor.distance(dog.translate(tuple(spec['stroke_length_mm']*normal)))))
        with np.load(ASSETS / 'reference_yarn.npz') as textile:
            q = textile['positions_mm']
        radius = frame['reference_yarn_radius_mm']
        stroke = -frame['slide_stroke_mm']*basis[:,0]
        result['locks'] = rows
        result['folded_rotor_to_yarn_mm'] = float(yarn_clearance(rotor,stroke,q,radius))
        result['trimmed_fork_to_yarn_mm'] = float(yarn_clearance(parts['fork'],stroke,q,radius))
    return result


def swept_edge(a, b, displacement):
    import cadquery as cq

    pts = np.array([a, b, b - displacement, a - displacement])
    if np.linalg.norm(np.cross(b - a, displacement)) < 1.e-9:
        projection = pts @ (b - a)
        return cq.Edge.makeLine(cq.Vector(*pts[np.argmin(projection)]),
                                cq.Vector(*pts[np.argmax(projection)]))
    return cq.Face.makeFromWires(cq.Wire.makePolygon([cq.Vector(*p) for p in pts],close=True))


def yarn_clearance(part, displacement, points, radius, cap=.20):
    box = part.BoundingBox()
    lo = np.array([box.xmin, box.ymin, box.zmin]) + np.minimum(0., displacement)
    hi = np.array([box.xmax, box.ymax, box.zmax]) + np.maximum(0., displacement)
    a, b = points[:-1], points[1:]
    wide = np.linalg.norm(np.maximum(0., np.maximum(lo-np.maximum(a,b), np.minimum(a,b)-hi)),axis=1)
    result = cap
    for i in np.flatnonzero(wide < radius + cap):
        result = min(result, part.distance(swept_edge(a[i],b[i],displacement)) - radius)
    return result


def replay_native():
    import cadquery as cq

    data = json.loads((ASSETS / 'interface.json').read_text())
    with np.load(ASSETS / 'reference_yarn.npz') as z:
        points = z['positions_mm']
    radius = data['reference_yarn_radius_mm']
    O, D, N = (np.asarray(data[name]) for name in ('origin_mm','slide_axis','swivel_axis'))
    parts = {name:cq.importers.importStep(str(ASSETS / (name+'.step'))).val()
             for name in ('fork','front_liner','back_liner','rotor','index_dog','gland')}
    dog = parts['index_dog']
    rotor = parts['rotor']
    spin = lambda shape, angle: shape.rotate(tuple(O),tuple(O+N),angle)
    def common(a,b):
        return sum(v.Volume() for v in a.intersect(b).Solids())
    locks = []
    for angle in (0., data['fold_degrees']):
        face = spin(rotor, angle)
        locks.append(dict(angle_deg=angle, gap_mm=dog.distance(face),
                          common_volume_mm3=common(dog,face),
                          overtravel_0p1_deg_mm3=common(dog,spin(rotor,angle-.10))))
    strokes = np.linspace(0.,data['fold_degrees'],91)
    turn_limit = .20
    for a, b in zip(strokes[:-1],strokes[1:]):
        middle = spin(rotor,(a+b)/2)
        pad = 2*data['indexed_rotor_radius_bound_mm']*np.sin(np.deg2rad(abs(b-a))/4)+1.e-7
        turn_limit = min(turn_limit,yarn_clearance(middle,np.zeros(3),points,radius)-pad)
    parts['rotor'] = spin(rotor,data['fold_degrees'])
    dr = -data['slide_stroke_mm']*D
    withdrawal = {k:yarn_clearance(sh,dr,points,radius) for k,sh in parts.items()}
    return dict(positive_locks=locks,swivel_yarn_floor_mm=float(turn_limit),
                withdraw_yarn_floor_mm=withdrawal, dog_motion_yarn_floor_mm=
                yarn_clearance(dog,data['dog_stroke_mm']*N,points,radius))


if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--native',action='store_true',help='also measure native STEP clearance using CadQuery')
    p.add_argument('--brake',action='store_true',help='also replay the tapered pin and mass-balanced cam variant')
    args = p.parse_args()
    result = replay()
    if args.native and not args.brake:
        result['native'] = replay_native()
    if args.brake:
        result['brake'] = replay_brake(native=args.native)
    print(json.dumps(result,indent=2))

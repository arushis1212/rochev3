"""One current physical assembly, without historical coupon simplifications.

The single-station module remains reproducible for archived diagnostic runs.
This module is the current manufacturing assembly and retains both service and
indexing hardware. Its inventory pose is not a validated operating trajectory.
"""
from functools import lru_cache
import hashlib
import json
import math
import numpy as np

from cad.r5m2 import build as base, service
from cad.transfer import build as transfer, indexed, installation

S = json.loads((base.ROOT / 'spec/current_machine.json').read_text())


@lru_cache(maxsize=1)
def parts():
    board = service.indexed_base_board(indexed.parts()['XT09_drilled_base'])
    return {'CM01_complete_base_board': base.cq.Workplane(obj=board)}


def installed(ps=None, tp=None, *, station_index=1, transfer_x=None,
              roll=20, advance=0., gate=16.5, lift=0., reset=0.,
              guide=None, head_tip=None, head_roll=None, support_q=None,
              support_gate_q=None, index_locked=True, dock_height=0.,
              feed_mode='high', carrier_z=160., inlet_nip='CLOSED',
              outlet_nip='OPEN', cradle_position='HIGH_RELEASE', cradle_angle=90.,
              cradle_indexed=False, clamp_pose=None):
    ps = base.parts() if ps is None else ps
    tp = transfer.parts() if tp is None else tp
    scene = indexed.installed(
        ps, tp, station_index=station_index, transfer_x=transfer_x,
        roll=roll, advance=advance, gate=gate, lift=lift, reset=reset,
        guide=guide, head_tip=head_tip, head_roll=head_roll, support_q=support_q,
        support_gate_q=support_gate_q,
        index_locked=index_locked, dock_height=dock_height,
        feed_mode=feed_mode, carrier_z=carrier_z)
    scene = service.install_nips(scene, inlet_nip, outlet_nip)
    stops = service.S['counterweight_cradle']['center_stops_mm']
    if isinstance(cradle_position, str):
        release = cradle_position.endswith('_RELEASE')
        position = cradle_position.removesuffix('_RELEASE')
        if position not in stops:
            raise ValueError('Unknown physical cradle detent')
        if release and cradle_indexed:
            raise ValueError('Cradle release position is between physical detents')
        cradle_z = stops[position] - (service.C['release_drop_mm'] if release else 0.)
    else:
        cradle_z = float(cradle_position)
    scene.update(service.installed(cradle_z, cradle_angle, cradle_indexed))
    scene['F03_base_board'] = parts()['CM01_complete_base_board'].val()
    if clamp_pose is not None:
        center, angles = clamp_pose
        scale = base.S['cloth_clamp']['angular_scale_mm']
        yaw, pitch, clamp_roll = np.asarray(angles) * 180 / math.pi / scale
        for name, shape in list(scene.items()):
            if name.startswith(('D01_', 'D02_', 'D03_', 'D04_',
                                'HW_M3x16_cloth_', 'HW_M3nut_cloth_')):
                shape = shape.translate((-150, -165, -installation.I['take_down_z_mm']))
                shape = shape.rotate((0, 0, 0), (1, 0, 0), float(clamp_roll))
                shape = shape.rotate((0, 0, 0), (0, 1, 0), float(-pitch))
                shape = shape.rotate((0, 0, 0), (0, 0, 1), float(yaw))
                scene[name] = shape.translate(tuple(center))
    return scene


def inventory_scene():
    p = S['inventory_pose']
    return installed(station_index=p['station_index'], roll=p['roll_deg'],
                     advance=p['advance_mm'], gate=p['main_gate_mm'],
                     lift=p['lift_mm'], reset=p['reset_mm'],
                     feed_mode=p['feed_mode'].lower(), carrier_z=p['carrier_z_mm'],
                     inlet_nip=p['inlet_nip'], outlet_nip=p['outlet_nip'],
                     cradle_position=p['cradle_position'],
                     cradle_angle=p['cradle_angle_deg'],
                     cradle_indexed=p['cradle_indexed'])


def export(output=None):
    output = base.ROOT / 'cad/machine/generated' if output is None else output
    output.mkdir(parents=True, exist_ok=True)
    scene = inventory_scene()
    assembly = base.cq.Assembly()
    rows = {}
    for name, shape in sorted(scene.items()):
        if not shape.isValid() or len(shape.Solids()) != 1:
            raise ValueError(f'Invalid installed solid: {name}')
        assembly.add(shape, name=name)
        b = shape.BoundingBox()
        rows[name] = {'volume_mm3': shape.Volume(),
                      'bounds_mm': [b.xmin, b.xmax, b.ymin, b.ymax, b.zmin, b.zmax]}
    assembly.save(str(output / 'machine.step'))
    sources = [base.ROOT / p for p in (
        'spec/current_machine.json', 'spec/r5_m2_fixture.json',
        'spec/d26_finished_interfaces.json', 'spec/effective.py',
        'spec/transfer_candidate.json', 'spec/transfer_interfaces.json',
        'spec/transfer_installation.json', 'spec/indexed_transfer.json',
        'spec/machine_service.json', 'cad/machine/assembly.py',
        'cad/r5m2/build.py', 'cad/r5m2/peripherals.py', 'cad/r5m2/service.py',
        'cad/transfer/build.py', 'cad/transfer/interfaces.py',
        'cad/transfer/installation.py', 'cad/transfer/indexed.py')]
    manifest = {'revision': S['revision'], 'assembly_solids': len(scene),
                'scope': S['scope'], 'inventory_pose': S['inventory_pose'],
                'source_hashes': {str(p.relative_to(base.ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in sources},
                'instances': rows}
    (output / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    print(json.dumps({'revision': S['revision'], 'solids': len(scene), 'output': str(output)}))


if __name__ == '__main__':
    export()

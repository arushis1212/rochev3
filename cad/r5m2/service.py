"""Native, dimensioned service hardware; no full-cycle qualification claim.

S3 implements the counterweight cradle and two service nips. Dimensions come from machine_service
and the existing manual-slide authority. This module does not mutate shared CAD.
"""
from functools import lru_cache
import json
import math
from pathlib import Path
import csv
import hashlib

from cad.r5m2 import build as base

SPEC_PATH = base.ROOT / 'spec/machine_service.json'
S = json.loads(SPEC_PATH.read_text())
C = S['counterweight_cradle']
cq = base.cq


def _z_box(bounds):
    return base.box(*bounds)


def _local_to_world(shape):
    return base.transformed(
        {'shape': shape}, C['rail_origin_xyz_mm'], C['rail_xdir'],
        C['rail_normal'])['shape']


def _turn(shape, angle):
    x, y = C['tray_pivot_xy_mm']
    return shape.rotate((x, y, 0), (x, y, 1), angle)


@lru_cache(maxsize=1)
def parts():
    """Manufactured component variants, before service-position translation."""
    b, cy, cz = base.box, base.cyl_y, base.cyl_z
    p = {}
    post = b(*C['upright_bbox_mm']).union(b(*C['foot_bbox_mm']))
    x = C['rail_origin_xyz_mm'][0]
    z0 = C['rail_origin_xyz_mm'][2]
    for z in [z0 + a for a in C['rail_mount_z_offsets_mm']]:
        post = post.cut(cy(C['upright_bbox_mm'][2] - 1, C['upright_bbox_mm'][3] + 1, base.P['bolt_clearance'] / 2, x, z))
    for z in C['center_stops_mm'].values():
        post = post.cut(cy(C['upright_bbox_mm'][2] - 1, C['upright_bbox_mm'][3] + 1, C['rail_index_bore_mm'] / 2, x, z))
    for bx, by in C['base_holes_xy_mm']:
        post = post.cut(cz(11, 21, C['base_hole_diameter_mm'] / 2, bx, by))
    sx, sy, sz = C['index_storage_underhead_xyz_mm']
    post = post.cut(cy(C['upright_bbox_mm'][2] - 1, C['upright_bbox_mm'][3] + 1, C['rail_index_bore_mm'] / 2, sx, sz))
    sx, sy, sz = C['tray_index_storage_underhead_xyz_mm']
    post = post.cut(cy(C['upright_bbox_mm'][2] - 1, C['upright_bbox_mm'][3] + 1, C['tray_index_bore_mm'] / 2, sx, sz))
    p['CS01_upright'] = post

    L = base.P['lengths'][C['rail_kind']]
    rail = base.slide_base(L).mirror('XZ')
    for z in C['center_stops_mm'].values():
        rail = rail.cut(cz(-1, base.P['floor_thickness'] + 1,
                           C['rail_index_bore_mm'] / 2, z - z0, 0))
    p['CS02_indexed_rail'] = rail
    p['CS03_indexed_carriage'] = base.slide_carriage().cut(
        cz(0, base.P['carriage_top'] + 1, C['carriage_index_bore_mm'] / 2))
    p['CS06_cap_L'] = base.slide_cap(L, -1)
    p['CS07_cap_R'] = base.slide_cap(L, 1)
    p['CS08_stop_L'] = base.slide_stop(L, -1)
    p['CS09_stop_R'] = base.slide_stop(L, 1)

    adapter = b(*C['adapter_bbox_relative_center_z_mm']).union(
        b(*C['adapter_shelf_bbox_relative_center_z_mm']))
    for z in C['adapter_mount_z_offsets_mm']:
        adapter = adapter.cut(cy(C['adapter_bbox_relative_center_z_mm'][2] - 1, C['adapter_bbox_relative_center_z_mm'][3] + 1, base.P['bolt_clearance'] / 2, x, z))
    adapter = adapter.cut(cy(C['adapter_bbox_relative_center_z_mm'][2] - 1, C['adapter_bbox_relative_center_z_mm'][3] + 1, C['index_access_bore_mm'] / 2, x, 0))
    px, py = C['tray_pivot_xy_mm']
    tray = b(*C['tray_bbox_relative_center_z_mm'])
    cx, cy0 = C['cup_center_xy_mm']
    top = C['tray_top_relative_center_z_mm']
    ring = cz(top, top + C['tray_ring_height_mm'], C['tray_ring_outer_radius_mm'], cx, cy0)
    ring = ring.cut(cz(top - 1, top + C['tray_ring_height_mm'] + 1,
                       C['tray_ring_inner_radius_mm'], cx, cy0))
    tray = tray.union(ring)
    for obj_name, obj in [('adapter', adapter), ('tray', tray)]:
        obj = obj.cut(cz(-25, -11, C['tray_pivot_bore_mm'] / 2, px, py))
        if obj_name == 'adapter':
            adapter = obj
        else:
            tray = obj
    dx, dy = C['tray_index_offset_xy_mm']
    tray = tray.cut(cz(-25, -11, C['tray_index_bore_mm'] / 2, px + dx, py + dy))
    for angle in (C['supported_angle_deg'], C['stowed_angle_deg']):
        a = math.radians(angle)
        ix = px + dx * math.cos(a) - dy * math.sin(a)
        iy = py + dx * math.sin(a) + dy * math.cos(a)
        adapter = adapter.cut(cz(-25, -11, C['tray_index_bore_mm'] / 2, ix, iy))
    p['CS04_adapter'] = adapter
    p['CS05_swivel_tray'] = tray
    return p


def base_hole_cutter():
    """Actual cutter for the existing F03 base; callers must apply this cut."""
    shapes = [base.cyl_z(-1, base.S['frame']['base_size'][2] + 1,
                         C['base_hole_diameter_mm'] / 2, x, y).val()
              for x, y in C['base_holes_xy_mm']]
    return cq.Compound.makeCompound(shapes)


def indexed_base_board(base_board):
    """Return a drilled copy, never mutate the supplied shared solid."""
    if isinstance(base_board, cq.Workplane):
        base_board = base_board.val()
    return base_board.cut(base_hole_cutter())


def installed(center_z=None, tray_angle_deg=0.0, vertical_index=True):
    """All 45 native solids; the loose vertical index is physically parked.

    center_z is the supported cup center if loaded. For release it is lowered
    three millimetres while the real cup remains suspended at its prior height.
    The tray's M2 angle index is present only at its two indexed angles; for an
    intermediate rotation it is parked in the upright's dedicated storage hole.
    """
    if center_z is None:
        center_z = C['center_stops_mm']['LOW']
    q = center_z - C['rail_origin_xyz_mm'][2]
    L = base.P['lengths'][C['rail_kind']]
    travel = (L - 2 * base.P['endstop_thickness'] - base.P['carriage_length']) / 2
    if abs(q) > travel + 1e-9:
        raise ValueError('Counterweight service carriage exceeds retained rail travel')
    if not (0 <= tray_angle_deg <= C['stowed_angle_deg']):
        raise ValueError('Tray angle outside adopted swivel path')
    if vertical_index and not any(abs(center_z - z) < 1e-7 for z in C['center_stops_mm'].values()):
        raise ValueError('Vertical index can only engage a manufactured index hole')
    p = parts()
    rail_items = {
        'CS02_indexed_rail': p['CS02_indexed_rail'].val(),
        'CS03_indexed_carriage': p['CS03_indexed_carriage'].val().translate((q, 0, 0)),
        **{name: p[name].val() for name in ('CS06_cap_L', 'CS07_cap_R', 'CS08_stop_L', 'CS09_stop_R')},
    }
    base.add_slide_hardware(rail_items, q, C['rail_kind'])
    result = {'SERVICE_' + name: _local_to_world(shape) for name, shape in rail_items.items()}
    result['SERVICE_CS01_upright'] = p['CS01_upright'].val()
    result['SERVICE_CS04_adapter'] = p['CS04_adapter'].val().translate((0, 0, center_z))
    result['SERVICE_CS05_swivel_tray'] = _turn(p['CS05_swivel_tray'].val(), tray_angle_deg).translate((0, 0, center_z))

    def screw(name, d, length, at, normal=(0, 0, 1), xdir=(1, 0, 0)):
        result['SERVICE_' + name] = base.place(base.bolt(d, length), at, xdir, normal)

    def nut(name, d, at, normal=(0, 0, 1), xdir=(1, 0, 0)):
        result['SERVICE_' + name] = base.place(base.nut(d), at, xdir, normal)

    x = C['rail_origin_xyz_mm'][0]
    z0 = C['rail_origin_xyz_mm'][2]
    for i, offset in enumerate(C['rail_mount_z_offsets_mm']):
        screw(f'HW_M3x16_rail_mount_{i}', 3, C['rail_mount_screw_length_mm'],
              (x, C['rail_mount_underhead_y_mm'], z0 + offset), (0, -1, 0))
        nut(f'HW_M3nut_rail_mount_{i}', 3, (x, C['upright_bbox_mm'][3], z0 + offset), (0, 1, 0))
    for i, (x0, y0) in enumerate(C['base_holes_xy_mm']):
        screw(f'HW_M3x25_base_{i}', 3, C['base_screw_length_mm'], (x0, y0, C['foot_bbox_mm'][5]))
        nut(f'HW_M3nut_base_{i}', 3, (x0, y0, C['base_nut_bottom_z_mm']))
    for i, offset in enumerate(C['adapter_mount_z_offsets_mm']):
        screw(f'HW_M3x16_adapter_{i}', 3, C['adapter_mount_screw_length_mm'],
              (x, C['adapter_mount_underhead_y_mm'], center_z + offset), (0, -1, 0))
    if vertical_index:
        screw('HW_M3x30_vertical_index', 3, C['index_screw_length_mm'],
              (x, C['index_pin_underhead_y_mm'], center_z), (0, -1, 0))
        nut('HW_M3nut_vertical_index', 3, (x, C['index_nut_back_y_mm'], center_z), (0, 1, 0))
    else:
        sx, sy, sz = C['index_storage_underhead_xyz_mm']
        screw('HW_M3x30_vertical_index', 3, C['index_screw_length_mm'], (sx, sy, sz), (0, 1, 0))
        nut('HW_M3nut_vertical_index', 3,
            (sx, C['upright_bbox_mm'][2] - base.S['fasteners']['M3']['nut_height_max'], sz), (0, 1, 0))
    px, py = C['tray_pivot_xy_mm']
    top = center_z + C['tray_top_relative_center_z_mm']
    screw('HW_M3x12_tray_pivot', 3, C['tray_pivot_screw_length_mm'], (px, py, top))
    nut('HW_M3nut_tray_pivot', 3, (px, py, center_z + C['tray_pivot_nut_bottom_relative_z_mm']))
    dx, dy = C['tray_index_offset_xy_mm']
    if tray_angle_deg in (0.0, C['stowed_angle_deg']):
        a = math.radians(tray_angle_deg)
        ix = px + dx * math.cos(a) - dy * math.sin(a)
        iy = py + dx * math.sin(a) + dy * math.cos(a)
        screw('HW_M2x12_tray_index', 2, C['tray_index_screw_length_mm'], (ix, iy, top))
        nut('HW_M2nut_tray_index', 2, (ix, iy, center_z + C['tray_index_hardware_bottom_relative_z_mm']))
    else:
        sx, sy, sz = C['tray_index_storage_underhead_xyz_mm']
        screw('HW_M2x12_tray_index', 2, C['tray_index_screw_length_mm'], (sx, sy, sz), (0, 1, 0))
        nut('HW_M2nut_tray_index', 2, (sx, C['tray_index_storage_nut_front_y_mm'], sz), (0, 1, 0))
    return result


def inventory(items=None):
    """Every installed solid has exactly one procurement/manufacturing ID."""
    items = installed() if items is None else items
    rows = []
    known = S['parts']
    for name, shape in items.items():
        key = name.removeprefix('SERVICE_')
        if key in known:
            part_id = key
        else:
            matches = [k for k in known if key.startswith(k + '_')]
            if len(matches) != 1:
                raise ValueError(f'Unmapped service solid: {name}, candidates={matches}')
            part_id = matches[0]
        bb = shape.BoundingBox()
        rows.append({'instance_id': name, 'part_id': part_id,
                     'volume_mm3': shape.Volume(), 'valid': shape.isValid(),
                     'bbox_mm': [bb.xmin, bb.xmax, bb.ymin, bb.ymax, bb.zmin, bb.zmax]})
    return rows


def interface_checks():
    """Analytical necessary conditions, explicitly separate from tests."""
    length = base.P['lengths'][C['rail_kind']]
    limit = (length - 2 * base.P['endstop_thickness'] - base.P['carriage_length']) / 2
    lower = min(C['center_stops_mm'].values()) - C['release_drop_mm']
    qlow = lower - C['rail_origin_xyz_mm'][2]
    projection = (C['base_screw_length_mm'] - C['foot_bbox_mm'][5]
                  + C['base_nut_bottom_z_mm'])
    return {
        'retained_travel_each_side_mm': limit,
        'lower_release_to_endstop_margin_mm': qlow + limit,
        'nominal_ring_release_clearance_mm': C['release_drop_mm'] - C['tray_ring_height_mm'],
        'admitted_cup_radial_clearance_mm': C['tray_ring_inner_radius_mm'] - C['admission']['cup_max_outer_diameter_mm'] / 2,
        'base_bolt_projection_mm': projection,
        'full_cycle_qualified': False,
    }


@lru_cache(maxsize=1)
def nip_parts():
    """Actual keyed mounts, retained jaws, metal pads, shoulders and open shims."""
    n = S['service_nips']
    original = base.peripherals.parts(base)
    b, cz, cy = base.box, base.cyl_z, base.cyl_y
    lower = original['P13_nip_lower']
    px, py = n['lower_pad_fix_xy_mm']
    lower = lower.cut(cz(231, 239, n['pad_fix_bore_diameter_mm'] / 2, px, py))
    px, py = n['upper_pad_fix_xy_mm']
    lower = lower.cut(cz(*n['lower_opposed_head_pocket_z_mm'], n['opposed_head_clearance_diameter_mm'] / 2, px, py))
    upper_z = n['upper_body_closed_bottom_z_mm']
    upper = b(*n['pad_bounds_xy_mm'], upper_z, upper_z + n['upper_body_thickness_mm'])
    for x, y in n['actuation_bolts_xy_mm']:
        upper = upper.cut(cz(upper_z - 1, upper_z + n['upper_body_thickness_mm'] + 1,
                             n['actuation_bore_diameter_mm'] / 2, x, y))
    px, py = n['upper_pad_fix_xy_mm']
    upper = upper.cut(cz(upper_z - 1, upper_z + n['upper_body_thickness_mm'] + 1,
                         n['pad_fix_bore_diameter_mm'] / 2, px, py))
    px, py = n['lower_pad_fix_xy_mm']
    upper = upper.cut(cz(*n['upper_opposed_head_pocket_z_mm'], n['opposed_head_clearance_diameter_mm'] / 2, px, py))
    pad_lower = b(*n['pad_bounds_xy_mm'], n['lower_body_top_z_mm'], n['lower_body_top_z_mm'] + n['pad_thickness_mm'])
    pad_upper = b(*n['pad_bounds_xy_mm'], upper_z - n['pad_thickness_mm'], upper_z)
    pads = []
    for kind, pad in [('lower', pad_lower), ('upper', pad_upper)]:
        for x, y in n['actuation_bolts_xy_mm']:
            pad = pad.cut(cz(237, 241, n['pad_shoulder_clearance_diameter_mm'] / 2, x, y))
        x, y = n[kind + '_pad_fix_xy_mm']
        pad = pad.cut(cz(237, 241, n['pad_fix_bore_diameter_mm'] / 2, x, y))
        x, y = n[('upper' if kind == 'lower' else 'lower') + '_pad_fix_xy_mm']
        pad = pad.cut(cz(237, 241, n['opposed_head_clearance_diameter_mm'] / 2, x, y))
        if kind in n['pad_corner_notches_xy_mm']:
            pad = pad.cut(b(*n['pad_corner_notches_xy_mm'][kind], 237, 241))
        if kind == 'upper':
            for slot in n['upper_pad_shim_entry_slots_xy_mm']:
                pad = pad.cut(b(*slot, 237, 241))
        pads.append(pad)

    shoulder = cz(0, n['shoulder_length_mm'], n['shoulder_od_mm'] / 2)
    shoulder = shoulder.cut(cz(-1, n['shoulder_length_mm'] + 1, n['shoulder_id_mm'] / 2))
    shim = cz(0, n['open_shim_thickness_mm'], n['open_shim_od_mm'] / 2)
    shim = shim.cut(cz(-1, n['open_shim_thickness_mm'] + 1, n['open_shim_bore_mm'] / 2))
    shim = shim.cut(b(-n['open_shim_od_mm'], 0, -n['open_shim_slot_width_mm'] / 2,
                      n['open_shim_slot_width_mm'] / 2, -1, n['open_shim_thickness_mm'] + 1))
    tower = original['P01_tower']
    inlet = lower
    for x, z in n['upstream_key_xz_mm']:
        inlet = inlet.union(b(x - n['key_width_mm'] / 2, x + n['key_width_mm'] / 2,
                              n['upstream_key_root_y_mm'] - .01, n['upstream_key_root_y_mm'] + n['key_projection_mm'],
                              z - n['key_height_mm'] / 2, z + n['key_height_mm'] / 2))
        tower = tower.cut(b(x - n['key_pocket_width_mm'] / 2, x + n['key_pocket_width_mm'] / 2,
                            n['upstream_key_root_y_mm'] - .01, n['upstream_key_root_y_mm'] + n['key_pocket_depth_mm'],
                            z - n['key_pocket_height_mm'] / 2, z + n['key_pocket_height_mm'] / 2))
    ref = n['reference_center_xyz_mm']
    out = n['installed_centers_xyz_mm']['OUT']
    delta = tuple(out[i] - ref[i] for i in range(3))
    outlet = lower.translate(delta)
    bracket = original['P10_fairlead_bracket'].union(b(*n['downstream_bracket_beam_bbox_mm'])).union(b(*n['downstream_bracket_connector_bbox_mm']))
    mz = out[2] + n['mount_z_relative_center_mm']
    bracket = bracket.cut(cy(415, 423, base.P['bolt_clearance'] / 2, out[0], mz))
    for x, z in n['downstream_key_xz_mm']:
        bracket = bracket.union(b(x - n['key_width_mm'] / 2, x + n['key_width_mm'] / 2,
                                  n['downstream_key_root_y_mm'] - n['key_projection_mm'], n['downstream_key_root_y_mm'] + .01,
                                  z - n['key_height_mm'] / 2, z + n['key_height_mm'] / 2))
        outlet = outlet.cut(b(x - n['key_pocket_width_mm'] / 2, x + n['key_pocket_width_mm'] / 2,
                              n['downstream_key_root_y_mm'] - n['key_pocket_depth_mm'], n['downstream_key_root_y_mm'] + .01,
                              z - n['key_pocket_height_mm'] / 2, z + n['key_pocket_height_mm'] / 2))
    return {'NS01_fairlead_bracket_extended': bracket, 'NS02_tower_keyed': tower,
            'NS03_inlet_lower': inlet, 'NS04_outlet_lower': outlet,
            'NS05_upper': upper, 'NS06_lower_pad': pads[0], 'NS07_upper_pad': pads[1],
            'NS08_shoulder': shoulder, 'NS09_open_shim': shim}


def nips_installed(in_state='CLOSED', out_state='OPEN', enforce_custody=True):
    """Two actual nips. OPEN is a translated retained jaw on physical shims."""
    n = S['service_nips']
    states = {'IN': in_state, 'OUT': out_state}
    if any(v not in ('OPEN', 'CLOSED') for v in states.values()):
        raise ValueError('Nip state must be OPEN or CLOSED')
    if enforce_custody and all(v == 'OPEN' for v in states.values()):
        raise ValueError('Service custody forbids both nips OPEN')
    ps = nip_parts()
    result = {'NIP_' + name: ps[name].val() for name in ('NS01_fairlead_bracket_extended', 'NS02_tower_keyed', 'NS03_inlet_lower', 'NS04_outlet_lower')}
    ref = n['reference_center_xyz_mm']
    for label, state in states.items():
        center = n['installed_centers_xyz_mm'][label]
        delta = tuple(center[i] - ref[i] for i in range(3))
        lift = n['upper_travel_mm'] if state == 'OPEN' else 0.0
        def at(xyz):
            return tuple(xyz[i] + delta[i] for i in range(3))
        def obj(name, shape, xyz=(0, 0, 0)):
            result[f'NIP_{name}_{label}'] = shape.translate(at(xyz))
        def screw(name, d, length, xyz, normal=(0, 0, 1)):
            result[f'NIP_{name}_{label}'] = base.place(base.bolt(d, length), at(xyz), (1, 0, 0), normal)
        def nut(name, d, xyz, normal=(0, 0, 1)):
            result[f'NIP_{name}_{label}'] = base.place(base.nut(d), at(xyz), (1, 0, 0), normal)
        obj('NS05_upper', ps['NS05_upper'].val(), (0, 0, lift))
        obj('NS06_lower_pad', ps['NS06_lower_pad'].val())
        obj('NS07_upper_pad', ps['NS07_upper_pad'].val(), (0, 0, lift))
        for i, (x, y) in enumerate(n['actuation_bolts_xy_mm']):
            obj(f'NS08_shoulder_{i}', ps['NS08_shoulder'].val(), (x, y, n['lower_body_top_z_mm']))
            shim_z = (n['upper_body_closed_bottom_z_mm'] if state == 'OPEN' else
                      n['upper_body_closed_bottom_z_mm'] + n['upper_body_thickness_mm'])
            shim = ps['NS09_open_shim'].val()
            if i == 0:
                shim = shim.rotate((0, 0, 0), (0, 0, 1), 180)
            obj(f'NS09_open_shim_{i}', shim, (x, y, shim_z))
            screw(f'HW_M2x16_actuator_{i}', 2, n['actuation_screw_length_mm'], (x, y, n['actuation_underhead_z_mm']))
            nut(f'HW_M2nut_actuator_{i}', 2, (x, y, n['lower_nut_bottom_z_mm']))
        x, y = n['lower_pad_fix_xy_mm']
        lower_pad_top = n['lower_body_top_z_mm'] + n['pad_thickness_mm']
        screw('HW_M2x12_lower_pad', 2, n['lower_pad_screw_length_mm'], (x, y, lower_pad_top))
        nut('HW_M2nut_lower_pad', 2, (x, y, n['lower_nut_bottom_z_mm']))
        x, y = n['upper_pad_fix_xy_mm']
        upper_pad_bottom = n['upper_body_closed_bottom_z_mm'] - n['pad_thickness_mm'] + lift
        screw('HW_M2x8_upper_pad', 2, n['upper_pad_screw_length_mm'], (x, y, upper_pad_bottom), (0, 0, -1))
        nut('HW_M2nut_upper_pad', 2, (x, y, n['upper_body_closed_bottom_z_mm'] + n['upper_body_thickness_mm'] + lift))
        mount_z = ref[2] + n['mount_z_relative_center_mm']
        screw('HW_M3x16_mount', 3, n['mount_bolt_length_mm'], (ref[0], n['mount_bolt_underhead_y_mm'], mount_z), (0, 1, 0))
        nut('HW_M3nut_mount', 3, (ref[0], n['mount_nut_front_y_mm'], mount_z), (0, 1, 0))
    return result


def install_nips(machine_scene, in_state='CLOSED', out_state='OPEN'):
    """Replace original nip/tower/bracket solids; never hide unchanged hardware."""
    remove = {'P01_tower', 'P10_fairlead_bracket', 'P13_nip_lower', 'P14_nip_upper',
              'P15_pad_lower', 'P15_pad_upper', 'HW_M3x16_nip', 'HW_M3nut_nip'}
    prefixes = ('HW_M2x16_nip_', 'HW_M2nut_nip_')
    result = {name: shape for name, shape in machine_scene.items()
              if name not in remove and not name.startswith(prefixes)}
    result.update(nips_installed(in_state, out_state))
    return result


def nip_inventory(items=None):
    items = nips_installed() if items is None else items
    known = S['nip_parts']
    rows = []
    for name, shape in items.items():
        key = name.removeprefix('NIP_')
        candidates = [k for k in known if key == k or key.startswith(k + '_')]
        if len(candidates) != 1:
            raise ValueError(f'Unmapped nip solid {name}: {candidates}')
        bb = shape.BoundingBox()
        rows.append({'instance_id': name, 'part_id': candidates[0],
                     'volume_mm3': shape.Volume(), 'valid': shape.isValid(),
                     'bbox_mm': [bb.xmin, bb.xmax, bb.ymin, bb.ymax, bb.zmin, bb.zmax]})
    return rows


def nip_gap_bounds(state):
    n = S['service_nips']
    a = n['finish_admission']
    nominal = n['shoulder_length_mm'] - 2 * n['pad_thickness_mm']
    error = a['shoulder_length_tolerance_mm'] + 2 * a['pad_thickness_tolerance_mm']
    if state == 'OPEN':
        nominal += n['open_shim_thickness_mm']
        error += a['shim_thickness_tolerance_mm']
    elif state != 'CLOSED':
        raise ValueError(state)
    return (nominal - error, nominal + error)


def nip_opening_transition(active, phase, fraction):
    """Native control trajectory; the other nip always remains CLOSED.

    Reverse the same trajectory to close. This proves only rigid control
    geometry; yarn compression/release requires the coupled contact model.
    """
    n = S['service_nips']
    if active not in ('IN', 'OUT') or phase not in n['opening_phases']:
        raise ValueError('Unknown nip or opening phase')
    if not 0 <= fraction <= 1:
        raise ValueError('Transition fraction must be within [0, 1]')
    k = n['opening_phases'].index(phase)
    loose = n['actuator_loosen_mm'] * (fraction if k == 0 else (1 - fraction if k == 5 else 1))
    withdraw = n['shim_withdrawal_mm'] * (fraction if k == 1 else (1 - fraction if k == 4 else (1 if 1 < k < 4 else 0)))
    lift = n['upper_travel_mm'] * (fraction if k == 2 else (1 if k > 2 else 0))
    shim_lower = -n['upper_body_thickness_mm'] * (fraction if k == 3 else (1 if k > 3 else 0))
    result = nips_installed('CLOSED', 'CLOSED')
    for part in ('NS05_upper', 'NS07_upper_pad', 'HW_M2x8_upper_pad', 'HW_M2nut_upper_pad'):
        name = f'NIP_{part}_{active}'
        result[name] = result[name].translate((0, 0, lift))
    for i in range(2):
        name = f'NIP_HW_M2x16_actuator_{i}_{active}'
        result[name] = result[name].translate((0, 0, loose))
        name = f'NIP_NS09_open_shim_{i}_{active}'
        result[name] = result[name].translate((withdraw * (-1 if i == 0 else 1), 0, shim_lower))
    return result


def nip_interface(label, state, radius_mm=None):
    """Physical pad faces/corridor for a coupled material model, not a grip BC."""
    n = S['service_nips']
    if label not in n['installed_centers_xyz_mm'] or state not in ('OPEN', 'CLOSED'):
        raise ValueError('Unknown nip or state')
    radius = n['open_uncompressed_yarn_radius_max_mm'] if radius_mm is None else radius_mm
    if radius < 0:
        raise ValueError('Yarn radius cannot be negative')
    center = n['installed_centers_xyz_mm'][label]
    lower = center[2] - n['closed_gap_mm'] / 2
    upper = center[2] + n['closed_gap_mm'] / 2 + (n['upper_travel_mm'] if state == 'OPEN' else 0)
    dx = center[0] - n['reference_center_xyz_mm'][0]
    interval = [lower + radius, upper - radius]
    return {
        'lower_pad_face_z_mm': lower,
        'upper_pad_face_z_mm': upper,
        'pad_face_bounds_xy_mm': [n['pad_bounds_xy_mm'][0] + dx,
                                  n['pad_bounds_xy_mm'][1] + dx,
                                  n['pad_bounds_xy_mm'][2], n['pad_bounds_xy_mm'][3]],
        'gap_midpoint_xyz_mm': [center[0], center[1], (lower + upper) / 2],
        'uncompressed_center_z_interval_mm': interval if interval[0] <= interval[1] else None,
        'compression_law_required': interval[0] > interval[1],
        'material_custody_qualified': False,
    }


def export_bundle(output):
    """Export reproducible native manufacturing artifacts, never images."""
    output = Path(output)
    target = output / 'parts'
    target.mkdir(parents=True, exist_ok=True)
    components = {**parts(), **nip_parts()}
    metadata = {**S['parts'], **S['nip_parts']}
    part_rows = []
    for name, part in components.items():
        cq.exporters.export(part, str(target / (name + '.step')))
        cq.exporters.export(part, str(target / (name + '.stl')), tolerance=.03, angularTolerance=.1)
        bb = part.val().BoundingBox()
        info = metadata[name]
        part_rows.append({'part_id': name, 'quantity': info['quantity'],
                          'material': info['material'], 'process': info['process'],
                          'volume_mm3': part.val().Volume(),
                          'bbox_mm': json.dumps([bb.xmin, bb.xmax, bb.ymin, bb.ymax, bb.zmin, bb.zmax]),
                          'step': 'parts/' + name + '.step',
                          'parameter_authority': 'spec/machine_service.json'})
    cradle_items = installed(C['center_stops_mm']['HIGH'])
    nip_items = nips_installed()
    counts = {}
    for catalog in (S['parts'], S['nip_parts']):
        for name, info in catalog.items():
            counts[name] = counts.get(name, 0) + info['quantity']
    bom_rows = [{'part_id': name, 'installed_quantity': count,
                 'material': metadata[name]['material'], 'process': metadata[name]['process'],
                 'source': metadata[name].get('source', 'spec/machine_service.json')}
                for name, count in sorted(counts.items())]
    for filename, rows in [('manufacturing_parts.csv', part_rows),
                           ('bom.csv', bom_rows),
                           ('installed_instances.csv', inventory(cradle_items) + nip_inventory(nip_items))]:
        with (output / filename).open('w', newline='') as stream:
            writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
    all_parts = {**cradle_items, **nip_items}
    assembly = cq.Assembly(name=S['revision'])
    for name, solid in all_parts.items():
        assembly.add(solid, name=name)
    assembly.save(str(output / 'service_subassemblies.step'))
    cq.exporters.export(indexed_base_board(base.base_board()), str(output / 'BASE_F03_service_drilled.step'))
    source_paths = [SPEC_PATH, Path(__file__), base.SPEC, Path(base.__file__), Path(base.peripherals.__file__)]
    manifest = {
        'revision': S['revision'],
        'exported_state': {'cup_center_mm': C['center_stops_mm']['HIGH'],
                           'tray_angle_deg': 0, 'IN': 'CLOSED', 'OUT': 'OPEN'},
        'source_hashes': {
            str(p.relative_to(base.ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in source_paths},
        'manufactured_variants': len(components), 'service_solids': len(all_parts),
        'cradle_inventory': {k: v['quantity'] for k, v in S['parts'].items()},
        'nip_inventory': {k: v['quantity'] for k, v in S['nip_parts'].items()},
        'interface_checks': interface_checks(),
        'nip_gap_bounds_mm': {state: nip_gap_bounds(state) for state in ('CLOSED', 'OPEN')},
        'nip_interfaces': {label: {state: nip_interface(label, state) for state in ('CLOSED', 'OPEN')}
                           for label in ('IN', 'OUT')},
        'not_a_full_machine_release': True,
    }
    (output / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    hashes = {str(p.relative_to(output)): hashlib.sha256(p.read_bytes()).hexdigest()
              for p in sorted(output.rglob('*')) if p.is_file() and p.name != 'SHA256SUMS.json'}
    (output / 'SHA256SUMS.json').write_text(json.dumps(hashes, indent=2) + '\n')
    return manifest


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(export_bundle(args.output), indent=2))

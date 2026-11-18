"""Affine first-capture actuation at fixed roll/support/transfer/feed modes.

This is a motion provider, not a swept-clearance or equilibrium certificate.
The mapping is derived from cad.r5m2.build.xyz_instances/integrated_instances
and cad.transfer.indexed.installed. A candidate needs a source-bound native
replay before the mapping may be used in a continuation guard.
"""
from copy import deepcopy
from collections.abc import Mapping
import json

import numpy as np

VARYING = ('head_tip_mm', 'guide_tip_mm', 'main_gate_mm')
GATE_PARTS = frozenset(('H02_gate', 'H07_gate_knob', 'H08_stop_sleeve',
    'HW_M2x20_gate', 'HW_M2nut_gate'))


def _three(value):
    a = np.asarray(value, float)
    if a.shape != (3,) or not np.isfinite(a).all():
        raise ValueError('Finite three-vector control required')
    return a.copy()


def _stage_mask(name):
    """World XYZ displacement masks, including the rotated guide-axis frame."""
    for axis, base_mask in [('X', [0, 0, 0]), ('Y', [1, 0, 0]), ('Z', [1, 1, 0])]:
        if name.startswith(axis+'_'):
            local = name[2:]; mask = np.array(base_mask, float)
            moving = local == 'A02_carriage' or local.startswith('HW_M3nut_carriage_')
            fixed = (local.startswith(('A01_', 'A03_', 'A04_', 'A05_', 'A06_',
                'HW_buttonM3x12_cap_', 'HW_M3nut_cap_', 'HW_M3x12_stop_', 'HW_M3nut_stop_'))
                or local in ('HW_M3x12_slide_lock', 'HW_M3nut_slide_lock'))
            if moving:
                mask['XYZ'.index(axis)] = 1.
            elif not fixed:
                raise ValueError('Unregistered moving-axis member: '+name)
            return mask
    for prefix, mask in [('HW_M3x20_base_', [0, 0, 0]), ('HW_M3nut_base_', [0, 0, 0]),
            ('HW_M3x12_XY_', [1, 0, 0]), ('HW_M3x12_bracket_', [1, 1, 0]),
            ('HW_M3x12_Zbase_', [1, 1, 0]), ('HW_M3nut_Zbase_', [1, 1, 0]),
            ('HW_M3x12_adapter_', [1, 1, 1])]:
        if name.startswith(prefix):
            return np.array(mask, float)
    if name in ('F01_z_bracket', 'F06_guide_z_bracket'):
        return np.array([1., 1., 0.])
    if name == 'F05_adapter':
        return np.ones(3)
    raise ValueError('Unregistered head/guide member: '+name)


class CaptureTranslationPath:
    def __init__(self, start, end):
        self.start, self.end = deepcopy(start), deepcopy(end)
        a, b = deepcopy(start), deepcopy(end)
        for key in VARYING:
            if key not in a or key not in b:
                raise ValueError('Missing explicit capture control: '+key)
            del a[key]; del b[key]
        if json.dumps(a, sort_keys=True) != json.dumps(b, sort_keys=True):
            raise ValueError('Only head/guide translation and main gate may vary on this path')
        self.head_start = _three(start['head_tip_mm']); self.guide_start = _three(start['guide_tip_mm'])
        with np.errstate(over='ignore', invalid='ignore'):
            self.head_delta = _three(end['head_tip_mm'])-self.head_start
            self.guide_delta = _three(end['guide_tip_mm'])-self.guide_start
        if not np.isfinite(np.r_[self.head_delta,self.guide_delta]).all():
            raise ValueError('Finite actuator endpoint differences required')
        self.gate_start, self.gate_end = float(start['main_gate_mm']), float(end['main_gate_mm'])
        if not np.isfinite([self.gate_start, self.gate_end]).all() or min(self.gate_start, self.gate_end) < 0:
            raise ValueError('Finite nonnegative gate control required')
        self.gate_delta = self.gate_end-self.gate_start
        if not np.isfinite([start['head_inclination_deg'], start['head_roll_deg']]).all():
            raise ValueError('Finite fixed inclination and roll required')
        inclination = np.deg2rad(start['head_inclination_deg'])
        axis = np.array([0.,np.cos(inclination),-np.sin(inclination)])
        self.gate_displacement = -axis*self.gate_delta

    def state_at(self, fraction):
        t = float(fraction)
        if not np.isfinite(t) or not 0 <= t <= 1:
            raise ValueError('Capture fraction must lie in[0,1]')
        state = deepcopy(self.start)
        state['head_tip_mm'] = (self.head_start+t*self.head_delta).tolist()
        state['guide_tip_mm'] = (self.guide_start+t*self.guide_delta).tolist()
        state['main_gate_mm'] = self.gate_start+t*self.gate_delta
        return state

    def native_translations(self, motion_kinds):
        """Full-interval prescribed translation; free clamp/feed is separate.

        Require an already exhaustive native inventory from the contact scene.
        Unknown axis components are rejected instead of treated as stationary.
        """
        if not motion_kinds or set(motion_kinds.values())-{'fixed', 'clamp', 'carrier', 'counter'}:
            raise ValueError('Exhaustive supported native motion ownership required')
        result = {}
        for name, kind in motion_kinds.items():
            if name.startswith('GUIDE_TOOL_'):
                delta = self.guide_delta
            elif name.startswith('TOOL_'):
                with np.errstate(over='ignore', invalid='ignore'):
                    delta = self.head_delta+(self.gate_displacement if name[5:] in GATE_PARTS else 0.)
            elif name.startswith('HEAD_'):
                delta = _stage_mask(name[5:])*self.head_delta
            elif name.startswith('GUIDE_'):
                delta = _stage_mask(name[6:])*self.guide_delta
            else:
                delta = np.zeros(3)
            if kind != 'fixed' and np.any(delta):
                raise ValueError('Prescribed and free-rigid ownership overlap: '+name)
            result[name] = _three(delta)
        return result

    def analytical_translations(self, components, coverage, native_translations):
        """Derive every component's motion from its actual covered native parts.

        Use the scene's geometry-bound coverage and the exhaustive map returned
        by ``native_translations``. A component cannot silently become fixed,
        and a union containing independently moving solids is not translated as
        one body. Free clamp/feeder motion remains a separate dynamic coordinate.
        """
        if (not isinstance(components,Mapping) or not components
                or not isinstance(coverage,Mapping) or not coverage
                or not isinstance(native_translations,Mapping) or not native_translations):
            raise ValueError('Explicit component, native coverage and motion mappings required')
        vectors={name:_three(value) for name,value in native_translations.items()}
        result={}
        for name,record in coverage.items():
            if not isinstance(record,Mapping) or not isinstance(record.get('contact_id'),str):
                raise ValueError('Every covered native part needs an explicit contact ID')
            contact_id=record['contact_id']
            if contact_id not in components or name not in vectors:
                raise ValueError('Analytical coverage and native motion inventory differ: '+str(name))
            if contact_id in result and not np.array_equal(result[contact_id],vectors[name]):
                raise ValueError('One analytical component covers differently moving native solids: '+contact_id)
            result[contact_id]=vectors[name].copy()
        if set(result)!=set(components):
            raise ValueError('Every analytical component must have actual native coverage')
        return result

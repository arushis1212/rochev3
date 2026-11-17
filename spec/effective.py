"""Load the fixture's source parameters and adopted finished-interface overlay.

CAD and physics use this same reader. Drawing clearances remain relational to
the functional hook/gate parameters; neither input file is modified by loading.
"""
import copy
import json
from pathlib import Path


def _merge(target, overlay):
    for key, value in overlay.items():
        if isinstance(value, dict) and isinstance(target.get(key), dict):
            _merge(target[key], value)
        else:
            target[key] = copy.deepcopy(value)


def load_fixture(root=None):
    root = Path(root) if root is not None else Path(__file__).resolve().parents[1]
    fixture = json.loads((root / 'spec/r5_m2_fixture.json').read_text())
    finished = json.loads((root / 'spec/d26_finished_interfaces.json').read_text())
    _merge(fixture, finished['base_overrides'])
    tool = fixture['tool']
    tool['barrel_slot_top'] = (tool['gate_bottom'] + tool['gate_thickness']
                               + finished['tool']['upper_passage_nominal_clearance_mm'])
    tool['barrel_slot_bottom'] = (tool['body_bottom']
                                  - finished['tool']['body_bottom_nominal_clearance_mm'])
    tool['gate_stop_slot_width'] = tool['stop_sleeve_od'] + tool['stop_slot_side_clearance']
    tool['gate_stop_slot_length'] = tool['gate_stroke'] + tool['stop_sleeve_od']
    fixture['frame']['head_x_origin'][0] = finished['reach']['head_x_origin_x_mm']
    fixture['finished_interfaces'] = finished
    return fixture

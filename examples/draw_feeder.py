"""Meter working yarn from the registered pulley path while preserving axial strain."""
import argparse
import json
from pathlib import Path

import numpy as np
from scipy.optimize import brentq


def replay(rest_to_issue_mm=None, path=None):
    with np.load(path or Path(__file__).with_suffix('.npz'), allow_pickle=False) as data:
        marks, points = data['s_mm'], data['q_mm']
        weights = np.interp(marks, marks[data['tangent_indices']], [0., 1., 1., 0.])
        strain_ratio = np.linalg.norm(np.diff(points, axis=0), axis=1) / np.diff(marks)
        initial = float(data['carrier_start_z_mm'])
        maximum = float(data['carrier_limit_z_mm'])
        target = float(data['command_mm'] if rest_to_issue_mm is None else rest_to_issue_mm)

        def payout(z):
            moved = points.copy()
            moved[:, 2] += weights * (z - initial)
            remaining = np.linalg.norm(np.diff(moved, axis=0), axis=1) / strain_ratio
            return float(np.sum(np.diff(marks) - remaining))

        capacity = payout(maximum)
        if not np.isfinite(target) or not 0 <= target <= capacity:
            raise ValueError('Requested length exceeds the modeled positive carrier stroke')
        z = initial if target == 0 else brentq(lambda height: payout(height) - target, initial, maximum)
        return dict(carrier_start_z_mm=initial, carrier_end_z_mm=z, stroke_mm=z-initial,
                    donated_rest_mm=payout(z), source_nodes=len(marks),
                    modeled_capacity_mm=capacity)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('payout_mm', type=float, nargs='?')
    print(json.dumps(replay(parser.parse_args().payout_mm), indent=2))

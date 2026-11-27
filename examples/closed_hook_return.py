"""Evaluate the camera-free bight-release command in machine coordinates."""
import argparse
import json
from itertools import accumulate
from math import dist, isfinite
from pathlib import Path

COMMAND = Path(__file__).with_suffix('.json')


def read_path():
    return json.loads(COMMAND.read_text())['waypoints_mm']


def stations(points):
    if len(points) < 2 or any(len(p) != 3 or not all(map(isfinite, p)) for p in points):
        raise ValueError('Expected at least two finite XYZ points')
    lengths = [dist(a, b) for a, b in zip(points, points[1:])]
    if min(lengths) <= 0:
        raise ValueError('Consecutive command points must be distinct')
    return [0.0, *accumulate(lengths)]


def tip_at(points, travel_mm):
    marks = stations(points)
    if not isfinite(travel_mm) or not 0 <= travel_mm <= marks[-1]:
        raise ValueError('Requested travel is outside the recorded path')
    for i, end in enumerate(marks[1:]):
        if travel_mm <= end:
            weight = (travel_mm - marks[i]) / (end - marks[i])
            return tuple(a + weight*(b-a) for a, b in zip(points[i], points[i+1]))


def hook_stop(data):
    return stations(data['waypoints_mm'])[3] + data['bight_release']['fourth_leg_hook_travel_mm']


def command_at(travel_mm=None, withdrawal_mm=0.0):
    """Return (hook XYZ, guide XYZ) for a selected hook travel and a subsequent guide withdrawal."""
    data = json.loads(COMMAND.read_text())
    release = data['bight_release']
    stop = hook_stop(data)
    travel = stop if travel_mm is None else travel_mm
    if not isfinite(travel) or not 0 <= travel <= stop:
        raise ValueError('Hook travel must lie between gate closure and the selected head stop')
    if not isfinite(withdrawal_mm) or not 0 <= withdrawal_mm <= release['modeled_guide_withdrawal_mm'][-1]:
        raise ValueError('Guide withdrawal is outside the modeled stroke')
    if withdrawal_mm and travel != stop:
        raise ValueError('Guide-only withdrawal begins at the held hook position')
    hook = tip_at(data['waypoints_mm'], travel)
    if travel == stop:
        guide = tuple(a + withdrawal_mm * u for a, u in zip(release['guide_tip_before_withdrawal_mm'],
                                                             release['guide_withdrawal_unit_vector']))
        return hook, guide
    marks = [*stations(data['waypoints_mm'])[:4], stop]
    guides = [*data['guide_tip_waypoints_mm'], release['guide_tip_before_withdrawal_mm']]
    for i, end in enumerate(marks[1:]):
        if travel <= end:
            weight = (travel - marks[i]) / (end - marks[i])
            return hook, tuple(a + weight * (b-a) for a, b in zip(guides[i], guides[i+1]))


def guide_at(travel_mm, withdrawal_mm=0.0):
    """Guide tip in world coordinates at the selected command."""
    return command_at(travel_mm, withdrawal_mm)[1]


def nominal_clearances():
    """Measure sleeve exposure and yarn separation from the recorded local segments."""
    import numpy as np
    from physics.full_stitch_aperture import _segment_triangle
    from physics.roche_contact3d import closest_segments

    release = json.loads(COMMAND.read_text())['bight_release']
    geometry = release['nominal_crossing_geometry']
    triangle = np.array(geometry['foundation_aperture_triangle_mm'])
    start, end = np.array(geometry['crossing_yarn_segment_mm'])
    crossing = _segment_triangle(start, end, triangle, 1e-9)
    if crossing['kind'] != 'hit' or crossing['sign'] != 1:
        raise ValueError('The recorded strand must cross the oriented aperture in the positive direction')
    fraction, point, _ = crossing['points'][0]
    s0, s1 = geometry['crossing_segment_material_mm']
    _, guide = command_at(withdrawal_mm=release['nominal_guide_withdrawal_mm'])
    diameter = release['nominal_yarn_diameter_mm']
    exposure = (guide - point) @ release['guide_withdrawal_unit_vector'] - diameter / 2
    work = np.array(geometry['nearest_working_segment_mm'])
    foundation = np.array(geometry['neighboring_foundation_segment_mm'])
    center_distance, *_ = closest_segments(work[:1], work[1:], foundation[:1], foundation[1:])
    return {'full_radius_sleeve_clearance_mm': float(exposure),
            'foundation_yarn_surface_gap_mm': float(center_distance[0] - diameter),
            'positive_crossing_material_mm': float(s0 + fraction * (s1 - s0))}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('travel_mm', type=float, nargs='?', help='Hook path length from closure in mm')
    parser.add_argument('--guide', action='store_true', help='Print guide coordinates')
    parser.add_argument('--withdraw', type=float, metavar='MM', help='Guide withdrawal at the held hook')
    parser.add_argument('--reference', action='store_true', help='Print the four complete reference hook translations')
    parser.add_argument('--measure', action='store_true', help='Measure the nominal clearances using the recorded segments')
    args = parser.parse_args()
    data = json.loads(COMMAND.read_text())
    path = data['waypoints_mm']
    try:
        if args.measure:
            if args.travel_mm is not None or args.guide or args.reference or args.withdraw is not None:
                parser.error('--measure uses the recorded nominal stop')
            print(json.dumps(nominal_clearances(), indent=2))
        elif args.reference:
            if args.guide or args.withdraw is not None:
                parser.error('--reference describes the hook datums alone')
            for travel in stations(path) if args.travel_mm is None else [args.travel_mm]:
                x, y, z = tip_at(path, travel)
                print(f'{travel:9.5f} mm   X {x:10.5f}   Y {y:10.5f}   Z {z:10.5f}')
        else:
            stop = hook_stop(data)
            if args.travel_mm is None and args.withdraw is None:
                rows = [(s, 0.) for s in [*stations(path)[:4], stop]]
                rows.append((stop, data['bight_release']['nominal_guide_withdrawal_mm']))
            else:
                rows = [(stop if args.travel_mm is None else args.travel_mm, args.withdraw or 0.)]
            print('Hook travel (mm)  Guide withdrawal (mm)       X (mm)      Y (mm)      Z (mm)')
            for travel, withdrawal in rows:
                hook, guide = command_at(travel, withdrawal)
                x, y, z = guide if args.guide else hook
                print(f'{travel:16.5f}  {withdrawal:21.5f}  {x:11.5f} {y:11.5f} {z:11.5f}')
    except ValueError as exc:
        parser.error(str(exc))

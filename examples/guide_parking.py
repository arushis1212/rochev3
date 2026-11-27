"""Replay the gate-closed hook and guide movements from first draw to guide park."""
import argparse
import json
from math import dist, sqrt
from pathlib import Path

from examples.closed_hook_return import command_at as first_draw_command, tip_at


DATA = Path(__file__).with_suffix('.json')
PHASES = ('guide-start', 'hook-backoff', 'guide-finish', 'guide-center')


def waypoints():
    data = json.loads(DATA.read_text())
    h0, g0 = first_draw_command(withdrawal_mm=0.48)
    h1 = tuple(data['backed_off_hook_mm'])
    g1 = tuple(data['guide_at_hook_backoff_mm'])
    g2 = tuple(data['guide_at_axial_stop_mm'])
    g3 = tuple(data['guide_park_mm'])
    return [(h0, g0), (h0, g1), (h1, g1), (h1, g2), (h1, g3)]


def phase_segment(phase):
    idx = PHASES.index(phase)
    start, end = waypoints()[idx:idx+2]
    moving = 0 if phase == 'hook-backoff' else 1
    return start, end, moving


def command_at(phase, travel_mm):
    """World hook and guide coordinates at this phase's local distance."""
    start, end, moving = phase_segment(phase)
    positions = list(start)
    positions[moving] = tip_at([start[moving], end[moving]], travel_mm)
    return tuple(positions)


def parked_rim_gap():
    """Surface gap between the recorded closest rim and working segments at park."""
    data = json.loads(DATA.read_text())['parked_yarn']
    a, b = data['foundation_rim_segment_xyz_mm']
    c, d = data['working_segment_xyz_mm']
    u = [x - y for x, y in zip(b, a)]
    v = [x - y for x, y in zip(d, c)]
    w = [x - y for x, y in zip(a, c)]

    def dot(x, y):
        return sum(i * j for i, j in zip(x, y))

    uu, uv, vv, uw, vw = dot(u, u), dot(u, v), dot(v, v), dot(u, w), dot(v, w)
    denominator = uu * vv - uv * uv
    if denominator <= 0:
        raise ValueError('The measured segment directions must be independent')
    t = (uv * vw - vv * uw) / denominator
    r = (uu * vw - uv * uw) / denominator
    if not (0 < t < 1 and 0 < r < 1):
        raise ValueError('The closest points in this measurement must lie on both finite segments')
    distance = sqrt(sum((x + t*y - r*z)**2 for x, y, z in zip(w, u, v)))
    return distance - data['diameter_mm']


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument('phase', nargs='?', choices=PHASES)
    cli.add_argument('travel_mm', nargs='?', type=float)
    cli.add_argument('--measure', action='store_true', help='Measure the parked yarn surface gap')
    args = cli.parse_args()
    if args.measure:
        if args.phase is not None:
            cli.error('--measure uses the parked geometry')
        print(f'Parked working-yarn to foundation-rim gap: {parked_rim_gap():.6f} mm')
        return
    if (args.phase is None) != (args.travel_mm is None):
        cli.error('Supply both a phase and its local travel in mm')
    print('Phase          Local travel (mm)    Hook XYZ (mm)                    Guide XYZ (mm)')
    for phase in ([args.phase] if args.phase else PHASES):
        start, end, moving = phase_segment(phase)
        distance = dist(start[moving], end[moving]) if args.phase is None else args.travel_mm
        try:
            hook, guide = command_at(phase, distance)
        except ValueError as exc:
            cli.error(str(exc))
        hook_xyz = ' '.join(f'{v:9.4f}' for v in hook)
        guide_xyz = ' '.join(f'{v:9.4f}' for v in guide)
        print(f'{phase:<15}{distance:12.6f}      {hook_xyz}    {guide_xyz}')


if __name__ == '__main__':
    main()

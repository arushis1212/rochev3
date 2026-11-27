"""Interpolate the nominal hook-tip command by distance along its return path."""
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


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('travel_mm', type=float, nargs='?', help='Distance from gate closure')
    args = parser.parse_args()
    path = read_path()
    for mark in stations(path) if args.travel_mm is None else [args.travel_mm]:
        x, y, z = tip_at(path, mark)
        print(f'{mark:9.5f} mm   X {x:10.5f}   Y {y:10.5f}   Z {z:10.5f}')

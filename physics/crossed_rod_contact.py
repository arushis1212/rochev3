"""Perpendicular-rod contact energy: exact integral and bounded cell quadrature.
Units: mm, N, N/mm^2. Positive centerline separation; straight long rods.
"""
import math


def continuum(diameter, separation, penalty):
    if not all(math.isfinite(v) and v > 0 for v in (diameter, separation, penalty)):
        raise ValueError('Finite positive diameter, separation and penalty required')
    if separation >= diameter:
        return 0.0, 0.0
    a = diameter - separation
    energy = math.pi * penalty * (a**3 / 3.0 - a**4 / (4.0 * diameter))
    force = math.pi * penalty * separation * a**2 / diameter
    return energy, force


def pair_minimum(mesh, diameter, separation, penalty, maximum_candidate_pairs=100000):
    continuum(diameter, separation, penalty)
    if not math.isfinite(mesh) or mesh <= 0:
        raise ValueError('Finite positive segment spacing required')
    if type(maximum_candidate_pairs) is not int or maximum_candidate_pairs <= 0:
        raise ValueError('Positive integer pair budget required')
    if separation >= diameter:
        return 0.0, 0.0, 0
    # Full rods extend well past contact. A conservative exact distance cull
    # leaves only intervals that intersect the active disk in parameter space.
    active_radius = math.sqrt(diameter**2 - separation**2)
    ratio = active_radius / mesh
    if not math.isfinite(ratio) or ratio > math.sqrt(maximum_candidate_pairs) / 2:
        raise ValueError('Diagnostic grid exceeds the declared pair budget')
    n = math.ceil(ratio)
    if 4*n*n > maximum_candidate_pairs:
        raise ValueError('Diagnostic grid exceeds the declared pair budget')
    intervals = [(i * mesh, (i + 1) * mesh) for i in range(-n, n)]
    energy = force = 0.0
    active = 0
    for lo, hi in intervals:
        x = max(lo, -hi, 0.0)
        for bottom, top in intervals:
            y = max(bottom, -top, 0.0)
            distance = math.sqrt(x*x + y*y + separation*separation)
            depth = max(diameter - distance, 0.0)
            if depth == 0.0:
                continue
            weight = mesh * mesh / diameter
            energy += 0.5 * penalty * weight * depth**2
            force += penalty * weight * depth * separation / distance
            active += 1
    return energy, force, active

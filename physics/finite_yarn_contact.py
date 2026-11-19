"""Distributed contact between two straight finite yarn segments in 3D."""
from functools import lru_cache
import math

import numpy as np


@lru_cache(maxsize=8)
def _rule(order):
    return np.polynomial.legendre.leggauss(order)


def _sphere_events(offset, velocity, diameter):
    """Roots of ||offset + t velocity|| = diameter, using closest approach."""
    speed2 = velocity @ velocity
    if speed2 == 0:
        return []
    closest = -(offset @ velocity) / speed2
    distance = np.linalg.norm(offset + closest * velocity)
    if distance >= diameter:
        return []
    half = math.sqrt((diameter - distance) * (diameter + distance) / speed2)
    return [closest - half, closest + half]


def integrate(endpoints, rest_lengths, diameter, stiffness, order=24):
    """Return energy in N mm and four physical endpoint forces in N.

    Points and natural lengths use mm. Stiffness uses N/mm². Natural lengths
    stay fixed when differentiating energy with respect to the four endpoints.
    The centerline separation must be positive throughout active contact.
    """
    points = np.asarray(endpoints, dtype=float)
    natural = np.asarray(rest_lengths, dtype=float)
    if (points.shape != (4, 3) or natural.shape != (2,) or not np.isfinite(points).all()
            or not np.isfinite(natural).all() or min(natural) <= 0
            or not all(math.isfinite(x) and x > 0 for x in (diameter, stiffness))):
        raise ValueError("Four finite 3D endpoints and positive lengths, diameter and stiffness required")
    if type(order) is not int or not 4 <= order <= 96:
        raise ValueError("Gaussian quadrature order must be an integer between 4 and 96")
    a, b, c, d = points
    u, v, offset = b - a, d - c, a - c
    length_u, length_v = np.linalg.norm(u), np.linalg.norm(v)
    if min(length_u, length_v) <= 0:
        raise ValueError("Both finite segments need positive length")
    direction = v / length_v
    axial0, axial_speed = offset @ direction, u @ direction
    radial0, radial_speed = offset - axial0 * direction, u - axial_speed * direction
    # A slice changes formula when its disk appears or a finite endpoint
    # enters or leaves that disk. These events protect narrow contact patches.
    events = [0., 1.]
    for start, motion in ((radial0, radial_speed), (offset, u), (a - d, u)):
        events.extend(t for t in _sphere_events(start, motion, diameter) if 0 < t < 1)
    # Rule out a crossing at the same spatial point, including parallel overlap.
    candidates = [0., 1.]
    radial2 = radial_speed @ radial_speed
    if radial2 > 0:
        candidates.append(float(np.clip(-(radial_speed @ radial0) / radial2, 0, 1)))
    for endpoint in (c, d):
        candidates.append(float(np.clip((endpoint-a) @ u / (length_u**2), 0, 1)))
    for t in candidates:
        relative = offset + t * u
        near = relative - np.clip(relative @ direction, 0, length_v) * direction
        if np.linalg.norm(near) <= 32 * np.finfo(float).eps * max(length_u, length_v, diameter):
            raise ValueError("Coincident centerlines fall outside the positive-separation model")
    cuts = sorted(set(events))
    gauss, weights = _rule(order)
    # This reparameterization gives zero slope at the end of each outer slice,
    # where a circular contact patch can open with square-root dependence.
    angular = (math.pi / 2) * gauss
    outer_x, outer_weight = np.sin(angular), (math.pi / 2) * np.cos(angular) * weights
    energy = 0.
    forces = np.zeros((4, 3))
    scale = stiffness * natural[0] * natural[1] / diameter
    for left, right in zip(cuts[:-1], cuts[1:]):
        half = (right - left) / 2
        outer = (right + left) / 2 + half * outer_x
        delta = offset + outer[:, None] * u
        axial = delta @ direction
        radial = np.linalg.norm(delta - axial[:, None] * direction, axis=1)
        extent = np.sqrt(np.maximum(0., (diameter - radial) * (diameter + radial)))
        lo = np.maximum(0., (axial - extent) / length_v)
        hi = np.minimum(1., (axial + extent) / length_v)
        width = np.maximum(hi - lo, 0.)
        if not np.any(width):
            continue
        inner = lo[:, None] + width[:, None] * ((1 + gauss) / 2)
        difference = delta[:, None, :] - inner[:, :, None] * v
        distance = np.linalg.norm(difference, axis=2)
        depth = np.maximum(0., diameter - distance)
        quadrature = scale * half * (outer_weight * width / 2)[:, None] * weights
        energy += .5 * np.sum(quadrature * depth**2)
        magnitude = np.divide(quadrature * depth, distance, out=np.zeros_like(depth), where=distance > 0)
        pair_force = magnitude[:, :, None] * difference
        for i, shape in enumerate((1 - outer[:, None], outer[:, None], inner - 1, -inner)):
            forces[i] += np.sum(pair_force * shape[:, :, None], axis=(0, 1))
    return float(energy), forces

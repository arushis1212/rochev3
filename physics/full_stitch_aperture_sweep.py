"""Conservative geometry certificate for an affine material-aperture sweep.

See docs/APERTURE_GEOMETRY.md. This proves neither force equilibrium,
physical custody, passage-event history nor actual nonaffine motion. Arithmetic
is floating point with explicit reserves, not a formal interval-arithmetic proof.
"""
import hashlib
import json
import numpy as np

from physics.full_stitch_aperture import MaterialAperture, _interval, _material
from physics.roche_contact3d import closest_segments


def _quadratic_bounds(c0, c1, c2, half, arithmetic_error=0.):
    """Exact quadratic extrema in real arithmetic, expanded for roundoff."""
    c0, c1, c2 = np.broadcast_arrays(c0, c1, c2)
    values = np.stack((c0-c1*half+c2*half**2, c0+c1*half+c2*half**2))
    low, high = values.min(axis=0), values.max(axis=0)
    stationary = np.divide(-c1, 2*c2, out=np.zeros_like(c0), where=c2 != 0)
    inside = (c2 != 0) & (np.abs(stationary) <= half)
    value = c0+c1*stationary+c2*stationary**2
    low, high = np.where(inside, np.minimum(low, value), low), np.where(inside, np.maximum(high, value), high)
    reserve = 256*np.finfo(float).eps*np.maximum(1., np.abs(c0)+np.abs(c1)*half+np.abs(c2)*half**2)
    return low-reserve-arithmetic_error, high+reserve+arithmetic_error


def _turn_bounds(u, v, du, dv, normal, half, vector_error=0.):
    # Bound the products before cancellation, not merely the final coefficients.
    # A long, nearly collinear triangle can lose its entire area to cancellation.
    au, av = np.abs(u)+half*np.abs(du), np.abs(v)+half*np.abs(dv)
    gross = sum(abs(normal[k])*(au[..., i]*av[..., j]+au[..., j]*av[..., i])
                for k, i, j in ((0, 1, 2), (1, 2, 0), (2, 0, 1)))
    error = 256*np.finfo(float).eps*gross
    error += vector_error*(np.linalg.norm(au, axis=-1)+np.linalg.norm(av, axis=-1))+vector_error**2
    return _quadratic_bounds(np.cross(u, v)@normal,
        (np.cross(du, v)+np.cross(u, dv))@normal, np.cross(du, dv)@normal, half, error)


def _dot_bounds(u, v, du, dv, half, vector_error=0.):
    au, av = np.abs(u)+half*np.abs(du), np.abs(v)+half*np.abs(dv)
    error = 256*np.finfo(float).eps*np.sum(au*av, axis=-1)
    error += vector_error*(np.linalg.norm(au, axis=-1)+np.linalg.norm(av, axis=-1))+vector_error**2
    return _quadratic_bounds(np.sum(u*v, axis=-1),
        np.sum(du*v+u*dv, axis=-1), np.sum(du*dv, axis=-1), half, error)


def _pair_lower(a, b, c, d, va, vb, vc, vd, half, reserve):
    """Finite segment separation minus a common-translation-invariant bound."""
    if not len(a):
        return float('inf')
    reserve = max(reserve, 256*np.finfo(float).eps*max(1., *(float(np.abs(x).max()) for x in (a, b, c, d))))
    # A clipped material interval can contain a point/very short segment from
    # cumulative-S roundoff. Replacing that segment by its endpoint changes its
    # set by at most its length. Subtract that finite bound, never omit the pair.
    la, lc = np.linalg.norm(b-a, axis=1), np.linalg.norm(d-c, axis=1)
    short_a, short_c = la <= reserve, lc <= reserve
    ordinary = ~short_a & ~short_c
    distance = np.empty(len(a))
    distance[ordinary] = closest_segments(a[ordinary], b[ordinary], c[ordinary], d[ordinary])[0]
    def point_segment(point, start, end):
        edge = end-start
        length2 = np.sum(edge*edge, axis=1)
        fraction = np.divide(np.sum((point-start)*edge, axis=1), length2,
                             out=np.zeros(len(point)), where=length2 > 0)
        return np.linalg.norm(point-start-np.clip(fraction, 0, 1)[:, None]*edge, axis=1)
    both = short_a & short_c
    distance[both] = np.linalg.norm(a[both]-c[both], axis=1)-la[both]-lc[both]
    only_a, only_c = short_a & ~short_c, short_c & ~short_a
    distance[only_a] = point_segment(a[only_a], c[only_a], d[only_a])-la[only_a]
    distance[only_c] = point_segment(c[only_c], a[only_c], b[only_c])-lc[only_c]
    speed = np.max(np.stack([np.linalg.norm(x-y, axis=1)
        for x in (va, vb) for y in (vc, vd)]), axis=0)
    result = distance-speed*half-reserve
    if not np.isfinite(result).all():
        return float('-inf')
    return float(result.min())


def _finite_or_none(value):
    return float(value) if np.isfinite(value) else None


def _fingerprint(aperture, q0, q1, s, passing, thresholds):
    h = hashlib.sha256()
    for a in (q0, q1, s):
        h.update(np.asarray(a, dtype='<f8').tobytes())
    h.update(json.dumps({'aperture': aperture.as_dict(), 'passing': list(map(float, passing)),
                         'thresholds': thresholds}, sort_keys=True).encode())
    return h.hexdigest()


def certify_affine_aperture(aperture, q0, q1, material_s, passing_s_interval, *,
        physical_margin_mm, closure_margin_mm, max_depth=10,
        distance_reserve_mm=1e-9, area_reserve_mm2=1e-9, deadline_check=lambda: None):
    """Bound every time in [0,1]; unresolved leaves reject the whole sweep.

    Inspected aperture/working material MUST follow q(t)=(1-t)q0+t*q1. A caller
    using a different motion law there cannot use this result. Uninspected
    material is outside this certificate. All passing/physical boundary pairs are
    checked; overlapping material intervals are rejected rather than exempted.
    """
    if not isinstance(aperture, MaterialAperture):
        raise ValueError('A material-bound disk is required')
    q0, s = _material(q0, material_s)
    q1, s1 = _material(q1, material_s)
    if q0.shape != q1.shape:
        raise ValueError('Affine endpoints require identical material topology')
    # Copy inputs so a callback cannot quietly change the certified trajectory.
    q0, q1, s = q0.copy(), q1.copy(), s.copy()
    thresholds = dict(physical_margin_mm=float(physical_margin_mm),
        closure_margin_mm=float(closure_margin_mm), distance_reserve_mm=float(distance_reserve_mm),
        area_reserve_mm2=float(area_reserve_mm2), max_depth=max_depth)
    if (not np.isfinite(list(thresholds.values())).all() or min(physical_margin_mm, closure_margin_mm) < 0
            or min(distance_reserve_mm, area_reserve_mm2) <= 0
            or type(max_depth) is not int or not 0 <= max_depth <= 20):
        raise ValueError('Finite nonnegative margins, positive reserves and bounded integer depth required')
    # Reconstruct to validate mutable dataclass attributes and own the topology.
    aperture = MaterialAperture(aperture.boundary_s, aperture.triangles, aperture.orientation_normal,
        aperture.position_tolerance, aperture.minimum_double_area, aperture.boundary_tolerance,
        aperture.material_s_domain)
    v0, v1 = aperture.vertices(q0, s), aperture.vertices(q1, s)
    p0, ps = _interval(q0, s, passing_s_interval)
    p1, _ = _interval(q1, s, passing_s_interval)
    ba, bb = min(aperture.boundary_s), max(aperture.boundary_s)
    if not (ps[-1] < ba or ps[0] > bb):
        raise ValueError('Passing and aperture boundary material intervals must be disjoint')
    dv, dp = v1-v0, p1-p0
    if not np.isfinite(dv).all() or not np.isfinite(dp).all():
        raise ValueError('Finite affine differences required')
    n, npass = len(v0), len(p0)-1
    i, j = np.triu_indices(n, 1)
    keep = (j != i+1) & ~((i == 0) & (j == n-1))
    i, j = i[keep], j[keep]
    wi, bi = np.repeat(np.arange(npass), n-1), np.tile(np.arange(n-1), npass)
    tri = aperture.triangles
    binding = _fingerprint(aperture, q0, q1, s, passing_s_interval, thresholds)
    leaves, evaluations = [], 0
    required_area = max(area_reserve_mm2, aperture.minimum_double_area)
    # Coordinate formation, subtraction and projection errors enter before the
    # cross/dot product. A large-coordinate/aspect-ratio input is inconclusive
    # when this conservative numerical reserve consumes its area margin.
    vector_error = 2048*np.finfo(float).eps*max(1., float(np.abs(v0).max()), float(np.abs(v1).max()))

    def assess(lo, hi, normal_hint=None):
        nonlocal evaluations
        deadline_check()
        evaluations += 1
        mid, half = (lo+hi)/2, (hi-lo)/2
        v, p = v0+mid*dv, p0+mid*dp
        face, vel = v[tri], dv[tri]
        u, w = face[:, 1]-face[:, 0], face[:, 2]-face[:, 0]
        du, dw = vel[:, 1]-vel[:, 0], vel[:, 2]-vel[:, 0]
        normal = np.cross(u, w).sum(axis=0) if normal_hint is None else np.asarray(normal_hint, float).copy()
        if not np.isfinite(normal).all() or np.linalg.norm(normal) <= required_area:
            return {'valid': False, 'reason': 'no_nondegenerate_projection'}
        normal /= np.linalg.norm(normal)
        areas, _ = _turn_bounds(u, w, du, dw, normal, half, vector_error)
        if not np.isfinite(areas).all() or np.any(areas <= required_area):
            return {'valid': False, 'reason': 'projected_triangle_orientation',
                    'area_lower_mm2': _finite_or_none(areas.min())}
        # Only differences enter the projection; discard a common origin.
        project = lambda a: a-(a@normal)[..., None]*normal
        vproj, dproj = project(v-v[0]), project(dv-dv[0])
        edge, de = np.roll(vproj, -1, axis=0)-vproj, np.roll(dproj, -1, axis=0)-dproj
        if np.any(np.linalg.norm(edge, axis=1)-np.linalg.norm(de, axis=1)*half <= distance_reserve_mm):
            return {'valid': False, 'reason': 'projected_boundary_edge_collapse'}
        a, b = np.roll(vproj, 1, axis=0)-vproj, edge
        da, db = np.roll(dproj, 1, axis=0)-dproj, de
        turnlo, turnhi = _turn_bounds(a, b, da, db, normal, half, vector_error)
        _, dothi = _dot_bounds(a, b, da, db, half, vector_error)
        adjacent = (turnlo > area_reserve_mm2) | (turnhi < -area_reserve_mm2) | (dothi < -area_reserve_mm2)
        if not adjacent.all():
            return {'valid': False, 'reason': 'adjacent_projected_boundary_overlap_unresolved'}
        boundary = _pair_lower(vproj[i], vproj[(i+1)%n], vproj[j], vproj[(j+1)%n],
            dproj[i], dproj[(i+1)%n], dproj[j], dproj[(j+1)%n], half, distance_reserve_mm)
        if boundary <= distance_reserve_mm:
            return {'valid': False, 'reason': 'projected_boundary_separation', 'lower_mm': _finite_or_none(boundary)}
        physical = _pair_lower(p[wi], p[wi+1], v[bi], v[bi+1],
            dp[wi], dp[wi+1], dv[bi], dv[bi+1], half, distance_reserve_mm)
        if physical < physical_margin_mm:
            return {'valid': False, 'reason': 'physical_boundary_separation', 'lower_mm': _finite_or_none(physical)}
        repeat = lambda x: np.broadcast_to(x, (npass, 3))
        closure = _pair_lower(p[:-1], p[1:], repeat(v[-1]), repeat(v[0]),
            dp[:-1], dp[1:], repeat(dv[-1]), repeat(dv[0]), half, distance_reserve_mm)
        if closure < closure_margin_mm:
            return {'valid': False, 'reason': 'virtual_neck_separation', 'lower_mm': _finite_or_none(closure)}
        return dict(valid=True, projection_normal=normal.tolist(), area_lower_mm2=float(areas.min()),
            projected_boundary_lower_mm=None if not len(i) else boundary,
            physical_boundary_lower_mm=physical, virtual_neck_lower_mm=closure)

    unresolved = None
    pending = [(0., 1., 0)]
    while pending:
        lo, hi, depth = pending.pop()
        result = assess(lo, hi)
        if not result['valid'] and result['reason'] in (
                'no_nondegenerate_projection', 'projected_triangle_orientation',
                'projected_boundary_edge_collapse', 'adjacent_projected_boundary_overlap_unresolved',
                'projected_boundary_separation'):
            # Each alternative is only a suggested fixed projection. It must
            # independently pass the SAME interval area/boundary/neck checks.
            # Changing projection changes no vertex, triangle or material path.
            normals = [*np.eye(3), *(-np.eye(3)),
                *[np.array([i, j, k], float) for i in (-1, 1) for j in (-1, 1) for k in (-1, 1)]]
            for normal in normals:
                result = assess(lo, hi, normal)
                if result['valid'] or result['reason'] in ('physical_boundary_separation', 'virtual_neck_separation'):
                    break
        if result['valid']:
            leaves.append(dict(time_interval=[lo, hi], depth=depth, **result))
        elif depth < max_depth:
            mid = (lo+hi)/2
            pending.extend([(mid, hi, depth+1), (lo, mid, depth+1)])
        else:
            unresolved = dict(time_interval=[lo, hi], depth=depth, **result)
            break
    return dict(certified=unresolved is None, input_sha256=binding, interpolation='affine_inspected_material_positions',
        projection_search='area_sum_then_six_signed_axes_then_eight_signed_cube_diagonals',
        thresholds=thresholds, evaluations=evaluations, accepted_leaves=leaves, unresolved=unresolved,
        physical_custody_certified=False, passage_event_history_certified=False,
        scope='Continuous projected disk embedding and distinct working-material separation from its physical boundary and virtual neck; no mechanics or crossing-event admission.')

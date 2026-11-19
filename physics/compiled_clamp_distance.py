"""Distance-only acceleration of the existing body-frame clamp contact union.

The physical energy still uses ClampContact. This numerical event oracle copies
its exact boxes, cylinders and material-edge pad reductions; it adds no geometry.
No fastmath, parallel reductions, smoothing or approximate distances are used.
"""
import numpy as np
from numba import njit


@njit(cache=True, fastmath=False)
def _box_distance(x, y, z, box):
    dx = abs(x-(box[0, 0]+box[1, 0])/2)-(box[1, 0]-box[0, 0])/2
    dy = abs(y-(box[0, 1]+box[1, 1])/2)-(box[1, 1]-box[0, 1])/2
    dz = abs(z-(box[0, 2]+box[1, 2])/2)-(box[1, 2]-box[0, 2])/2
    return np.sqrt(max(dx, 0.)**2+max(dy, 0.)**2+max(dz, 0.)**2)+min(max(dx, dy, dz), 0.)


@njit(cache=True, fastmath=False)
def _distances(points, groups, rigid, pads, offsets, cylinders):
    out = np.empty(len(points))
    for i in range(len(points)):
        x, y, z = points[i]
        best = np.inf
        for box in rigid:
            best = min(best, _box_distance(x, y, z, box))
        group = groups[i]
        for j in range(offsets[group], offsets[group+1]):
            best = min(best, _box_distance(x, y, z, pads[j]))
        for cylinder in cylinders:
            ox, oy, oz, length, inner, outer = cylinder
            rho = np.sqrt((x-ox)**2+(z-oz)**2)
            dr = max(rho-outer, inner-rho)
            da = abs(y-oy)-length/2
            distance = np.sqrt(max(dr, 0.)**2+max(da, 0.)**2)+min(max(dr, da), 0.)
            best = min(best, distance)
        out[i] = best
    return out


class CompiledClampDistance:
    def __init__(self, body):
        if not np.array_equal(body.center, np.zeros(3)) or not np.array_equal(body.R, np.eye(3)):
            raise ValueError('Compiled clamp oracle requires an unposed body-frame clamp')
        self.rigid = np.array(body.rigid.boxes, dtype=float, copy=True)
        pieces = list(body.pads.boxes)
        offsets = [0, len(pieces)]
        self.edge_groups = {}
        for group, edge in enumerate(sorted(body.reduced_pads), 1):
            self.edge_groups[edge] = group
            pieces.extend(body.reduced_pads[edge].boxes)
            offsets.append(len(pieces))
        self.pads = np.array(pieces, dtype=float, copy=True)
        self.offsets = np.array(offsets, dtype=np.int64)
        cylinders = [list(origin)+[length, inner, outer]
                     for origin, length, inner, outer in body.spacers]
        pin = body.spec.get('return_pin')
        if pin:
            cylinders.append(list(pin['center_body_mm'])+[pin['length_mm'], -2e9, pin['diameter_mm']/2])
        self.cylinders = np.array(cylinders, dtype=float).reshape(-1, 6)

    def groups_for_edges(self, edges):
        edges = np.asarray(edges)
        groups = np.zeros(len(edges), dtype=np.int64)
        for edge, group in self.edge_groups.items():
            groups[edges == edge] = group
        return groups

    def distances(self, points, groups):
        points = np.asarray(points, dtype=float)
        groups = np.asarray(groups)
        if (points.ndim != 2 or points.shape[1] != 3 or not np.isfinite(points).all()
                or groups.shape != (len(points),) or groups.dtype.kind not in 'iu'
                or np.any(groups < 0) or np.any(groups >= len(self.offsets)-1)):
            raise ValueError('Invalid clamp distance points or material groups')
        return _distances(points, groups, self.rigid,
                          self.pads, self.offsets, self.cylinders)

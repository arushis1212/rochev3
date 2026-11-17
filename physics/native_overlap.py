"""Reusable exact native-solid overlap test, for parametric CAD assemblies."""
import itertools
import math


def overlap_pairs(items, volume_tolerance_mm3=1e-7):
    """Positive-volume intersections after conservative AABB rejection.

    Touching mating faces have zero common volume. This is a static nominal
    geometry query; it does not establish swept clearance or tolerance margins.
    """
    if not math.isfinite(volume_tolerance_mm3) or volume_tolerance_mm3 < 0:
        raise ValueError('Intersection reporting tolerance must be nonnegative')
    boxes = {name: shape.BoundingBox() for name, shape in items.items()}
    hits = []
    for (a, shape_a), (b, shape_b) in itertools.combinations(items.items(), 2):
        aa, bb = boxes[a], boxes[b]
        if any(min(getattr(aa, axis + 'max'), getattr(bb, axis + 'max'))
               <= max(getattr(aa, axis + 'min'), getattr(bb, axis + 'min'))
               for axis in 'xyz'):
            continue
        volume = shape_a.intersect(shape_b).Volume()
        if volume > volume_tolerance_mm3:
            hits.append({'a': a, 'b': b, 'intersection_mm3': volume})
    return hits

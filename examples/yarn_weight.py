"""Compare the gravitational loads of two yarns held in the same geometry."""
import json
import math


def comparison(rest_mm, density_a_tex, density_b_tex, free_nodes):
    """Return the greatest necessary imbalance over the indicated free vertical DOFs.

    1 tex is 1 gram per kilometre. Half of each reference segment's mass
    loads each endpoint under the linear two-node discretization.
    """
    lengths = tuple(rest_mm)
    nodes = tuple(free_nodes)
    if not lengths or any(not math.isfinite(x) or x <= 0 for x in lengths):
        raise ValueError("Each segment needs a finite positive rest length")
    if any(not math.isfinite(x) or x < 0 for x in (density_a_tex, density_b_tex)):
        raise ValueError("Linear density must be finite and nonnegative")
    if not nodes or any(type(i) is not int or not 0 <= i <= len(lengths) for i in nodes):
        raise ValueError("Supply at least one free node, numbered from zero")
    left = (0.0, *lengths)
    right = (*lengths, 0.0)
    dual_mm = [(a + b) / 2 for a, b in zip(left, right)]
    # At a common pose with all other forces equal, their difference is the
    # weight difference. The triangle inequality gives half of it as a bound.
    difference_n = [abs(density_b_tex - density_a_tex) * x * 9.80665e-9 for x in dual_mm]
    governing = max(nodes, key=difference_n.__getitem__)
    return {"nodal_weight_difference_N": difference_n, "governing_free_node": governing,
            "common_pose_lower_bound_N": difference_n[governing] / 2}


if __name__ == "__main__":
    print(json.dumps(comparison([10, 20, 30], 100, 160, [1, 2]), indent=2))

"""Infer reciprocal section compliance from two measured force increments."""
from dataclasses import dataclass
import json
import math
import numpy as np


def pair_matrix(values):
    value = np.asarray(values, dtype=float)
    if value.shape != (2, 2) or not np.all(np.isfinite(value)):
        raise ValueError("Use two finite two-component measurement columns")
    return value


@dataclass(frozen=True)
class Fit:
    measured: np.ndarray
    symmetric: np.ndarray
    error_bound: float
    least_force_singular_value: float
    reciprocity_within_bound: bool
    positive_definite_within_bound: bool

    def check(self, load, movement, load_error, movement_error):
        """Compare a separate combined load with the measured response."""
        p = np.asarray(load, dtype=float)
        y = np.asarray(movement, dtype=float)
        if p.shape != (2,) or y.shape != (2,) or not np.all(np.isfinite([p, y])):
            raise ValueError("Use one finite force/displacement vector pair")
        if not all(math.isfinite(v) and v >= 0 for v in (load_error, movement_error)):
            raise ValueError("Use finite nonnegative per-component error bounds")
        model_norm = np.linalg.norm(self.symmetric, 2)
        limit = (math.sqrt(2) * movement_error + self.error_bound * np.linalg.norm(p)
                 + math.sqrt(2) * load_error * (model_norm + self.error_bound))
        residual = float(np.linalg.norm(y - self.symmetric @ p))
        return dict(residual_mm=residual, bound_mm=float(limit), within_bound=bool(residual <= limit))


def fit(loads, movements, load_error, movement_error):
    """Errors bound accumulated errors in each entry after reference/fixture subtraction."""
    p, y = pair_matrix(loads), pair_matrix(movements)
    if not all(math.isfinite(v) and v >= 0 for v in (load_error, movement_error)):
        raise ValueError("Use finite nonnegative per-component error bounds")
    strength = float(np.linalg.svd(p, compute_uv=False)[-1])
    if strength <= 2 * load_error:
        raise ValueError("The two independent applied loads are unresolved within the force uncertainty")
    measured = np.linalg.solve(p.T, y.T).T
    error = float((2 * movement_error + 2 * load_error * np.linalg.norm(measured, 2))
                  / (strength - 2 * load_error))
    symmetric = (measured + measured.T) / 2
    reciprocal = bool(abs(measured[0, 1] - measured[1, 0]) <= 2 * error)
    positive = bool(reciprocal and np.linalg.eigvalsh(symmetric)[0] > error)
    return Fit(measured, symmetric, error, strength, reciprocal, positive)


if __name__ == "__main__":
    load = np.array([[.4, 0], [0, .4]])
    displacement = np.array([[.160, .048], [.048, .120]])
    result = fit(load, displacement, .001, .001)
    print(json.dumps(dict(compliance_mm_per_N=result.symmetric.tolist(),
                          spectral_error_mm_per_N=result.error_bound,
                          reciprocal=result.reciprocity_within_bound,
                          positive_within_bound=result.positive_definite_within_bound,
                          holdout=result.check([.2,.2],[.104,.084],.001,.001)), indent=2))

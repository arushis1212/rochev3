"""A gravity-loaded circle supported by two symmetric compliant yarn contacts."""
import json
import math


def response(height_mm, lateral_mm, contact_radius_mm, stiffness_n_per_mm, weight_n):
    """Return the vertical potential gradient and its height derivative."""
    radius = math.hypot(lateral_mm, height_mm)
    penetration = max(0.0, contact_radius_mm - radius)
    if penetration == 0:
        return weight_n, 0.0
    preload = 2 * stiffness_n_per_mm * penetration * height_mm / radius
    tangent = 2 * stiffness_n_per_mm * (1 - contact_radius_mm*lateral_mm**2/radius**3)
    return weight_n - preload, tangent


def equilibrium(lateral_mm, contact_radius_mm=10.5, stiffness_n_per_mm=4.0, mass_kg=0.025):
    """Find the stable equilibrium of the two-contact analytical model."""
    values = (lateral_mm, contact_radius_mm, stiffness_n_per_mm, mass_kg)
    if not all(math.isfinite(v) and v > 0 for v in values) or lateral_mm >= contact_radius_mm:
        raise ValueError("Expected positive dimensions, stiffness and mass with possible contact")
    weight = mass_kg * 9.80665
    critical_radius = (contact_radius_mm * lateral_mm**2)**(1/3)
    critical_height = math.sqrt((critical_radius-lateral_mm)*(critical_radius+lateral_mm))
    release_height = math.sqrt((contact_radius_mm-lateral_mm)*(contact_radius_mm+lateral_mm))
    def evaluate(z):
        return response(z, lateral_mm, contact_radius_mm, stiffness_n_per_mm, weight)
    if evaluate(critical_height)[0] >= 0:
        raise ValueError("The contact pair cannot supply a stable balance for this weight")
    lo, hi = critical_height, release_height
    # Positive stiffness throughout this open interval makes this root unique.
    for _ in range(60):
        midpoint = (lo + hi)/2
        if evaluate(midpoint)[0] > 0:
            hi = midpoint
        else:
            lo = midpoint
    height = (lo + hi)/2
    gradient, tangent = evaluate(height)
    return {"lateral_mm": lateral_mm, "height_mm": height, "weight_n": weight,
            "residual_n": gradient, "vertical_stiffness_n_per_mm": tangent}


def load_envelope(lateral_mm, contact_radius_mm, stiffness_n_per_mm, mass_kg, bias_n):
    """Bound stable height under an additive, height-independent vertical load."""
    gravity = 9.80665
    weight = mass_kg * gravity
    if not math.isfinite(bias_n) or bias_n < 0 or bias_n >= weight:
        raise ValueError("The entire prescribed load interval must be finite and positive")
    def at_load(force_n):
        return equilibrium(lateral_mm, contact_radius_mm, stiffness_n_per_mm, force_n/gravity)
    low_height = at_load(weight + bias_n)
    high_height = at_load(weight - bias_n)
    # The tangent grows with height on this branch, so the lowest height bounds it.
    return {"load_interval_n": [weight-bias_n, weight+bias_n],
            "stable_height_interval_mm": [low_height["height_mm"], high_height["height_mm"]],
            "minimum_stiffness_n_per_mm": low_height["vertical_stiffness_n_per_mm"]}


if __name__ == "__main__":
    print(json.dumps([equilibrium(x) for x in (5.5, 6.0, 6.5)], indent=2))

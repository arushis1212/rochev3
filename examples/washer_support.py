"""Guaranteed planar bearing area for a washer near one straight plate edge."""
import json
import math


def supported_disk(radius, signed_center_distance):
    """Area on the supported side; positive distance places the center on the plate."""
    if radius == 0 or signed_center_distance <= -radius:
        return 0.
    if signed_center_distance >= radius:
        return math.pi * radius**2
    d = signed_center_distance
    half_chord = math.sqrt((radius - d) * (radius + d))
    return radius**2 * math.atan2(half_chord, -d) + d * half_chord


def bearing_area(flat_outer_radius, washer_bore_radius, plate_bore_radius,
                 nominal_edge_distance, center_uncertainty):
    """The nominal plate bore is concentric with the nominal washer center, in mm."""
    values = (flat_outer_radius, washer_bore_radius, plate_bore_radius,
              nominal_edge_distance, center_uncertainty)
    if not all(math.isfinite(v) for v in values):
        raise ValueError("Dimensions must be finite")
    if min(washer_bore_radius, plate_bore_radius, center_uncertainty) < 0:
        raise ValueError("Radii and center uncertainty must be nonnegative")
    if flat_outer_radius <= washer_bore_radius:
        raise ValueError("The washer must have a positive flat annulus")
    excluded_radius = max(washer_bore_radius, plate_bore_radius + center_uncertainty)
    edge = nominal_edge_distance - center_uncertainty
    if excluded_radius >= flat_outer_radius:
        return 0.
    return max(0., supported_disk(flat_outer_radius, edge) - supported_disk(excluded_radius, edge))


if __name__ == "__main__":
    area = bearing_area(3.0, 1.55, 1.50, 1.80, .18)
    load = 36.
    print(json.dumps({"area_floor_mm2": area,
                      "average_pressure_ceiling_MPa_at_full_imprint": load/area}, indent=2))

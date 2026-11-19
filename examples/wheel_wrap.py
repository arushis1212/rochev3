"""Radial clearance loss when a circular yarn trajectory is interpolated by chords."""
import math


def chord_loss_mm(radius_mm, angle_rad):
    """Maximum inward distance from the minor arc over one straight segment."""
    if not math.isfinite(radius_mm) or radius_mm <= 0:
        raise ValueError("The centerline radius must be finite and positive")
    if not math.isfinite(angle_rad) or abs(angle_rad) > math.pi:
        raise ValueError("One subarc may span at most a half turn")
    return radius_mm * (2 * math.sin(angle_rad / 4)**2)


def segment_count(radius_mm, total_angle_rad, tolerance_mm):
    """Minimum equal-angle minor chords that meet a positive radial tolerance."""
    if not math.isfinite(total_angle_rad):
        raise ValueError("The turn angle must be finite")
    chord_loss_mm(radius_mm, 0)
    if not math.isfinite(tolerance_mm) or tolerance_mm <= 0:
        raise ValueError("The position tolerance must be finite and positive")
    turn = abs(total_angle_rad)
    relative_width = math.sqrt(min(tolerance_mm, radius_mm)) / math.sqrt(radius_mm)
    maximum_angle = min(math.pi, 4 * math.asin(relative_width / math.sqrt(2)))
    quotient = turn / maximum_angle
    if not math.isfinite(quotient) or quotient >= 2**53:
        raise ValueError("Segment count exceeds the integer resolution of the floating-point model")
    count = max(1, math.ceil(quotient))
    # Recheck the actual boundary when its quotient is within machine precision of an integer.
    if count > 1 and turn/(count-1) <= math.pi and chord_loss_mm(radius_mm, turn/(count-1)) <= tolerance_mm:
        count -= 1
    if turn/count > math.pi or chord_loss_mm(radius_mm, turn/count) > tolerance_mm:
        count += 1
    return count


if __name__ == "__main__":
    turn = math.radians(60)
    for count in (1, 2, 4, 8):
        print(count, "segments:", f"{chord_loss_mm(12., turn/count):.6f} mm greatest radial loss")
    print("Segments for 0.02 mm:", segment_count(12., turn, .02))

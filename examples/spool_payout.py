"""Unstrained length balance of a helical winding and an axially moving takeoff."""
import math
from dataclasses import dataclass


def nonnegative(value, name):
    if not math.isfinite(value) or value < 0:
        raise ValueError(name + " must be finite and nonnegative")
    return value


@dataclass(frozen=True)
class HelicalPayout:
    radius_mm: float
    pitch_mm: float

    def __post_init__(self):
        nonnegative(self.radius_mm, "winding radius")
        nonnegative(self.pitch_mm, "axial pitch")

    @classmethod
    def for_marks(cls, first_mm, next_mm, turns, pitch_mm):
        first_mm = nonnegative(first_mm, "first material mark")
        next_mm = nonnegative(next_mm, "second material mark")
        turns = nonnegative(turns, "turn count")
        pitch_mm = nonnegative(pitch_mm, "axial pitch")
        if next_mm < first_mm or turns == 0:
            raise ValueError("Require increasing material marks and a positive turn count")
        payout = (next_mm-first_mm)/turns
        circumference = math.sqrt(payout)*math.sqrt(payout+2*pitch_mm)
        return cls(circumference/(2*math.pi), pitch_mm)

    def lengths(self, turns):
        turns = nonnegative(turns, "turn count")
        circumference = 2*math.pi*self.radius_mm
        helix = math.hypot(circumference,self.pitch_mm)
        # Rationalized difference prevents loss of the payout for shallow radii.
        net = 0 if helix == 0 else circumference*(circumference/(helix+self.pitch_mm))
        return turns*helix, turns*self.pitch_mm, turns*net


if __name__ == "__main__":
    spool = HelicalPayout.for_marks(219.30876920587457,359.8804517871325,7,0.84)
    wound, takeoff, delivered = spool.lengths(7)
    print(f"Winding centerline radius  {spool.radius_mm:.9f} mm")
    print(f"Helix released             {wound:.9f} mm")
    print(f"Takeoff travel             {takeoff:.9f} mm")
    print(f"Delivered material         {delivered:.9f} mm")

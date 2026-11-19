"""Replay the forty first-station service poses on the published STEP shaft and screw."""
from hashlib import sha256
import json
from pathlib import Path

import cadquery as cq


def run(directory):
    settings = json.loads((directory / "service_poses.json").read_text())
    for name, expected in settings["cad_sha256"].items():
        if sha256((directory / name).read_bytes()).hexdigest() != expected:
            raise ValueError(f"Unexpected STEP file at {name}")
    pin = cq.importers.importStep(str(directory / "station0_pin.step")).val()
    tool = cq.importers.importStep(str(directory / "matched_driver.step")).val()
    if any(len(part.Solids()) != 1 or not part.isValid() for part in (pin, tool)):
        raise ValueError("A component needs to be one valid solid")
    x, y, z = settings["socket_origin_mm"]
    pivot = settings["tilt_pivot_z_local_mm"]
    worst_volume = worst_gap_error = 0.0
    for index, pose in enumerate(settings["poses"], 1):
        placed = (
            tool.rotate((0, 0, 0), (0, 0, 1), pose["clock_deg"])
            .rotate((0, 0, pivot), (0, 1, pivot), pose["tilt_deg"])
            .translate((x + pose["shift_mm"], y, z + pose["depth_mm"]))
        )
        volume = pin.intersect(placed).Volume()
        gap_error = abs(pin.distance(placed) - pose["gap_mm"])
        if (volume > settings["model_volume_tolerance_mm3"]
                or gap_error > settings["model_gap_tolerance_mm"]):
            raise ValueError(f"Pose {index} differs: overlap {volume} mm³, gap error {gap_error} mm")
        worst_volume = max(worst_volume, volume)
        worst_gap_error = max(worst_gap_error, gap_error)
    return len(settings["poses"]), worst_volume, worst_gap_error


if __name__ == "__main__":
    data = Path(__file__).resolve().parents[1] / "cad" / "service_driver"
    count, volume, gap_error = run(data)
    print(f"{count} CAD poses; largest overlap {volume:.3g} mm³; maximum gap difference {gap_error:.3g} mm")

"""Replay finite nose contact, material registration and friction forces in mm and N."""
import json
from pathlib import Path

import numpy as np


def evaluate(data):
    pivot = np.r_[data["pivot_mm"], 0.]
    nose = np.array(data["nose_center_at_zero_mm"])
    radius = data["nose_radius_mm"] + data["yarn_radius_mm"]

    def closest(row, center):
        p = np.array(row["nodes_eye_mm"])
        s = np.array(row["material_mm"])
        edge = np.diff(p, axis=0)
        fraction = np.clip(((center - p[:-1]) * edge).sum(1) /
                           (edge * edge).sum(1), 0., 1.)
        delta = p[:-1] + fraction[:, None] * edge - center
        distance = np.linalg.norm(delta, axis=1)
        i = int(distance.argmin())
        return float(distance[i] - radius), float(s[i] + fraction[i] * (s[i+1] - s[i]))

    closures = []
    for steps in data["angular_closures"].values():
        contacts = []
        for state in steps:
            a = np.deg2rad(state["angle_deg"])
            c, s = np.cos(a), np.sin(a)
            rotation = np.array([[c,-s,0.], [s,c,0.], [0.,0.,1.]])
            gap, mark = closest(state, pivot + rotation @ (nose - pivot))
            contacts.append([gap, mark, state["normal_N"]])
        closures.append(dict(initial_gap_mm=contacts[0][0], final_gap_mm=contacts[-1][0],
                             final_mark_mm=contacts[-1][1], final_normal_N=contacts[-1][2]))

    draws = []
    for state in data["draw_stops"]:
        gap, mark = closest(state, nose)
        normals = np.array(state["compressive_directions_eye"])
        forces = np.array(state["forces_eye_N"])
        compression = (forces * normals).sum(1)
        shear = np.linalg.norm(forces - compression[:, None] * normals, axis=1)
        # The normal points from the nose to the filament centerline.
        surface = nose + normals[0] * data["nose_radius_mm"]
        torque = np.cross(surface - pivot, -forces[0])[2]
        draws.append(dict(route_mm=state["route_mm"], skin_mm=gap,
                          mark_error_mm=mark-state["fixed_mark_mm"],
                          compressive_N=compression.tolist(), shear_N=shear.tolist(),
                          friction_slack_N=(data["contact_friction_screen"]*compression-shear).tolist(),
                          input_torque_Nmm=float(abs(torque))))
    return dict(closures=closures, draws=draws)


if __name__ == "__main__":
    path = Path(__file__).with_suffix(".json")
    result = evaluate(json.loads(path.read_text()))
    print(json.dumps({"closures":result["closures"], "last_draw":result["draws"][-1]}, indent=2))

"""Run the finite-cord reference calculation from the current design inputs."""
from pathlib import Path
import sys,json
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from physics.r5_feed_geometry import geometry_screen
s=json.loads((ROOT/'spec/r5_m2_fixture.json').read_text())
r=geometry_screen(s)
print(json.dumps({k:r[k] for k in ('effective_length_at_midstroke_mm','low_mode_positions','park_counter_center_mm','finite_yarn_tangents')},indent=2))

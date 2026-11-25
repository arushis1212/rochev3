"""Report the tolerance stack of the issued feeder ball retainer in mm."""
import json
from pathlib import Path
from meridian import tolerance

if __name__=='__main__':
    geometry=json.loads(Path(__file__).with_name('SPEC.json').read_bytes())
    result=tolerance(geometry)
    for key in ('clearance_lower_mm','minimum_intact_straight_land_mm','escape_blocking_margin_mm'):
        if result[key]<=0:raise ValueError(key)
        print(f"{key}: {result[key]:.9f} mm")

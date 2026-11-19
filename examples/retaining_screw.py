"""Screen a circular screw head between a yarn path and a planar bearing land."""
from dataclasses import dataclass
import json
import math


@dataclass(frozen=True)
class Joint:
    load_N: float
    bearing_limit_MPa: float
    imprint_fraction: float
    inner_land_radius_mm: float
    unsupported_head_rim_mm: float
    supported_outer_radius_mm: float
    path_to_axis_mm: float
    yarn_radius_mm: float
    relative_position_error_mm: float
    required_free_gap_mm: float

    def diameter_interval_mm(self):
        values=vars(self)
        if any(not math.isfinite(x) or x<0 for x in values.values()):
            raise ValueError("Use finite nonnegative loads, dimensions and allowances")
        if self.load_N<=0 or self.bearing_limit_MPa<=0 or not 0<self.imprint_fraction<=1:
            raise ValueError("Require positive load, bearing limit and an imprint fraction at most one")
        area=self.load_N/(self.bearing_limit_MPa*self.imprint_fraction)
        outer=math.sqrt(self.inner_land_radius_mm**2+area/math.pi)
        minimum=2*(outer+self.unsupported_head_rim_mm)
        maximum=2*(self.path_to_axis_mm-self.yarn_radius_mm
                   -self.relative_position_error_mm-self.required_free_gap_mm)
        return dict(minimum_diameter_mm=minimum,maximum_diameter_mm=maximum,
                    minimum_supported_outer_radius_mm=outer,
                    feasible=outer<=self.supported_outer_radius_mm and minimum<=maximum)


if __name__=="__main__":
    coupon=Joint(load_N=24,bearing_limit_MPa=25,imprint_fraction=.8,
                 inner_land_radius_mm=1.2,unsupported_head_rim_mm=.10,
                 supported_outer_radius_mm=1.6,path_to_axis_mm=2.5,
                 yarn_radius_mm=.35,relative_position_error_mm=.25,required_free_gap_mm=.1)
    print(json.dumps(coupon.diameter_interval_mm(),indent=2))

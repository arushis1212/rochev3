"""Analytical finite sphere distance to a cylindrical pilot and its countersink."""
import math


def point_segment(point, start, end):
    dx,dy=end[0]-start[0],end[1]-start[1]
    norm=dx*dx+dy*dy
    t=0. if not norm else max(0.,min(1.,((point[0]-start[0])*dx+(point[1]-start[1])*dy)/norm))
    q=(start[0]+t*dx,start[1]+t*dy)
    return math.dist(point,q),q


def closest(radius, center_radial, center_above_top, bore, depth, half_angle, thickness):
    """Rim geometry in cylindrical coordinates. Axial coordinate increases downward."""
    if not (0 < bore and radius>0 and thickness>=depth>=0 and 0<=center_radial<bore and center_above_top>=0):
        raise ValueError("Outside the interior upper-sphere branch")
    point=(center_radial,-center_above_top)
    lip=(bore+depth*math.tan(math.radians(half_angle)),0.)
    shoulder=(bore,depth)
    bottom=(bore,thickness)
    candidates=[(*point_segment(point,a,b),name) for a,b,name in
                [(lip,shoulder,"bevel"),(shoulder,bottom,"through hole")]]
    distance,location,owner=min(candidates)
    return distance-radius,location,owner


def escape(bounds, radius):
    """Barrier radius inside a pair of continuous annuli whose holes bound the ball."""
    r=min(bounds["ball_diameter_measured_envelope"])/2
    a=max(bounds["through_diameter"])/2+bounds["aperture_to_seat_transverse_error"]+bounds["combined_edge_profile_burr_allowance"]
    b=bounds["cup_lip_diameter_max"]/2
    # A guaranteed coaxial ring in the lower parallel plane can be avoided
    # by tilt. Enclose every tilted rim point by its worst radial and axial
    # displacement in machine coordinates; include the full surviving thickness.
    tilt=math.radians(bounds["retainer_tilt_deg_max"])
    a+=max(bounds["steel_thickness"])*math.sin(tilt)
    separation=(max(bounds["local_seated_ball_center_height_above_foil"])+max(bounds["steel_thickness"])+
                bounds["cup_lip_height_above_seated_center_max"]+(a+radius)*math.sin(tilt))
    if not radius<a<min(bounds["full_lower_rim_outer_radius_min_from_seat"],r) or not radius<b<min(bounds["full_upper_rim_outer_radius_min_from_seat"],r):
        raise ValueError("Finite circle for a complete barrier is missing")
    required=math.sqrt(r*r-(a-radius)**2)+math.sqrt(r*r-(b-radius)**2)
    return dict(barrier_radius_mm=radius,maximum_plane_separation_mm=separation,
                required_separation_at_barrier_mm=required,escape_blocking_margin_mm=required-separation,
                pilot_smaller_than_smallest_ball_radial_mm=r-max(bounds["through_diameter"])/2)


def tolerance(spec):
    b=spec["receiving"];motion=spec["motion"]
    tilt=math.radians(b["retainer_tilt_deg_max"])
    R=max(b["ball_diameter_measured_envelope"])/2
    rho=motion["design_radial_excursion_mm"]+b["aperture_to_seat_transverse_error"]
    axial=min(b["local_seated_ball_center_height_above_foil"])-motion["design_additional_axial_drop_mm"]
    # Bound rotation of the relative center about the measured aperture center.
    rotation=2*math.sin(tilt/2)*math.hypot(max(b["local_seated_ball_center_height_above_foil"]),rho)
    error=rotation+b["combined_edge_profile_burr_allowance"]
    # A pilot/spot axis mismatch subtracts e from the inscribed conical radius.
    # Equivalently let the whole ball advance toward both axes by e. This
    # deliberately also debits the pilot, which is slightly more conservative.
    rho+=b["outer_cone_to_bore_axis_error"]
    value,winner,owner=closest(R,rho,axial,min(b["through_diameter"])/2,min(b["countersink_depth"]),
                               min(b["half_angle_deg"]),max(b["steel_thickness"]))
    # Growing pilot, depth or cone angle removes material and increases clearance.
    # Shortening the overall plate below the contact likewise removes material.
    old,_,_=closest(R,rho,axial,.22,0.,45.,max(b["steel_thickness"]))
    return dict(clearance_lower_mm=value-error,original_straight_worst_scenario_mm=old-error,
                limiting_meridian_point_mm=winner,limiting_face=owner,rotation_and_form_budget_mm=error,
                minimum_intact_straight_land_mm=min(b["steel_thickness"])-max(b["countersink_depth"]),
                **escape(b,motion["barrier_radius_from_cup_axis"]))

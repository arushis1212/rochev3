"""Finite-radius, frictionless geometric screens. Millimetres, radians."""
import math

def rope_length(main_anchor_z,counter_anchor_z,radius=8.5,geometry=None):
    # Two equal upper idlers at(56,250),(88,250), anchorsX48/96.
    # The8mm lateral center offset differs from effective cord radius8.5.
    g=geometry or {};height=g.get("idler_height_mm",250.0);a=g.get("end_horizontal_offset_mm",8.0)
    total=g.get("idler_span_mm",32.0)
    for anchor in (main_anchor_z,counter_anchor_z):
        h=height-anchor;d=math.hypot(a,h)
        if h<=0 or d<=radius:raise ValueError('Anchor outside admitted below-idler domain')
        delta=math.atan2(h,a)-math.acos(radius/d)
        total+=math.sqrt(d*d-radius*radius)+radius*(math.pi/2+delta)
    return total

def counter_center(main_anchor_z,length,radius=8.5,geometry=None):
    g=geometry or {};eye=g.get("counter_eye_above_center_mm",10.0)
    lo,hi=80.,215.
    if not rope_length(main_anchor_z,lo+eye,radius,g)>=length>=rope_length(main_anchor_z,hi+eye,radius,g):raise ValueError('No counterweight solution in admitted travel')
    for _ in range(60):
        mid=(lo+hi)/2
        if rope_length(main_anchor_z,mid+eye,radius,g)>length:lo=mid
        else:hi=mid
    return (lo+hi)/2

def geometry_screen(s):
    f=s['feeder'];r=f['pulley_groove_radius']+f['rope_d']/2
    g=f['cord_geometry'];eye=g['main_eye_above_center_mm']
    length=rope_length(g['midstroke_main_center_mm']+eye,g['midstroke_counter_center_mm']+g['counter_eye_above_center_mm'],r,g)
    cord=[]
    for z in (130.,160.,190.):
        exact=counter_center(z+eye,length,r,g)
        cord.append({'main_center_z_mm':z,'counter_center_z_exact_mm':exact,'CAD_center_z_mm':counter_center(z+eye,f['rope_geometric_length_mm'],r,g),'CAD_error_mm':counter_center(z+eye,f['rope_geometric_length_mm'],r,g)-exact})
    yarn=[]
    for d in (.25,.6):
        # Internal common tangents between fixed/moving pulleys16mm apart inX.
        # Worst tangent angle at minimum vertical separation40mm.
        delta=math.atan2(40,16)-math.acos((16+d)/math.hypot(16,40))
        yarn.append({'yarn_diameter_mm':d,'maximum_leg_tilt_rad':delta,'maximum_tension_multiplier_vs_mg_over_2':1/math.cos(delta),'storage_lower_bound_mm':120*math.cos(delta),'storage_upper_bound_mm':120})
    return {'counter_cord_effective_radius_mm':r,'effective_length_at_midstroke_mm':length,'low_mode_positions':cord,'park_counter_center_mm':counter_center(f['park_anchor'][2],length,r,g),'finite_yarn_tangents':yarn,'qualified':False,'applicability':'Inextensible centerlines tangent to circular pulleys, no friction/stretch/dynamic motion. Effective cord length is set after tying; rough cut includes knot allowance. CAD solves the same constant-length geometry; material stretch and friction remain excluded.'}

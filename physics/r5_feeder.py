"""Auditable mass/ideal force screen, not a qualified tension simulator."""
import math

def mass_budget(cad, parts):
    f=cad.S['feeder']; a=f['mass_admission']; rows=[]
    def add(name, quantity, volume, rho, category):
        rows.append({'part':name,'quantity':quantity,'solid_or_envelope_mm3':volume,'density_ceiling_g_cm3':rho,'mass_ceiling_g':quantity*volume*rho/1000,'category':category})
    for name,n in [('P04_carrier',1),('P05_pulley_half',2)]:add(name,n,parts[name].val().Volume(),a['polymer_density_max_g_cm3'],'solid polymer ceiling, not assumed infill')
    for name in ('P07_spacer4','P21_spacer2'):add(name,1,parts[name].val().Volume(),a['brass_density_max_g_cm3'],'solid brass')
    join=f['pulley_join_screw_length_mm']
    for name,n,obj in [('M3x20',1,cad.bolt(3,20)),('M3nut',1,cad.nut(3)),(f'M2x{join:g}',2,cad.bolt(2,join)),('M2nut',2,cad.nut(2))]:add(name,n,obj.val().Volume(),a['steel_density_max_g_cm3'],'steel enclosing solid; threads unremoved')
    rows.append({'part':'623-2Z','quantity':1,'mass_ceiling_g':a['bearing_max_g'],'category':'weighed acceptance ceiling; source typical1.5g'})
    rows.append({'part':'cord/adhesive','quantity':1,'mass_ceiling_g':a['additional_cord_adhesive_max_g'],'category':'weighed allocation'})
    total=sum(r['mass_ceiling_g'] for r in rows); target=f['main_total_mass_g']
    return {'components':rows,'unballasted_mass_ceiling_g':total,'target_mass_g':target,'ballast_margin_g':target-total,
            'mass_screen_pass':total <= target-a['total_mass_tolerance_g'],
            'qualified':False,'conditions':'All admitted density/part mass ceilings and actual print dimensions must hold. Weigh full assembly, trim ballast and verify COM/friction. Mass-only screen does not establish dynamic output tension.'}

def center_of_mass_screen(cad,ps):
    a=cad.S['feeder']['mass_admission']; samples=[]
    def part(shape,rho):
        v=shape.val() if hasattr(shape,'val') else shape
        m=v.Volume()*rho/1000; center=v.Center();samples.append((m,center.x,center.y,center.z))
    part(ps['P04_carrier'],a['polymer_density_max_g_cm3'])
    for half in (ps['P05_pulley_half'],ps['P05_pulley_half'].mirror('XY')):part(cad.place(half,(48,406,0),(1,0,0),(0,1,0)),a['polymer_density_max_g_cm3'])
    for name,y in [('P07_spacer4',400),('P21_spacer2',408)]:part(cad.place(ps[name],(48,y,0),(1,0,0),(0,1,0)),a['brass_density_max_g_cm3'])
    part(cad.place(cad.bolt(3,20),(48,400,0),(1,0,0),(0,-1,0)),a['steel_density_max_g_cm3'])
    part(cad.place(cad.nut(3),(48,414,0),(1,0,0),(0,1,0)),a['steel_density_max_g_cm3'])
    for x in (41.5,54.5):
        part(cad.place(cad.bolt(2,cad.S['feeder']['pulley_join_screw_length_mm']),(x,409,0),(1,0,0),(0,1,0)),a['steel_density_max_g_cm3'])
        part(cad.place(cad.nut(2),(x,401.4,0),(1,0,0),(0,1,0)),a['steel_density_max_g_cm3'])
    samples.extend([(a['bearing_max_g'],48,406,0),(a['additional_cord_adhesive_max_g'],48,406,14)])
    total=sum(x[0] for x in samples); ym=sum(m*y for m,x,y,z in samples); target=cad.S['feeder']['main_total_mass_g']; ballast=target-total
    return {'mass_at_density_ceilings_g':total,'unballasted_center_mm':[sum(r[0]*r[i] for r in samples)/total for i in (1,2,3)],'ballast_to_target_g':ballast,'ballast_center_y_for_exact_balance_mm':(target*406-ym)/ballast if ballast>0 else None,'center_y_with_ballast_at_399_mm':(ym+ballast*399)/target,'force_axis_xy_mm':[48,406],'qualified':False,'applicability':'Screen at simultaneous density ceilings, not an interval proof. Cord/adhesive lumped at central eye. Actual complete assembly must meet measured COM and friction admission; split ballast equally in two windows.'}

def force_budget(s):
    f=s['feeder'];g=9.80665;m=f['main_total_mass_g']/1000;mc=f['counterweight_mass_g']/1000
    return {'high_ideal_N':m*g/2,'low_ideal_N':(m-mc)*g/2,'stroke_mm':f['moving_center_z_range'][1]-f['moving_center_z_range'][0],
            'ideal_storage_mm':2*(f['moving_center_z_range'][1]-f['moving_center_z_range'][0]),
            'mass_tolerance_tension_N':f['mass_admission']['total_mass_tolerance_g']/1000*g/2,
            'balance_equation':'T1+T2=(m-mc)g +/- F_guide + m_eff*a; each pulley adds tension difference tau/r. HIGH mc=0. LOW includes moving counterweight inertia and rope/idler friction.',
            'qualified':False}

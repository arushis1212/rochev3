"""Reproduce the loaded cam travel and elastic stopping response. Units are mm, N and s."""
import json
import math
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SPEC=ROOT/'cad/fork_brake/design.json'

def simulate(settings,frequency_scale=1.,intervals=4000):
    """Integrate the actual fork response by RK4, independently of the cam synthesis."""
    s=settings
    w=2*math.pi*s['nominal_axial_frequency_Hz']*frequency_scale
    speed=s['entry_speed_mm_s'];length=s['brake_distance_mm'];end=2*length/speed
    rise=end*s['ramp_fraction'];acc=speed/(end-rise)
    def driver(t):
        if t>=end:return length
        if t<=rise:return speed*t-acc*t**3/(6*rise)
        if t>end-rise:return length-acc*(end-t)**3/(6*rise)
        u=t-rise
        return speed*rise-acc*rise**2/6+(speed-acc*rise/2)*u-acc*u*u/2
    def derivative(t,x,v):return v,w*w*(driver(t)-x)
    x=0.;v=speed;dt=end/intervals;peak=0.
    for i in range(intervals):
        t=i*dt;k1,l1=derivative(t,x,v)
        k2,l2=derivative(t+dt/2,x+dt*k1/2,v+dt*l1/2)
        k3,l3=derivative(t+dt/2,x+dt*k2/2,v+dt*l2/2)
        k4,l4=derivative(t+dt,x+dt*k3,v+dt*l3)
        x+=dt*(k1+2*k2+2*k3+k4)/6;v+=dt*(l1+2*l2+2*l3+l4)/6;peak=max(peak,x)
    return dict(duration_ms=1000*end,position_mm=x,speed_mm_s=v,
                residual_amplitude_mm=math.hypot(x-length,v/w),peak_or_dwell_bound_mm=max(peak,length+math.hypot(x-length,v/w)))
if __name__=='__main__':
    settings=json.loads(SPEC.read_text())
    for factor in (.9,1.,1.1):
        print(f'{factor:.1f} × nominal frequency',simulate(settings,factor))

"""Independently integrate the mounted cam, frame and receiver fork in the axial plane."""
import json
import math
from pathlib import Path

SPEC=Path(__file__).resolve().parents[1]/'cad/fork_brake/mounted.json'
def command(t,s):
    T=s['brake_s'];r=T*s['brake_ramp'];v=s['entry_speed_mm_s'];a=v/(T-r);L=s['travel_mm']
    if t<r:return v*t-a*t**3/(6*r),-a*t/r
    if t<T-r:
        u=t-r;return v*r-a*r*r/6+(v-a*r/2)*u-a*u*u/2,-a
    if t<T:return L-a*(T-t)**3/(6*r),-a*(T-t)/r
    u=t-T;D=s['working_dwell_s']
    if u>=D:return L,0.
    w=math.pi/D;si=math.sin(w*u);co=math.cos(w*u)
    E=si**4;E1=4*w*si**3*co;E2=4*w*w*(3*si*si*co*co-si**4)
    x=L;aa=0.
    for j,hz in enumerate(s['frequency_Hz']):
        f=2*math.pi*hz;A,B=s['coefficients_mm'][2*j:2*j+2]
        h=A*math.sin(f*u)+B*math.cos(f*u);dh=f*(A*math.cos(f*u)-B*math.sin(f*u))
        x+=E*h;aa+=E2*h+2*E1*dh-E*f*f*h
    return x,aa

def simulate(settings,intervals=48000):
    s=settings;m=s['fork_effective_kg'];mf=s['follower_and_fork_kg']-m
    base=s['frame_modal_mass_kg']+mf;T=s['brake_s']+s['working_dwell_s'];dt=T/intervals
    def deriv(t,y):
        x,v,z,dz=y;u,du2=command(t,s);f=s['k_wire_N_mm']*(z+u-x)
        return (v,1000*f/m,dz,(-1000*(s['k_frame_N_mm']*z+f)-mf*du2)/base)
    y=[0.,s['entry_speed_mm_s'],0.,0.];peak=0.
    for i in range(intervals):
        t=i*dt;d1=deriv(t,y)
        d2=deriv(t+.5*dt,[a+.5*dt*v for a,v in zip(y,d1)])
        d3=deriv(t+.5*dt,[a+.5*dt*v for a,v in zip(y,d2)])
        d4=deriv(t+dt,[a+dt*v for a,v in zip(y,d3)])
        y=[a+dt*(b+2*c+2*d+e)/6 for a,b,c,d,e in zip(y,d1,d2,d3,d4)]
        peak=max(peak,y[0])
    return dict(peak_fork_mm=peak,final_fork_mm=y[0],final_fork_mm_s=y[1],final_frame_mm=y[2],final_frame_mm_s=y[3])

if __name__=='__main__':print(simulate(json.loads(SPEC.read_text())))

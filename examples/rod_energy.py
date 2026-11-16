"""Uniform stretch reference case: energy and force have analytic solutions."""
from pathlib import Path
import sys
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from physics.roche_rod import energy_gradient
q=np.column_stack([np.linspace(0,10.1,11),np.zeros(11)])
energy,gradient=energy_gradient(q,np.ones(10),EA=2.,B=.1)
print({'energy_Nmm':energy,'end_force_N':float(gradient[-1,0]),'analytic_energy_Nmm':.001,'analytic_force_N':.02})

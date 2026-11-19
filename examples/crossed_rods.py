"""Print segment-quadrature convergence against exact energy and force."""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from physics.crossed_rod_contact import continuum, pair_minimum

if __name__ == '__main__':
    diameter, separation, penalty = .6, .59998, 1000.
    exact_energy, exact_force = continuum(diameter, separation, penalty)
    print(f'Exact energy: {exact_energy:.10g} N mm; force: {exact_force:.10g} N')
    print('Spacing (mm)  Active pairs  Energy ratio  Force ratio')
    for spacing in (.005, .001, .0005, .0001, .00005):
        energy, force, pairs = pair_minimum(spacing, diameter, separation, penalty)
        print(f'{spacing:12g}  {pairs:12d}  {energy/exact_energy:12.6f}  {force/exact_force:11.6f}')

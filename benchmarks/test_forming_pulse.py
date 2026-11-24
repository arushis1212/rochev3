import csv
from pathlib import Path
import unittest


DATA=Path(__file__).resolve().parents[1]/"examples/forming_face/forming_pulse.csv"


class FormingPulseTest(unittest.TestCase):
    def test_continuous_time_and_brass_energy(self):
        with DATA.open(newline="") as f:
            rows=[{key:float(value) for key,value in row.items()} for row in csv.DictReader(f)]
        self.assertEqual(len(rows),88)
        for i,row in enumerate(rows,1):
            self.assertAlmostEqual(row["cell_end_us"],305.5+.025*i,places=8)
            self.assertGreaterEqual(row["midpoint_normal_mN"],0.)
            stored=row["kinetic_Nmm"]+row["strain_Nmm"]
            self.assertLess(abs(stored-row["cumulative_external_work_Nmm"]),1e-20)
        self.assertEqual(sum(row["midpoint_normal_mN"]>0 for row in rows),85)
        self.assertAlmostEqual(rows[-1]["midpoint_normal_mN"],16.301736232,places=7)

"""Check the published 0.600 mm outlet trace and its physical units."""
import csv
from pathlib import Path
import unittest

FOLDER=Path(__file__).resolve().parents[1]/"cad/sprung_clamp/0p600"


class OutletTravel(unittest.TestCase):
    def test_published_shoe_and_bearing_trace(self):
        with (FOLDER/"shoe_travel.csv").open(newline="") as f:
            rows=[{key:float(value) for key,value in row.items()} for row in csv.DictReader(f)]
        self.assertEqual(len(rows),197)
        times=[r["time_us"] for r in rows]
        self.assertEqual(times,sorted(set(times)))
        self.assertEqual((times[0],times[-1]),(0.,309.6))
        for row in rows:
            self.assertAlmostEqual(row["remaining_travel_mm"]+row["shoe_position_mm"],.006,places=11)
            self.assertGreater(row["sphere_bearing_force_mN"],0.)
            self.assertGreaterEqual(row["steel_yarn_force_mN"],0.)
        self.assertAlmostEqual(min(r["remaining_travel_mm"] for r in rows),.0048338795354,places=10)
        self.assertAlmostEqual(rows[0]["steel_yarn_force_mN"],3.4377257154,places=8)
        self.assertEqual(rows[-1]["steel_yarn_force_mN"],0.)

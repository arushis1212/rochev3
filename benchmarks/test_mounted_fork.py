"""Verify the grounded STEP assembly and integrate the two coupled equations of motion."""
import hashlib
import json
import unittest
from examples.mounted_fork import SPEC,simulate

class TestMountedFork(unittest.TestCase):
    def test_frame_and_dwell(self):
        s=json.loads(SPEC.read_text())
        for name,digest in s['files'].items():
            self.assertEqual(hashlib.sha256((SPEC.parent/name).read_bytes()).hexdigest(),digest)
        self.assertEqual(len(s['stays_mm']),6)
        self.assertLess(s['shaft']['used_angle_rad'],s['shaft']['available_dwell_angle_rad'])
        y=simulate(s)
        self.assertLess(y['peak_fork_mm'],s['available_mm'])
        self.assertLess(abs(y['final_fork_mm']-s['travel_mm']),1e-5)
        self.assertLess(abs(y['final_fork_mm_s']),.01)
        self.assertLess(abs(y['final_frame_mm']),1e-5)
        self.assertLess(abs(y['final_frame_mm_s']),.01)

if __name__=='__main__':unittest.main()

"""Replay yarn crossings of a finite rectangular aperture in the original eye's moving frame."""
import json
from pathlib import Path


def crossings(segments, z, window):
    """Count directed passages. The half-open height test counts a shared vertex once."""
    xmin, xmax, ymin, ymax = window
    hits = []
    for first, second in segments:
        s0, x0, y0, z0 = first
        s1, x1, y1, z1 = second
        if not (z0 <= z < z1 or z1 <= z < z0):
            continue
        t = (z - z0) / (z1 - z0)
        x, y = x0 + t * (x1 - x0), y0 + t * (y1 - y0)
        if xmin <= x <= xmax and ymin <= y <= ymax:
            hits.append((s0 + t * (s1 - s0), 1 if z1 > z0 else -1))
    return hits


def replay(data):
    for row in data['stations']:
        hits = [crossings(row['segments'], z, data['window_xy_mm']) for z in data['section_z_mm']]
        yield row, hits


if __name__ == '__main__':
    data = json.loads((Path(__file__).resolve().parents[1]/'cad/castoff/eye_release.json').read_text())
    print('Payout (mm)   Crossings per section   Hook / jaw (mN)')
    for row, hits in replay(data):
        counts = ' '.join(str(len(x)) for x in hits)
        loads = row['jaw_normals_mN']
        print(f"{row['payout_mm']:11.6f}   {counts:22}  {loads['hook']:.3f} / {loads['jaw']:.3f}")

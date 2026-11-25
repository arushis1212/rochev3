"""Evaluate axial motion of the installed cartridge under a sinusoidal force."""
import argparse
import json
import math
from pathlib import Path

DATA = Path(__file__).with_name('AXIAL_MODES.json')


def displacement(force_mN, frequency_Hz=0., temperature_C=23):
    if not math.isfinite(force_mN):
        raise ValueError('Force must be finite')
    if not math.isfinite(frequency_Hz) or not 0 <= frequency_Hz <= 18000:
        raise ValueError('Use a frequency between 0 and 18000 Hz')
    if temperature_C not in (23, 40):
        raise ValueError('Select a modeled material case of 23 or 40 degrees C')
    case = json.loads(DATA.read_bytes())['cases'][str(temperature_C)]
    response = math.fsum(mode['static_contribution_mm_per_N'] /
                         (1-(frequency_Hz/mode['frequency_Hz'])**2)
                         for mode in case['modes'])
    # One mN times one mm/N gives one micrometre.
    return response * force_mN


if __name__=='__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--force-mn', type=float, default=10.)
    parser.add_argument('--frequency-hz', type=float, default=0.)
    parser.add_argument('--temperature-c', type=int, choices=(23,40), default=23)
    a=parser.parse_args()
    try:
        result=displacement(a.force_mn,a.frequency_hz,a.temperature_c)
    except ValueError as exc:
        parser.error(str(exc))
    print(f'{result:.6f} µm along the cartridge working axis (D01 Y)')

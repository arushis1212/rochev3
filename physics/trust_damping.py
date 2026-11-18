"""Optional persistent scalar damping for the absolute-Hessian search metric.

The physical objective and its Hessian remain unchanged. Only the positive
search metric is regularized. Updates use physical quadratic agreement and
backtracking relative to the proposed contact cap, not monotonic force reduction.
"""
from __future__ import annotations
import numpy as np


class AbsoluteDampingControl:
    def __init__(self, initial_N_per_mm=1., accumulate_good_capped_steps=False,
                 initial_good_step_credit=0.):
        if not np.isfinite(initial_N_per_mm) or initial_N_per_mm < 0:
            raise ValueError('Initial absolute damping must be finite and nonnegative')
        self.initial = self.next_damping = float(initial_N_per_mm)
        if type(accumulate_good_capped_steps) is not bool:
            raise ValueError('Capped-step accumulation flag must be boolean')
        if not np.isfinite(initial_good_step_credit) or not 0 <= initial_good_step_credit < 1:
            raise ValueError('Initial good-step credit must be finite in [0,1)')
        if not accumulate_good_capped_steps and initial_good_step_credit != 0:
            raise ValueError('Initial credit requires capped-step accumulation')
        self.accumulate = accumulate_good_capped_steps
        self.good_step_credit = float(initial_good_step_credit)
        self.increases = self.decays = self.holds = 0

    def update(self, *, used, old_energy, new_energy, predicted_reduction,
               accepted_alpha, proposed_cap_alpha, numerical_floor, hessian_scale):
        values = [used, old_energy, new_energy, predicted_reduction, accepted_alpha,
                  proposed_cap_alpha, numerical_floor, hessian_scale]
        if not np.isfinite(values).all():
            raise ValueError('Trust update received nonfinite data')
        if not 0 < accepted_alpha <= proposed_cap_alpha <= 1:
            raise ValueError('Accepted fraction must be within the proposed contact cap')
        if used < 0 or numerical_floor <= 0 or hessian_scale <= 0:
            raise ValueError('Trust damping and numerical scales are invalid')
        actual = old_energy-new_energy
        roundoff = 32*np.finfo(float).eps*max(1., abs(old_energy), abs(new_energy))
        ratio = actual/predicted_reduction if predicted_reduction > roundoff else None
        line_fraction = accepted_alpha/proposed_cap_alpha
        previous_credit = self.good_step_credit
        good_trial = ((ratio is not None and ratio > .75)
                      or (0 <= predicted_reduction <= roundoff and actual >= -roundoff))
        if self.accumulate:
            if good_trial and line_fraction >= 1.-1e-12:
                self.good_step_credit += accepted_alpha
            else:
                self.good_step_credit = 0.
        # A short geometric contact cap alone is not poor model agreement.
        # Backtracking is measured relative to that cap, not the full direction.
        if line_fraction < .25 or (ratio is not None and ratio < .25):
            value = max(used*4., numerical_floor, hessian_scale*1e-10)
            reason = 'backtracking_relative_to_cap' if line_fraction < .25 else 'poor_quadratic_agreement'
            action = 'increase'
            self.increases += 1
        elif (line_fraction >= 1.-1e-12 and good_trial
              and (accepted_alpha >= .5
                   or (self.accumulate and self.good_step_credit >= 1.-1e-12))):
            value = used*.5
            if value < numerical_floor:
                value = 0.
            reason = ('accumulated_good_capped_trials' if accepted_alpha < .5 else
                      'good_full_trial_agreement' if ratio is not None else 'roundoff_limited_full_trial')
            action = 'decay'
            self.decays += 1
            self.good_step_credit = 0.
        else:
            value = used
            reason = 'contact_cap_or_intermediate_agreement'
            action = 'hold'
            self.holds += 1
        if not np.isfinite(value):
            raise ValueError('Absolute damping overflowed its numerical range')
        self.next_damping = float(value)
        return {'used_damping_N_per_mm': float(used), 'next_damping_N_per_mm': self.next_damping,
                'action': action, 'reason': reason,
                'actual_energy_reduction_Nmm': float(actual),
                'physical_quadratic_predicted_reduction_Nmm': float(predicted_reduction),
                'actual_to_predicted_reduction': None if ratio is None else float(ratio),
                'energy_roundoff_floor_Nmm': float(roundoff),
                'accepted_alpha': float(accepted_alpha),
                'proposed_contact_cap_alpha': float(proposed_cap_alpha),
                'backtracking_fraction_relative_to_cap': float(line_fraction),
                'accumulate_good_capped_steps': self.accumulate,
                'previous_good_step_credit': previous_credit,
                'next_good_step_credit': self.good_step_credit,
                'geometric_cap_alone_does_not_increase_damping': True}

    def summary(self):
        return {'enabled': True, 'initial_N_per_mm': self.initial,
                'next_N_per_mm': self.next_damping, 'increases': self.increases,
                'decays': self.decays, 'holds': self.holds,
                'accumulate_good_capped_steps': self.accumulate,
                'next_good_step_credit': self.good_step_credit,
                'physical_objective_and_force_tolerance_unchanged': True}


def damping_from_config(config):
    if config is None:
        return None
    if not isinstance(config, dict):
        raise ValueError('Damping control configuration must be an object')
    if set(config)-{'enabled', 'initial_N_per_mm', 'accumulate_good_capped_steps', 'initial_good_step_credit'}:
        raise ValueError('Unknown damping control configuration fields')
    if type(config.get('enabled', False)) is not bool:
        raise ValueError('Damping control enabled flag must be boolean')
    if not config.get('enabled', False):
        return None
    return AbsoluteDampingControl(config.get('initial_N_per_mm', 1.),
                                  config.get('accumulate_good_capped_steps', False),
                                  config.get('initial_good_step_credit', 0.))

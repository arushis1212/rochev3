"""Optional short BFGS blocks initialized by an exact absolute-Hessian metric.

Only the search metric changes. The original energy, gradient, line search,
contact proposal limiter and swept physical guards decide every accepted step.
Inverse secant matrices are local to one invocation and are never checkpointed.
"""
from __future__ import annotations

import numpy as np

from physics.trust_damping import damping_from_config


def options_from_config(config):
    if config is None:
        return None
    if not isinstance(config, dict) or set(config) - {
        'enabled', 'refresh_interval', 'newton_below_residual_N'
    }:
        raise ValueError('Invalid guarded BFGS configuration')
    if type(config.get('enabled', False)) is not bool:
        raise ValueError('Guarded BFGS enabled flag must be boolean')
    interval = config.get('refresh_interval', 8)
    threshold = config.get('newton_below_residual_N', 1e-4)
    if type(interval) is not int or not 1 <= interval <= 32:
        raise ValueError('Exact Hessian refresh interval must be an integer in [1,32]')
    if not np.isfinite(threshold) or threshold <= 0:
        raise ValueError('Exact Newton switching residual must be finite and positive')
    return {'refresh_interval': interval, 'newton_below_residual_N': threshold} if config.get('enabled') else None


def inverse_bfgs_update(inverse, displacement, gradient_change):
    """Accept only resolvable positive curvature; otherwise request a rebuild."""
    s, y = np.asarray(displacement), np.asarray(gradient_change)
    sy = float(s @ y)
    relative_floor = 1e-10 * float(np.linalg.norm(s) * np.linalg.norm(y))
    if not np.isfinite(sy) or sy <= max(relative_floor, 1e-30):
        return None, {'accepted': False, 's_dot_y_Nmm': sy, 'reason': 'nonpositive_or_unresolved_curvature'}
    hy = inverse @ y
    updated = inverse + ((sy + float(y @ hy)) / sy**2) * np.outer(s, s)
    updated -= (np.outer(hy, s) + np.outer(s, hy)) / sy
    updated = .5 * (updated + updated.T)
    if not np.isfinite(updated).all():
        return None, {'accepted': False, 's_dot_y_Nmm': sy, 'reason': 'nonfinite_update'}
    return updated, {'accepted': True, 's_dot_y_Nmm': sy, 'reason': 'positive_curvature_secant'}


def minimize_guarded_bfgs(evaluate, start, hessian, *, gtol=1e-8, maxiter=200,
                          max_step=.25, callback=None, step_admissible=None,
                          contact_event_limiter=None, damping_control=None,
                          refresh_interval=8, newton_below_residual_N=1e-4):
    control = damping_from_config(damping_control)
    x = np.array(start, dtype=float, copy=True)
    E, g = evaluate(x)
    inverse = None
    since_refresh = refresh_interval
    iterations = refreshes = secants = skipped = 0
    reason = 'iteration_limit'
    largest_damping = metric_seed_damping = 0.
    for _ in range(maxiter):
        residual = float(np.max(abs(g)))
        if residual <= gtol:
            reason = 'force_residual'
            break
        fresh = inverse is None or since_refresh >= refresh_interval or residual <= newton_below_residual_N
        if fresh:
            physical = hessian(x)
            eig, vectors = np.linalg.eigh(physical)
            floor = max(1e-9, 1e-12 * float(np.max(abs(eig))))
            scale = max(1., float(np.max(abs(np.diag(physical)))))
            metric = np.maximum(abs(eig), floor)
            projected = vectors.T @ g
            metric_seed_damping = control.next_damping if control is not None else 0.
            for attempt in range(18):
                direction = -vectors @ (projected / (metric + metric_seed_damping))
                if float(np.max(abs(direction))) <= max_step:
                    break
                metric_seed_damping = scale*1e-10 if metric_seed_damping == 0 else metric_seed_damping*10
            else:
                reason = 'metric_step_bound'
                break
            inverse = (vectors / (metric + metric_seed_damping)) @ vectors.T
            since_refresh = 0
            refreshes += 1
        else:
            direction = -inverse @ g
            length = float(np.max(abs(direction)))
            if length > max_step:
                direction *= max_step / length
        slope = float(g @ direction)
        if not np.isfinite(direction).all() or slope >= 0:
            inverse = None
            if fresh:
                reason = 'non_descent_exact_metric'
                break
            continue
        event = None
        cap = 1.
        if contact_event_limiter is not None:
            event = contact_event_limiter(x, direction)
            cap = float(event['alpha'])
            if not np.isfinite(cap) or not 0 < cap <= 1:
                raise ValueError('Contact event fraction must be finite in (0,1]')
        alpha = cap
        accepted = False
        for line in range(35):
            candidate = x + alpha*direction
            try:
                En, gn = evaluate(candidate)
            except ValueError:
                En = float('inf')
            roundoff = 32*np.finfo(float).eps*max(1., abs(E))
            force_improved = residual <= 1e-6 and np.max(abs(gn)) < residual if np.isfinite(En) else False
            if np.isfinite(En) and (En <= E+1e-4*alpha*slope or (force_improved and En <= E+roundoff)):
                if step_admissible is None or step_admissible(x, candidate):
                    accepted = True
                    break
            alpha *= .5
        if not accepted:
            inverse = None
            if fresh:
                reason = 'line_search'
                break
            continue
        delta = candidate-x
        trust = None
        if control is not None and fresh:
            predicted = -float(g @ delta) - .5*float(delta @ physical @ delta)
            trust = control.update(used=metric_seed_damping, old_energy=E, new_energy=En,
                                   predicted_reduction=predicted, accepted_alpha=alpha,
                                   proposed_cap_alpha=cap, numerical_floor=floor, hessian_scale=scale)
            trust['physical_prediction_source'] = 'fresh_original_hessian'
        elif control is not None:
            # A stale Hessian is not presented as a fresh physical prediction.
            # Freeze the damping/credit until the next exact Hessian rebuild.
            trust = {'used_damping_N_per_mm': metric_seed_damping,
                     'next_damping_N_per_mm': control.next_damping,
                     'next_good_step_credit': control.good_step_credit,
                     'action': 'hold', 'reason': 'secant_step_has_no_fresh_physical_hessian',
                     'physical_quadratic_predicted_reduction_Nmm': None,
                     'actual_to_predicted_reduction': None,
                     'physical_prediction_source': None,
                     'backtracking_fraction_relative_to_cap': alpha/cap}
        inverse, update = inverse_bfgs_update(inverse, delta, gn-g)
        if inverse is None:
            skipped += 1
        else:
            secants += 1
        since_refresh += 1
        rebuild_reason = None
        if inverse is None:
            rebuild_reason = update['reason']
        elif alpha/cap < .25:
            inverse = None
            rebuild_reason = 'heavy_backtracking_relative_to_cap'
        elif (event is not None and event.get('selected_monitor') == 'moving_clamp'
              and event.get('verified_buffered_event') and event.get('event_kind') == 'activation'
              and alpha == cap):
            # New clamp contact couples free yarn to all six rigid-body DOFs.
            # Install its actual physical stiffness before another secant step.
            inverse = None
            rebuild_reason = 'verified_new_clamp_contact'
        x, E, g = candidate, En, gn
        iterations += 1
        largest_damping = max(largest_damping, metric_seed_damping)
        if callback is not None:
            info = {'iterations': iterations, 'energy_Nmm': float(E),
                    'residual_N': float(np.max(abs(g))),
                    'quasi_newton': {'fresh_physical_hessian': fresh,
                                     'exact_hessian_refreshes': refreshes,
                                     'steps_since_refresh': since_refresh,
                                     'refresh_interval': refresh_interval,
                                     'inverse_update': update, 'forced_rebuild_reason': rebuild_reason,
                                     'matrix_checkpointed': False}}
            if event is not None:
                info['contact_event'] = {**event, 'accepted_alpha': float(alpha),
                    'accepted_at_event_cap': bool(event.get('event_found') and alpha == cap),
                    'next_iteration_rebuilds_hessian': bool(inverse is None or since_refresh >= refresh_interval or np.max(abs(g)) <= newton_below_residual_N),
                    'metric_strategy': 'guarded_bfgs_with_periodic_exact_refresh'}
            if trust is not None:
                info['damping_control'] = trust
            callback(x, info)
    residual = float(np.max(abs(g)))
    result = {'optimizer_success': residual <= gtol,
              'message': 'force_residual' if residual <= gtol else reason,
              'iterations': iterations, 'energy_Nmm': float(E),
              'free_node_residual_N': residual,
              'max_solver_damping_N_per_mm': largest_damping,
              'method': 'guarded_bfgs_with_periodic_exact_refresh',
              'exact_hessian_refreshes': refreshes, 'positive_curvature_updates': secants,
              'skipped_updates': skipped, 'matrix_checkpointed': False}
    if control is not None:
        result['damping_control'] = control.summary()
    return x, result

"""Bounded step control for buffered changes of unilateral penalty contacts.

This module does not change an energy, force, material weight, or pass criterion.
The generic search verifies buffered sign changes using supplied Lipschitz bounds.
A budget/depth failure falls back explicitly to the original guarded line search;
it is never represented as a certificate that no event exists.
"""
from __future__ import annotations

import time
import numpy as np


class _SearchLimit(Exception):
    pass


class ContactEventLimiter:
    """Prepare(start, direction) supplies gaps(alpha), speeds, IDs and scope.

    gaps are distance minus yarn radius. speeds bound absolute gap change per
    unit alpha on [0,1], including moving geometry. The prepared sample set must
    contain every event claimed by its scope, with stable identities.
    """
    def __init__(self, prepare, activation_depth_mm=1e-5, max_queries=64,
                 max_depth=28, depth_tolerance_fraction=.125,
                 distance_roundoff_mm=1e-10, budget_check=None):
        if not np.isfinite(activation_depth_mm) or activation_depth_mm <= 0:
            raise ValueError('Contact activation depth must be finite and positive')
        if type(max_queries) is not int or max_queries < 2:
            raise ValueError('Contact event query budget must be an integer >=2')
        if type(max_depth) is not int or max_depth < 1:
            raise ValueError('Contact event depth budget must be a positive integer')
        if not 0 < depth_tolerance_fraction < 1:
            raise ValueError('Contact event depth tolerance fraction must be in(0,1)')
        if not np.isfinite(distance_roundoff_mm) or distance_roundoff_mm < 0:
            raise ValueError('Distance roundoff allowance must be finite and nonnegative')
        self.prepare = prepare
        self.activation_depth = float(activation_depth_mm)
        self.max_queries = max_queries
        self.max_depth = max_depth
        self.depth_tolerance = self.activation_depth * depth_tolerance_fraction
        self.roundoff = float(distance_roundoff_mm)
        self.budget_check = budget_check
        self.calls = self.events = self.incomplete = self.queries = 0
        self.seconds = 0.

    def __call__(self, start, direction):
        started = time.monotonic()
        self.calls += 1
        if self.budget_check:
            self.budget_check()
        monitor = self.prepare(start, direction)
        speed = np.asarray(monitor.speed_bounds, dtype=float)
        if speed.ndim != 1 or not np.isfinite(speed).all() or np.any(speed < 0):
            raise ValueError('Contact gap speed bounds must be finite nonnegative vectors')
        if len(monitor.sample_ids) != len(speed):
            raise ValueError('Contact sample identities and bounds differ')
        if len(set(monitor.sample_ids)) != len(speed):
            raise ValueError('Contact sample identities must be unique')
        cache = {}

        def gaps(alpha):
            if alpha not in cache:
                if len(cache) >= self.max_queries:
                    raise _SearchLimit('query_budget')
                if self.budget_check:
                    self.budget_check()
                value = np.asarray(monitor.gaps(float(alpha)), dtype=float)
                if value.shape != speed.shape or not np.isfinite(value).all():
                    raise ValueError('Contact samples changed identity/shape or became nonfinite')
                cache[alpha] = value
            return cache[alpha]

        result = {'alpha': 1., 'scope': monitor.scope,
                  'activation_depth_mm': self.activation_depth,
                  'event_found': False, 'search_complete': True,
                  'verified_buffered_event': False, 'sample_count': len(speed),
                  'fallback': None}
        if len(speed):
            initial = gaps(0.)
            sign = np.where(initial >= 0., 1., -1.)
            # Entry target is gap=-delta; separation target is gap=+delta.
            # All initial residuals are >=delta, so a finite bound excludes
            # zero-size event steps even when an initial sample is touching.
            def residual(alpha):
                return sign * gaps(alpha) + self.activation_depth

            def visit(a, fa, b, fb, depth):
                width = b-a
                allowance = speed * width
                if np.any(abs(fa-fb) > allowance + 4*self.roundoff):
                    raise ValueError('Contact gap violated its supplied motion bound')
                # Minimum of the endpoint Lipschitz cones. This is tighter than
                # subtracting half the interval width from the smaller endpoint.
                lower = np.minimum(np.minimum(fa, fb), (fa+fb-allowance)/2)
                if np.all(lower > self.roundoff):
                    return None
                crossed = np.flatnonzero(fb <= 0.)
                if (len(crossed) and np.all(fa > 0.)
                        and np.max(allowance, initial=0.) <= self.depth_tolerance):
                    witness = int(crossed[np.argmin(fb[crossed])])
                    return a, b, witness
                if depth >= self.max_depth:
                    raise _SearchLimit('depth_budget_or_unresolved_tangent')
                mid = (a+b)/2
                fm = residual(mid)
                left = visit(a, fa, mid, fm, depth+1)
                return left if left is not None else visit(mid, fm, b, fb, depth+1)

            try:
                bracket = visit(0., residual(0.), 1., residual(1.), 0)
                if bracket is not None:
                    a, b, witness = bracket
                    at = gaps(b)
                    result.update(alpha=float(b), event_found=True,
                                  verified_buffered_event=True,
                                  event_kind='activation' if sign[witness] > 0 else 'separation',
                                  sample_id=list(monitor.sample_ids[witness]),
                                  initial_gap_mm=float(initial[witness]),
                                  cap_gap_mm=float(at[witness]),
                                  alpha_bracket=[float(a), float(b)],
                                  bracket_motion_bound_mm=float(np.max(speed*(b-a), initial=0.)),
                                  target_depth_error_mm=float(abs(abs(at[witness])-self.activation_depth)),
                                  simultaneous_crossed_samples=int(np.sum(residual(b) <= 0.)))
                    self.events += 1
            except _SearchLimit as exc:
                result.update(search_complete=False, fallback=str(exc))
                self.incomplete += 1
        result['queries'] = len(cache)
        result['elapsed_s'] = time.monotonic()-started
        self.queries += len(cache)
        self.seconds += result['elapsed_s']
        return result

    def summary(self):
        return {'calls': self.calls, 'verified_events': self.events,
                'incomplete_search_fallbacks': self.incomplete,
                'distance_batch_queries': self.queries, 'elapsed_s': self.seconds,
                'activation_depth_mm': self.activation_depth,
                'query_budget_per_direction': self.max_queries,
                'depth_budget_per_direction': self.max_depth,
                'fallback_preserves_original_energy_and_path_guards': True}


class FrontStripperEventProvider:
    """Explicitly local R01 monitor, not coverage of every model obstacle.

    Uses the existing reference-midpoint quadrature without changing its weights.
    A conservative swept AABB selection keeps every R01 event over the trial.
    Other contact features and native hardware retain the existing line-search
    and geometric guard checks; this provider makes no event claim about them.
    """
    scope = ('R01_front_stripper only; all swept-selected fixed material '
             'quadrature samples; excludes other obstacles and native hardware')

    def __init__(self, model):
        self.model = model
        self.world = model.obstacle.base.base
        if not self.world.local.plates:
            raise ValueError('Cannot monitor a disabled front stripper')
        self.profile = self.world.local.profiles['R01_front_stripper']
        self.radius = float(model.cfg['yarn_radius_mm'])
        if not np.isfinite(self.radius) or self.radius <= 0:
            raise ValueError('Event monitor needs a finite positive yarn radius')

    def __call__(self, start, direction):
        from physics.edge_contact import edge_samples
        from physics.roche_contact3d import extrusion_bounds, extrusion_distance

        model, world = self.model, self.world
        q = model.unpack(start)[0]
        speeds = np.zeros(len(q))
        speeds[model.free] = np.linalg.norm(direction[:model.interior].reshape(-1, 3), axis=1)
        fixed_speeds, _ = model.step_speed_bounds(direction)
        speeds[model.fixed_indices] = fixed_speeds
        speeds[-1] = 0.
        if model.nip_grip:
            speeds[model.nip_grip.indices] = 0.
        local = (q-world.origin)@world.frame
        lo, hi = extrusion_bounds(self.profile)
        # A signed-distance event requires entering the radius-inflated solid
        # AABB; initial points farther than total motion cannot do that.
        edge, fractions, weights, _ = edge_samples(
            local, model.rest, model.counts, lo, hi,
            self.radius+float(np.max(speeds, initial=0.))+1e-10)
        bounds = (1-fractions)*speeds[edge]+fractions*speeds[edge+1]
        midpoint = np.rint(fractions*model.counts[edge]-.5).astype(int)
        ids = [('R01_front_stripper', int(e), int(i)) for e, i in zip(edge, midpoint)]
        profile, radius, scope = self.profile, self.radius, self.scope

        class Prepared:
            speed_bounds = bounds
            sample_ids = ids
            reference_weights_mm = weights

            def gaps(self, alpha):
                actual = model.unpack(start+alpha*direction)[0]
                points = (1-fractions[:, None])*actual[edge]+fractions[:, None]*actual[edge+1]
                points = (points-world.origin)@world.frame
                return extrusion_distance(points, profile)[0]-radius

        prepared = Prepared()
        prepared.scope = scope
        return prepared


def limiter_from_config(model, config, budget_check=None):
    """Opt-in runner adapter. Unknown scopes/options are configuration errors."""
    if not config:
        return None
    if not isinstance(config, dict):
        raise ValueError('Contact event configuration must be an object')
    allowed = {'enabled', 'scope', 'activation_depth_mm', 'max_queries',
               'max_depth', 'depth_tolerance_fraction', 'distance_roundoff_mm'}
    if set(config)-allowed:
        raise ValueError('Unknown contact event configuration fields')
    if type(config.get('enabled', False)) is not bool:
        raise ValueError('Contact event enabled flag must be boolean')
    if not config.get('enabled', False):
        return None
    if config.get('scope') != 'front_stripper':
        raise ValueError('Only the explicitly scoped front_stripper monitor is available')
    options = {k: v for k, v in config.items() if k not in ('enabled', 'scope')}
    return ContactEventLimiter(FrontStripperEventProvider(model),
                               budget_check=budget_check, **options)

"""Moving-clamp events in its body frame, with unchanged material-edge grips."""
from types import SimpleNamespace

import numpy as np

from physics.fixture_contact import ClampContact
from physics.rigid_clamp import rotation
from physics.edge_contact import edge_samples
from physics.compiled_clamp_distance import CompiledClampDistance


class MovingClampEventProvider:
    scope = ('Moving ClampContact only; fixed material quadrature and existing '
             'edge-specific grip reductions; excludes other obstacles')

    def __init__(self, model):
        self.model = model
        self.body = ClampContact(model.clamp_spec, np.zeros(3), np.zeros(3),
                                 model.fixed_section)
        self.distance_only = CompiledClampDistance(self.body)
        self.radius = float(model.cfg['yarn_radius_mm'])
        if not np.isfinite(self.radius) or self.radius <= 0:
            raise ValueError('Clamp event monitor needs a finite positive radius')

    def __call__(self, start, direction):
        model, body = self.model, self.body
        q, center, angles, _ = model.unpack(start)
        R, _ = rotation(angles, model.angle_scale)
        velocity = np.zeros_like(q)
        velocity[model.free] = direction[:model.interior].reshape(-1, 3)
        dc = direction[model.interior:model.interior+3]
        omega_bound = float(sum(abs(direction[model.interior+3:model.interior+6]))) / model.angle_scale
        relative_linear = velocity-dc
        # For free/world-fixed nodes, r(alpha)=q(alpha)-c(alpha) is affine.
        # |d(R.T r)/d alpha| <= |r'| + sum(|Euler'|)*max|r|.
        linear_speed = np.linalg.norm(relative_linear, axis=1)
        speeds = linear_speed + omega_bound*(np.linalg.norm(q-center, axis=1)+linear_speed)
        # A prescribed point on this same rigid body has constant body position.
        speeds[model.fixed_indices] = 0.
        local = (q-center)@R
        edge, fraction, weight, _ = edge_samples(local, model.rest, model.counts,
            body.local_lo, body.local_hi, self.radius+float(np.max(speeds, initial=0.))+1e-10)
        bounds = (1-fraction)*speeds[edge]+fraction*speeds[edge+1]
        midpoint = np.rint(fraction*model.counts[edge]-.5).astype(int)
        ids = [('moving_clamp', int(e), int(i)) for e, i in zip(edge, midpoint)]
        distance_only = self.distance_only
        groups = distance_only.groups_for_edges(edge)
        radius, scope = self.radius, self.scope

        class Prepared:
            speed_bounds = bounds
            sample_ids = ids
            reference_weights_mm = weight

            def gaps(self, alpha):
                actual, c, a, _ = model.unpack(start+alpha*direction)
                rotation_matrix, _ = rotation(a, model.angle_scale)
                points = (1-fraction[:, None])*actual[edge]+fraction[:, None]*actual[edge+1]
                local_points = (points-c)@rotation_matrix
                return distance_only.distances(local_points, groups)-radius

        prepared = Prepared()
        prepared.scope = scope
        return prepared


class CombinedContactLimiter:
    """Earliest verified cap among explicit monitors; incomplete scope is logged."""
    scope = ('R01 front stripper and moving ClampContact; fixed material '
             'quadrature; other contacts retain original energy/path/native guards')

    def __init__(self, front, clamp):
        self.components = {'front_stripper': front, 'moving_clamp': clamp}
        self.prepare = SimpleNamespace(scope=self.scope)

    def __call__(self, start, direction):
        results = {name: monitor(start, direction) for name, monitor in self.components.items()}
        selected = min(results, key=lambda name: (results[name]['alpha'], not results[name]['event_found']))
        row = dict(results[selected])
        complete = all(r['search_complete'] for r in results.values())
        row.update(scope=self.scope, selected_monitor=selected, component_events=results,
                   search_complete=complete, earliest_across_monitors_proven=complete,
                   fallback=None if complete else 'one_or_more_component_searches_incomplete',
                   selected_monitor_sample_count=row['sample_count'],
                   sample_count=sum(r['sample_count'] for r in results.values()),
                   queries=sum(r['queries'] for r in results.values()),
                   elapsed_s=sum(r['elapsed_s'] for r in results.values()))
        return row

    def summary(self):
        return {'scope': self.scope, 'components': {name: monitor.summary()
                for name, monitor in self.components.items()},
                'physical_energy_gradient_weights_and_guards_unchanged': True}

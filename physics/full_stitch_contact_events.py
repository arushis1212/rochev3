"""Buffered events for explicitly selected full-stitch analytical components.

This is search-step control only. It calls the original component distances at
the original material-edge midpoint quadrature, without changing any energy,
weight, reaction, grip, collision allowance, or acceptance criterion.
"""
import numpy as np

from physics.edge_contact import edge_samples


class AnalyticalComponentEventProvider:
    """Monitor named world components with a conservative swept sample set.

    The supported scene contract has one translating world component (the
    moving pulley); all other world components are fixed during this solve.
    The clamp has its own body-frame monitor. Component gaps are kept separate:
    taking a union minimum could hide a second body's contact activation.
    """

    def __init__(self, model, component_names):
        names = tuple(component_names)
        if not names or any(not isinstance(n, str) for n in names) or len(set(names)) != len(names):
            raise ValueError('Select distinct named analytical world components')
        scene = model.contacts
        contract = scene.dynamic_component_contract
        if (contract.get('other_dynamic_analytical_components') != []
                or contract.get('pulley_moving', {}).get('coordinates') != 'feeder z'
                or contract.get('pulley_moving', {}).get('object_identity_count') != 1):
            raise ValueError('The event monitor requires the explicit one-pulley motion contract')
        world = scene.world_obstacle.components
        all_parts = scene.obstacle.components
        if world.get('pulley_moving') is not scene.moving_pulley:
            raise ValueError('Moving pulley identity differs from the physical energy scene')
        selected = []
        for name in names:
            if name not in world or name == 'tail_clamp':
                raise ValueError('Unknown or non-world component: '+name)
            part = world[name]
            if (all_parts.get(name) is not part
                    or sum(x is part for x in all_parts.values()) != 1
                    or sum(x is part for x in world.values()) != 1):
                raise ValueError('Each selected component must occur once in the physical scene')
            if name != 'pulley_moving' and part is scene.moving_pulley:
                raise ValueError('Moving pulley has an unexpected component name')
            selected.append((name, part))
        radius = float(model.cfg['yarn_radius_mm'])
        if not np.isfinite(radius) or radius <= 0:
            raise ValueError('A finite positive yarn radius is required')
        self.model, self.components, self.radius = model, tuple(selected), radius
        self.scope = ('Named analytical components '+', '.join(names)+
            '; original fixed material quadrature; component outer-distance '
            'activation/separation only; excludes unselected components, '
            'internal closest-feature changes, yarn self-contact and native-only solids')

    def __call__(self, start, direction):
        model, radius = self.model, self.radius
        start, direction = np.array(start, dtype=float, copy=True), np.array(direction, dtype=float, copy=True)
        size = model.interior+7
        if (start.shape != (size,) or direction.shape != (size,)
                or not np.isfinite(start).all() or not np.isfinite(direction).all()):
            raise ValueError('Finite compatible full-stitch start and displacement required')
        q = model.unpack(start)[0]
        speeds = np.zeros(len(q))
        speeds[model.free] = np.linalg.norm(direction[:model.interior].reshape(-1, 3), axis=1)
        fixed_speeds, _ = model.step_speed_bounds(direction)
        speeds[model.fixed_indices] = fixed_speeds
        # World-fixed inlet nodes remain at zero speed. Actual tail-grip nodes
        # include translation and an enclosing Euler-rotation arc-length bound.
        if not np.isfinite(speeds).all() or np.any(speeds < 0):
            raise ValueError('Invalid material point motion bounds')
        model.set_obstacle_pose(start)
        groups, ids, weights, bounds = [], [], [], []
        try:
            for name, part in self.components:
                lo, hi = np.asarray(part.lo, float), np.asarray(part.hi, float)
                if (lo.shape != (3,) or hi.shape != (3,) or not np.isfinite(lo).all()
                        or not np.isfinite(hi).all() or np.any(lo > hi)):
                    raise ValueError('A finite enclosing component AABB is required')
                body_speed = abs(float(direction[-1])) if name == 'pulley_moving' else 0.
                reserve = radius+float(np.max(speeds, initial=0.))+body_speed+1e-10
                if not np.isfinite(reserve) or not np.isfinite(lo-reserve).all() or not np.isfinite(hi+reserve).all():
                    raise ValueError('Nonfinite swept component bounds')
                edge, fraction, weight, _ = edge_samples(q, model.rest, model.counts, lo, hi, reserve)
                midpoint = np.rint(fraction*model.counts[edge]-.5).astype(int)
                groups.append((part, edge, fraction))
                ids.extend((name, int(e), int(i)) for e, i in zip(edge, midpoint))
                weights.append(weight)
                bounds.append((1-fraction)*speeds[edge]+fraction*speeds[edge+1]+body_speed)
        finally:
            model.set_obstacle_pose(start)
        scope = self.scope

        class Prepared:
            sample_ids = ids
            reference_weights_mm = np.concatenate(weights)
            speed_bounds = np.concatenate(bounds)

            def gaps(self, alpha):
                if isinstance(alpha, (bool, np.bool_)) or not np.isfinite(alpha) or not 0 <= alpha <= 1:
                    raise ValueError('Trial fraction must be finite and in [0,1]')
                state = start+float(alpha)*direction
                try:
                    actual = model.unpack(state)[0]
                    model.set_obstacle_pose(state)
                    values = []
                    for part, edge, fraction in groups:
                        if len(edge):
                            points = (1-fraction[:, None])*actual[edge]+fraction[:, None]*actual[edge+1]
                            distance = (part.distance_for_edges(points, edge) if hasattr(part, 'distance_for_edges')
                                        else part.distance(points))[0]
                            value = np.asarray(distance, float)-radius
                            if value.shape != edge.shape or not np.isfinite(value).all():
                                raise ValueError('Component distances changed shape or became nonfinite')
                            values.append(value)
                        else:
                            values.append(np.empty(0))
                    return np.concatenate(values)
                finally:
                    model.set_obstacle_pose(start)

        prepared = Prepared()
        prepared.scope = scope
        return prepared

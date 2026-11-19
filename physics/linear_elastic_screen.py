"""Linear isotropic elastic component screens with explicit ideal supports.

Optional isolated FEA environment required. These models do not qualify an
anisotropic print, unilateral bearing clearance, fatigue, creep or a machine.
"""
import warnings

import numpy as np
from scipy.sparse.linalg import MatrixRankWarning
from skfem import Basis, ElementTetP2, ElementVector, FacetBasis, LinearForm
from skfem import MeshTet, asm, condense, solve
from skfem.helpers import dot
from skfem.models.elasticity import lame_parameters, linear_elasticity


def basis_and_stiffness(points_mm, tetra, E_MPa, poisson, max_vector_dofs=50000):
    if not np.isfinite([E_MPa, poisson]).all() or E_MPa <= 0 or not -1 < poisson < .5:
        raise ValueError('Positive modulus and stable isotropic Poisson ratio required')
    points = np.asarray(points_mm, float)
    tetra = np.asarray(tetra, int)
    if points.ndim != 2 or points.shape[1] != 3 or not np.isfinite(points).all():
        raise ValueError('Finite Nx3 mesh points required')
    if tetra.ndim != 2 or tetra.shape[1] != 4 or tetra.size == 0:
        raise ValueError('Nonempty four-node tetrahedral geometry required')
    if tetra.min() < 0 or tetra.max() >= len(points):
        raise ValueError('Mesh connectivity outside the point array')
    mesh = MeshTet(points.T, tetra.T)
    basis = Basis(mesh, ElementVector(ElementTetP2()), intorder=4)
    if basis.N > max_vector_dofs:
        raise ValueError(f'Component mesh has {basis.N} DOFs, above local resource limit {max_vector_dofs}')
    stiffness = asm(linear_elasticity(*lame_parameters(E_MPa, poisson)), basis)
    return mesh, basis, stiffness


def facet_indices(mesh, surface_triangles, group_indices):
    lookup = {tuple(sorted(face)): j for j, face in enumerate(mesh.facets.T)}
    boundary = set(mesh.boundary_facets().tolist())
    result = []
    for triangle in np.asarray(surface_triangles, int)[group_indices]:
        key = tuple(sorted(triangle.tolist()))
        if key not in lookup or lookup[key] not in boundary:
            raise ValueError('Declared contact face is not a mesh boundary triangle')
        result.append(lookup[key])
    if not result:
        raise ValueError('Required contact face group is empty')
    return np.unique(result)


def normal_bore_load(basis, facets, force_N):
    """Downward local-y load using compressive lower-bore normal pressure.

    The solid's outward normal on the lower bore points upward into its void.
    Pressure is proportional to max(n_y,0), then normalized to the requested
    total downward force. It is a specified smooth load distribution, not a
    solved pin/bore contact-pressure field.
    """
    if not np.isfinite(force_N) or force_N <= 0:
        raise ValueError('A finite positive bore load is required')
    surface = FacetBasis(basis.mesh, basis.elem, facets=facets, intorder=4)

    @LinearForm
    def pressure(v, w):
        return -np.maximum(w.n[1], 0.)*dot(w.n, v)

    load = asm(pressure, surface)
    downward = -float(load[basis.split_indices()[1]].sum())
    if downward <= 1e-12:
        raise ValueError('Selected bore surface has no lower contact area')
    return load*(force_N/downward)


def uniform_body_force(basis, force_density_N_mm3):
    density = np.asarray(force_density_N_mm3, float)
    if density.shape != (3,) or not np.isfinite(density).all():
        raise ValueError('Finite body-force density vector required')

    @LinearForm
    def body(v, w):
        return sum(density[j]*v[j] for j in range(3))

    return asm(body, basis)


def solve_ideal_supports(basis, stiffness, load, constrained_dofs):
    fixed = np.unique(np.asarray(constrained_dofs, int))
    if not len(fixed) or fixed.min() < 0 or fixed.max() >= basis.N:
        raise ValueError('Valid physical-support DOFs required')
    with warnings.catch_warnings():
        warnings.simplefilter('error', MatrixRankWarning)
        displacement = solve(*condense(stiffness, load, D=fixed))
    if not np.isfinite(displacement).all():
        raise ValueError('Elastic solution is not finite')
    residual = stiffness@displacement-load
    free = np.setdiff1d(np.arange(basis.N), fixed)
    free_residual = float(np.max(np.abs(residual[free])))
    if free_residual > 1e-8*max(1., np.linalg.norm(load, ord=1)):
        raise ValueError(f'Unbalanced free elastic DOFs: {free_residual}')
    components = basis.split_indices()
    xyz = basis.doflocs[:, components[0]].T
    field = np.array([displacement[c] for c in components]).T
    applied = [float(load[c].sum()) for c in components]
    support_residual = np.zeros_like(residual)
    support_residual[fixed] = residual[fixed]
    free_residual_vector = residual-support_residual
    reaction = [float(support_residual[c].sum()) for c in components]
    applied_moment = np.cross(xyz, np.array([load[c] for c in components]).T).sum(axis=0)
    reaction_moment = np.cross(xyz, np.array([support_residual[c] for c in components]).T).sum(axis=0)
    free_moment = np.cross(xyz, np.array([free_residual_vector[c] for c in components]).T).sum(axis=0)
    return {'displacement': displacement, 'field_xyz_mm': xyz,
            'field_displacement_mm': field,
            'report': {
                'scalar_nodes': len(field), 'vector_dofs': int(basis.N),
                'constrained_dofs': len(fixed),
                'maximum_displacement_mm': float(np.linalg.norm(field, axis=1).max()),
                'minimum_displacement_components_mm': field.min(axis=0).tolist(),
                'maximum_displacement_components_mm': field.max(axis=0).tolist(),
                'free_residual_inf_N': free_residual,
                'applied_force_N': applied, 'support_reaction_N': reaction,
                'force_balance_N': (np.array(applied)+reaction).tolist(),
                'applied_moment_about_origin_N_mm': applied_moment.tolist(),
                'support_moment_about_origin_N_mm': reaction_moment.tolist(),
                'moment_balance_N_mm': (applied_moment+reaction_moment).tolist(),
                'free_residual_resultant_N': [float(free_residual_vector[c].sum()) for c in components],
                'free_residual_moment_N_mm': free_moment.tolist(),
                'strain_energy_N_mm': float(.5*displacement@(stiffness@displacement)),
                'load_work_N_mm': float(displacement@load),
                'physical_supports_qualified': False,
                'material_qualified': False,
                'scope': 'Isotropic linear elasticity with declared ideal supports; '
                         'not a unilateral bearing or manufactured-material certificate.'}}


def strain_stress_screen(basis, displacement, E_MPa, poisson):
    """Quadrature stress/strain diagnostics, without a strength allowable.

    Peaks at ideal support/contact boundaries are mesh dependent; they cannot
    be reported as a qualified structural safety factor.
    """
    gradient = basis.interpolate(displacement).grad
    strain = .5*(gradient+gradient.swapaxes(0, 1))
    trace = np.einsum('ii...->...', strain)
    lam, mu = lame_parameters(E_MPa, poisson)
    stress = 2*mu*strain+lam*np.eye(3)[:, :, None, None]*trace
    hydro = np.einsum('ii...->...', stress)/3
    dev = stress-np.eye(3)[:, :, None, None]*hydro
    mises = np.sqrt(1.5*np.einsum('ij...,ij...->...', dev, dev))
    strain_norm = np.sqrt(np.einsum('ij...,ij...->...', strain, strain))
    return {'maximum_quadrature_strain_norm': float(strain_norm.max()),
            'maximum_quadrature_von_mises_MPa': float(mises.max()),
            'strength_allowable_supplied': False,
            'scope': 'Linear isotropic quadrature diagnostics; support/contact '
                     'peaks are mesh dependent, no safety factor or print qualification.'}

#!/usr/bin/env python3
"""
2019-05-07 13:21:02
@author: Paul Reiter
"""
import numpy as np
import pytest
from pybem import __version__
from pybem import Mesh
from pybem.pybem import (
    complex_system_matrix,
    calc_scattered_pressure_at,
)
from pybem.helmholtz import (
    g_2d,
    admitant_2d_integral,
    kirchhoff_helmholtz_solver,
    burton_miller_solver,
    vector_h_2d,
)


def test_version():
    assert __version__ == '0.3.0'


def test_complex_system_matrix():
    mesh = Mesh([[0, 0], [1, 0], [1, 2]], [[0, 1], [1, 2]])

    # def integral_function(k, r, admittance, n, corners, singular):
    def integral_function(k, mesh, row_idx, col_idx):
        return (mesh.centers[row_idx][0] + 1j*mesh.centers[row_idx][1]
                + (row_idx == col_idx))

    reference_system_matrix = np.array([[1.5, .5], [1 + 1j, 2 + 1j]],
                                       dtype=complex)
    system_matrix = complex_system_matrix(mesh, integral_function, 1)
    np.testing.assert_allclose(reference_system_matrix, system_matrix)


def test_calc_scattered_pressure_at():
    # point source above fully reflective plane
    n = 200
    mesh = Mesh([(x, 0) for x in np.linspace(10, -10, n+1)],
                [(i, i+1) for i in range(n)])
    k, rho, c = 2*np.pi*300/343, 1, 343
    surface_pressure = 2*np.array([g_2d(k, point, np.array([0., 1.]))
                                   for point in mesh.centers], dtype=complex)
    solution = calc_scattered_pressure_at(mesh, admitant_2d_integral, k,
                                          surface_pressure,
                                          np.array([[0., .5]]), rho, c)
    np.testing.assert_allclose(g_2d(k, np.array([0., .5]),
                                    np.array([0., -1.])),
                               solution[0], rtol=1e-3)


@pytest.mark.slow
@pytest.mark.parametrize('solver', [
    kirchhoff_helmholtz_solver,
    burton_miller_solver,
])
def test_calc_scattered_pressure_at_point_source_reflective_plane(solver):
    # actually solve the linear system for point source above reflective plane
    n = 80
    # create admitant mesh
    mesh = Mesh([(x, 0) for x in np.linspace(6, -6, n+1)],
                [(i, i+1) for i in range(n)])
    k, rho, c = 2*np.pi*300/343, 1, 343
    p_incoming = np.array([g_2d(k, point, np.array([0., 1.]))
                           for point in mesh.centers], dtype=complex)
    grad_p_incoming = np.array([vector_h_2d(k, point, np.array([0., 1.]))
                               for point in mesh.centers], dtype=complex)
    surface_pressure = solver(mesh, p_incoming, grad_p_incoming, k, rho, c)
    solution = calc_scattered_pressure_at(mesh, admitant_2d_integral, k,
                                          surface_pressure,
                                          np.array([[0., .5]]), rho, c)
    np.testing.assert_allclose(g_2d(k, np.array([0., .5]),
                                    np.array([0., -1.])),
                               solution[0], rtol=1e-2)


@pytest.mark.slow
@pytest.mark.parametrize('solver', [
    kirchhoff_helmholtz_solver,
    burton_miller_solver,
])
def test_calc_reflection_of_fully_absorbing_plane_for_plane_wave(solver):
    # plane wave impinging normally on admittance plane
    n = 180
    # create admitant mesh
    k, rho, c = 2*np.pi*300/343, 1, 343
    mesh = Mesh([(x, 0) for x in np.linspace(9, -9, n+1)],
                [(i, i+1) for i in range(n)], [1/343. for _ in range(n)])
    p_incoming = np.array([np.exp(1j*k*point[1])
                           for point in mesh.centers], dtype=complex)
    grad_p_incoming = np.array([[1j*k*np.exp(1j*k*point[1]), 0]
                                for point in mesh.centers],
                               dtype=complex)
    surface_pressure = solver(mesh, p_incoming, grad_p_incoming, k, rho, c)
    solution = calc_scattered_pressure_at(mesh, admitant_2d_integral, k,
                                          surface_pressure,
                                          np.array([[0., .5]]), rho, c)
    np.testing.assert_allclose(0+1, solution[0]+1, rtol=1e-2)

import numpy as np

from .cphf import CPHF
from .operators import Operator

from .explicit_equations_partial import \
    (form_rpa_a_matrix_mo_singlet_partial,
     form_rpa_a_matrix_mo_singlet_ss_partial,
     form_rpa_a_matrix_mo_singlet_os_partial,
     form_rpa_a_matrix_mo_triplet_partial,
     form_rpa_b_matrix_mo_singlet_partial,
     form_rpa_b_matrix_mo_singlet_ss_partial,
     form_rpa_b_matrix_mo_singlet_os_partial,
     form_rpa_b_matrix_mo_triplet_partial)

from .test_uhf import ref_water_cation_UHF_HF_STO3G


def test_explicit_uhf_outside_solver():
    from pyscf import ao2mo, gto, scf

    mol = gto.Mole()
    mol.verbose = 5
    with open('water.xyz') as fh:
        mol.atom = fh.read()
    mol.unit = 'Bohr'
    mol.basis = 'sto-3g'
    mol.symmetry = False

    mol.charge = 1
    mol.spin = 1

    mol.build()

    mf = scf.UHF(mol)
    mf.kernel()
    C_a = mf.mo_coeff[0, ...]
    C_b = mf.mo_coeff[1, ...]
    E_a = np.diag(mf.mo_energy[0, ...])
    E_b = np.diag(mf.mo_energy[1, ...])
    assert C_a.shape == C_b.shape
    assert E_a.shape == E_b.shape
    norb = C_a.shape[1]
    nocc_a, nocc_b = mol.nelec
    nvirt_a, nvirt_b = norb - nocc_a, norb - nocc_b
    occupations = [nocc_a, nvirt_a, nocc_b, nvirt_b]

    C_occ_alph = C_a[:, :nocc_a]
    C_virt_alph = C_a[:, nocc_a:]
    C_occ_beta = C_b[:, :nocc_b]
    C_virt_beta = C_b[:, nocc_b:]
    C_ovov_aaaa = (C_occ_alph, C_virt_alph, C_occ_alph, C_virt_alph)
    C_ovov_aabb = (C_occ_alph, C_virt_alph, C_occ_beta, C_virt_beta)
    C_ovov_bbaa = (C_occ_beta, C_virt_beta, C_occ_alph, C_virt_alph)
    C_ovov_bbbb = (C_occ_beta, C_virt_beta, C_occ_beta, C_virt_beta)
    C_oovv_aaaa = (C_occ_alph, C_occ_alph, C_virt_alph, C_virt_alph)
    C_oovv_bbbb = (C_occ_beta, C_occ_beta, C_virt_beta, C_virt_beta)
    tei_mo_ovov_aaaa = ao2mo.general(mol, C_ovov_aaaa, aosym='s4', compact=False, verbose=5).reshape(nocc_a, nvirt_a, nocc_a, nvirt_a)
    tei_mo_ovov_aabb = ao2mo.general(mol, C_ovov_aabb, aosym='s4', compact=False, verbose=5).reshape(nocc_a, nvirt_a, nocc_b, nvirt_b)
    tei_mo_ovov_bbaa = ao2mo.general(mol, C_ovov_bbaa, aosym='s4', compact=False, verbose=5).reshape(nocc_b, nvirt_b, nocc_a, nvirt_a)
    tei_mo_ovov_bbbb = ao2mo.general(mol, C_ovov_bbbb, aosym='s4', compact=False, verbose=5).reshape(nocc_b, nvirt_b, nocc_b, nvirt_b)
    tei_mo_oovv_aaaa = ao2mo.general(mol, C_oovv_aaaa, aosym='s4', compact=False, verbose=5).reshape(nocc_a, nocc_a, nvirt_a, nvirt_a)
    tei_mo_oovv_bbbb = ao2mo.general(mol, C_oovv_bbbb, aosym='s4', compact=False, verbose=5).reshape(nocc_b, nocc_b, nvirt_b, nvirt_b)

    A_s_ss_a = form_rpa_a_matrix_mo_singlet_ss_partial(E_a, tei_mo_ovov_aaaa, tei_mo_oovv_aaaa)
    A_s_os_a = form_rpa_a_matrix_mo_singlet_os_partial(tei_mo_ovov_aabb)
    B_s_ss_a = form_rpa_b_matrix_mo_singlet_ss_partial(tei_mo_ovov_aaaa)
    B_s_os_a = form_rpa_b_matrix_mo_singlet_os_partial(tei_mo_ovov_aabb)
    A_s_ss_b = form_rpa_a_matrix_mo_singlet_ss_partial(E_b, tei_mo_ovov_bbbb, tei_mo_oovv_bbbb)
    A_s_os_b = form_rpa_a_matrix_mo_singlet_os_partial(tei_mo_ovov_bbaa)
    B_s_ss_b = form_rpa_b_matrix_mo_singlet_ss_partial(tei_mo_ovov_bbbb)
    B_s_os_b = form_rpa_b_matrix_mo_singlet_os_partial(tei_mo_ovov_bbaa)
    # Since the "triplet" part contains no Coulomb contribution, and
    # (xx|yy) is only in the Coulomb part, there is no ss/os
    # separation for the triplet part.

    G_aa = np.asarray(np.bmat([[A_s_ss_a, B_s_ss_a],
                               [B_s_ss_a, A_s_ss_a]]))
    G_bb = np.asarray(np.bmat([[A_s_ss_b, B_s_ss_b],
                               [B_s_ss_b, A_s_ss_b]]))
    G_ab = np.asarray(np.bmat([[A_s_os_a, B_s_os_a],
                               [B_s_os_a, A_s_os_a]]))
    G_ba = np.asarray(np.bmat([[A_s_os_b, B_s_os_b],
                               [B_s_os_b, A_s_os_b]]))

    G_aa_inv = np.linalg.inv(G_aa)
    G_bb_inv = np.linalg.inv(G_bb)

    nov_aa = nocc_a * nvirt_a
    nov_bb = nocc_b * nvirt_b

    assert G_aa_inv.shape == (2 * nov_aa, 2 * nov_aa)
    assert G_bb_inv.shape == (2 * nov_bb, 2 * nov_bb)

    # Form the operator-independent part of the response vectors.
    left_a = np.linalg.inv(G_aa - np.dot(G_ab, np.dot(G_bb_inv, G_ba)))
    left_b = np.linalg.inv(G_bb - np.dot(G_ba, np.dot(G_aa_inv, G_ab)))

    integrals_dipole_ao = mol.intor('cint1e_r_sph', comp=3)

    integrals_dipole_mo_ai_a = []
    integrals_dipole_mo_ai_b = []

    for comp in range(3):

        integrals_dipole_mo_ai_comp_a = np.dot(C_a[:, nocc_a:].T, np.dot(integrals_dipole_ao[comp, ...], C_a[:, :nocc_a]))
        integrals_dipole_mo_ai_comp_b = np.dot(C_b[:, nocc_b:].T, np.dot(integrals_dipole_ao[comp, ...], C_b[:, :nocc_b]))

        integrals_dipole_mo_ai_comp_a = np.reshape(integrals_dipole_mo_ai_comp_a, -1, order='F')
        integrals_dipole_mo_ai_comp_b = np.reshape(integrals_dipole_mo_ai_comp_b, -1, order='F')

        integrals_dipole_mo_ai_a.append(integrals_dipole_mo_ai_comp_a)
        integrals_dipole_mo_ai_b.append(integrals_dipole_mo_ai_comp_b)

    integrals_dipole_mo_ai_a = np.stack(integrals_dipole_mo_ai_a, axis=0).T
    integrals_dipole_mo_ai_b = np.stack(integrals_dipole_mo_ai_b, axis=0).T

    integrals_dipole_mo_ai_a_super = np.concatenate((integrals_dipole_mo_ai_a, integrals_dipole_mo_ai_a), axis=0)
    integrals_dipole_mo_ai_b_super = np.concatenate((integrals_dipole_mo_ai_b, integrals_dipole_mo_ai_b), axis=0)

    # Form the operator-dependent part of the response vectors.
    right_a = integrals_dipole_mo_ai_a_super - (np.dot(G_ab, np.dot(G_bb_inv, integrals_dipole_mo_ai_b_super)))
    right_b = integrals_dipole_mo_ai_b_super - (np.dot(G_ba, np.dot(G_aa_inv, integrals_dipole_mo_ai_a_super)))

    # The total response vector for each spin is the product of the
    # operator-independent (left) and operator-dependent (right)
    # parts.
    rspvec_a = np.dot(left_a, right_a)
    rspvec_b = np.dot(left_b, right_b)

    res_a = np.dot(integrals_dipole_mo_ai_a_super.T, rspvec_a) / 2
    res_b = np.dot(integrals_dipole_mo_ai_b_super.T, rspvec_b) / 2
    res_u = 2 * (res_a + res_b)
    print(res_u)

    atol = 1.0e-5
    rtol = 0.0

    np.testing.assert_allclose(res_u, ref_water_cation_UHF_HF_STO3G, rtol=rtol, atol=atol)

    return


def test_explicit_uhf():
    from pyscf import ao2mo, gto, scf

    mol = gto.Mole()
    mol.verbose = 5
    with open('water.xyz') as fh:
        mol.atom = fh.read()
    mol.unit = 'Bohr'
    mol.basis = 'sto-3g'
    mol.symmetry = False

    mol.charge = 1
    mol.spin = 1

    mol.build()

    mf = scf.UHF(mol)
    mf.kernel()
    C = mf.mo_coeff
    C_a = C[0, ...]
    C_b = C[1, ...]
    E_a = np.diag(mf.mo_energy[0, ...])
    E_b = np.diag(mf.mo_energy[1, ...])
    assert C_a.shape == C_b.shape
    assert E_a.shape == E_b.shape
    E = np.stack((E_a, E_b), axis=0)
    norb = C_a.shape[1]
    nocc_a, nocc_b = mol.nelec
    nvirt_a, nvirt_b = norb - nocc_a, norb - nocc_b
    occupations = [nocc_a, nvirt_a, nocc_b, nvirt_b]

    C_occ_alph = C_a[:, :nocc_a]
    C_virt_alph = C_a[:, nocc_a:]
    C_occ_beta = C_b[:, :nocc_b]
    C_virt_beta = C_b[:, nocc_b:]
    C_ovov_aaaa = (C_occ_alph, C_virt_alph, C_occ_alph, C_virt_alph)
    C_ovov_aabb = (C_occ_alph, C_virt_alph, C_occ_beta, C_virt_beta)
    C_ovov_bbaa = (C_occ_beta, C_virt_beta, C_occ_alph, C_virt_alph)
    C_ovov_bbbb = (C_occ_beta, C_virt_beta, C_occ_beta, C_virt_beta)
    C_oovv_aaaa = (C_occ_alph, C_occ_alph, C_virt_alph, C_virt_alph)
    C_oovv_bbbb = (C_occ_beta, C_occ_beta, C_virt_beta, C_virt_beta)
    tei_mo_ovov_aaaa = ao2mo.general(mol, C_ovov_aaaa, aosym='s4', compact=False, verbose=5).reshape(nocc_a, nvirt_a, nocc_a, nvirt_a)
    tei_mo_ovov_aabb = ao2mo.general(mol, C_ovov_aabb, aosym='s4', compact=False, verbose=5).reshape(nocc_a, nvirt_a, nocc_b, nvirt_b)
    tei_mo_ovov_bbaa = ao2mo.general(mol, C_ovov_bbaa, aosym='s4', compact=False, verbose=5).reshape(nocc_b, nvirt_b, nocc_a, nvirt_a)
    tei_mo_ovov_bbbb = ao2mo.general(mol, C_ovov_bbbb, aosym='s4', compact=False, verbose=5).reshape(nocc_b, nvirt_b, nocc_b, nvirt_b)
    tei_mo_oovv_aaaa = ao2mo.general(mol, C_oovv_aaaa, aosym='s4', compact=False, verbose=5).reshape(nocc_a, nocc_a, nvirt_a, nvirt_a)
    tei_mo_oovv_bbbb = ao2mo.general(mol, C_oovv_bbbb, aosym='s4', compact=False, verbose=5).reshape(nocc_b, nocc_b, nvirt_b, nvirt_b)

    integrals_dipole_ao = mol.intor('cint1e_r_sph', comp=3)

    cphf = CPHF(C, E, occupations)

    cphf.tei_mo = (tei_mo_ovov_aaaa, tei_mo_ovov_aabb, tei_mo_ovov_bbaa, tei_mo_ovov_bbbb, tei_mo_oovv_aaaa, tei_mo_oovv_bbbb)
    cphf.tei_mo_type = 'partial'

    operator_dipole = Operator(label='dipole', is_imaginary=False, is_spin_dependent=False)
    operator_dipole.ao_integrals = integrals_dipole_ao
    cphf.add_operator(operator_dipole)

    cphf.set_frequencies()

    cphf.run(solver='explicit', hamiltonian='rpa', spin='singlet')
    assert len(cphf.frequencies) == len(cphf.results) == 1
    res = cphf.results[0]
    print(res)

    atol = 1.0e-5
    rtol = 0.0

    np.testing.assert_allclose(res, ref_water_cation_UHF_HF_STO3G, rtol=rtol, atol=atol)

    return


if __name__ == '__main__':
    pass
    # test_explicit_uhf_outside_solver()

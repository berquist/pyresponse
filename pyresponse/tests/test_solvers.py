import numpy as np
import scipy as sp

import psi4
import pyscf

from pyresponse import cphf, solvers, utils
from pyresponse.core import Hamiltonian, Program, Spin
from pyresponse.properties import electric, magnetic
from pyresponse.psi4 import molecules as molecules_psi4
from pyresponse.psi4.utils import (
    mocoeffs_from_psi4wfn,
    moenergies_from_psi4wfn,
    occupations_from_psi4wfn,
)
from pyresponse.pyscf import molecules as molecules_pyscf
from pyresponse.pyscf.utils import occupations_from_pyscf_mol


def test_inversion() -> None:
    """Test that each kind of inversion function gives identical results."""

    mol = molecules_pyscf.molecule_glycine_sto3g()
    mol.charge = 1
    mol.spin = 1
    mol.build()

    mf = pyscf.scf.uhf.UHF(mol)
    mf.scf()

    assert isinstance(mf.mo_coeff, np.ndarray)
    assert len(mf.mo_coeff) == 2
    C = utils.fix_mocoeffs_shape(mf.mo_coeff)
    E = utils.fix_moenergies_shape(mf.mo_energy)
    occupations = occupations_from_pyscf_mol(mol, C)

    calculator_ref = magnetic.Magnetizability(
        Program.PySCF,
        mol,
        cphf.CPHF(solvers.ExactInv(C, E, occupations)),
        C,
        E,
        occupations,
    )
    calculator_ref.form_operators()
    calculator_ref.run(hamiltonian=Hamiltonian.RPA, spin=Spin.singlet)
    calculator_ref.form_results()

    inv_funcs = (sp.linalg.inv, sp.linalg.pinv, sp.linalg.pinv2)

    thresh = 6.0e-14

    for inv_func in inv_funcs:
        calculator_res = magnetic.Magnetizability(
            Program.PySCF,
            mol,
            cphf.CPHF(solvers.ExactInv(C, E, occupations)),
            C,
            E,
            occupations,
        )
        calculator_res.form_operators()
        calculator_res.run(hamiltonian=Hamiltonian.RPA, spin=Spin.singlet)
        calculator_res.form_results()

        np.testing.assert_equal(
            np.sign(calculator_ref.magnetizability),
            np.sign(calculator_res.magnetizability),
        )
        diff = calculator_ref.magnetizability - calculator_res.magnetizability
        abs_diff = np.abs(diff)
        print(abs_diff)
        assert np.all(abs_diff < thresh)


def test_final_result_rhf_h2o_sto3g_rpa_singlet_iter() -> None:
    mol = molecules_psi4.molecule_glycine_sto3g()
    psi4.core.set_active_molecule(mol)
    _, wfn = psi4.energy("hf", return_wfn=True)
    C = mocoeffs_from_psi4wfn(wfn)
    E = moenergies_from_psi4wfn(wfn)
    occupations = occupations_from_psi4wfn(wfn)

    polarizability = electric.Polarizability(
        Program.Psi4,
        mol,
        cphf.CPHF(solvers.ExactInv(C, E, occupations)),
        C,
        E,
        occupations,
    )
    polarizability.form_operators()
    polarizability.run(hamiltonian=Hamiltonian.RPA, spin=Spin.singlet)
    polarizability.form_results()


if __name__ == "__main__":
    # test_inversion()
    test_final_result_rhf_h2o_sto3g_rpa_singlet_iter()
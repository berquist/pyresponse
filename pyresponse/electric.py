"""Wrapper for performing a dipole polarizability calculation."""

from pyresponse.interfaces import Program
from pyresponse.molecular_property import ResponseProperty
from pyresponse.operators import Operator


class Polarizability(ResponseProperty):
    """Wrapper for performing a dipole polarizability calculation."""

    def __init__(
        self,
        program,
        program_obj,
        mocoeffs,
        moenergies,
        occupations,
        frequencies,
        *args,
        **kwargs
    ):
        super().__init__(
            program,
            program_obj,
            mocoeffs,
            moenergies,
            occupations,
            frequencies,
            *args,
            **kwargs
        )

    def form_operators(self):

        if self.program == Program.PySCF:
            from pyresponse.pyscf import integrals

            integral_generator = integrals.IntegralsPyscf(self.program_obj)
        elif self.program == Program.Psi4:
            from pyresponse.psi4 import integrals

            integral_generator = integrals.IntegralsPsi4(self.program_obj)
        else:
            raise RuntimeError

        operator_diplen = Operator(
            label="dipole", is_imaginary=False, is_spin_dependent=False, triplet=False
        )
        operator_diplen.ao_integrals = integral_generator.integrals(integrals.DIPOLE)
        self.driver.add_operator(operator_diplen)

    def form_results(self):

        assert len(self.driver.results) == len(self.frequencies)
        self.polarizabilities = []
        for idxf, frequency in enumerate(self.frequencies):
            results = self.driver.results[idxf]
            assert results.shape == (3, 3)
            self.polarizabilities.append(results)

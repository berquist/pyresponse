from __future__ import print_function
from __future__ import division

from .molecular_property import ResponseProperty
from .operators import Operator


class Polarizability(ResponseProperty):

    def __init__(self, pyscfmol, mocoeffs, moenergies, occupations, hamiltonian, spin, frequencies, *args, **kwargs):
        super().__init__(pyscfmol, mocoeffs, moenergies, occupations, hamiltonian, spin, frequencies, *args, **kwargs)


    def form_operators(self):

        operator_diplen = Operator(label='dipole', is_imaginary=False, is_spin_dependent=False, triplet=False)
        integrals_diplen_ao = self.pyscfmol.intor('cint1e_r_sph', comp=3)
        operator_diplen.ao_integrals = integrals_diplen_ao
        self.solver.add_operator(operator_diplen)


    def form_results(self):

        assert len(self.solver.results) == len(self.frequencies)
        self.polarizabilities = []
        for idxf, frequency in enumerate(self.frequencies):
            # print('=' * 78)
            results = self.solver.results[idxf]
            assert results.shape == (3, 3)
            # print('frequency')
            # print(frequency)
            self.polarizabilities.append(results)

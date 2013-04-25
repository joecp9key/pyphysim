#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for the modules in the ia package.

Each module has several doctests that we run in addition to the unittests
defined here.
"""

__revision__ = "$Revision$"

# xxxxxxxxxx Add the parent folder to the python path. xxxxxxxxxxxxxxxxxxxx
import sys
import os
parent_dir = os.path.split(os.path.abspath(os.path.dirname(__file__)))[0]
sys.path.append(parent_dir)
# xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

import unittest
import doctest
import numpy as np

import ia  # Import the package ia
from ia.ia import AlternatingMinIASolver, IASolverBaseClass, MaxSinrIASolverIASolver
from util.misc import peig, leig, randn_c


# UPDATE THIS CLASS if another module is added to the ia package
class IaDoctestsTestCase(unittest.TestCase):
    """Teste case that run all the doctests in the modules of the ia
    package."""

    def test_ia(self):
        """Run doctests in the ia module."""
        doctest.testmod(ia)


# xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
# xxxxxxxxxx IA Module xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
# xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
class IASolverBaseClassTestCase(unittest.TestCase):
    def setUp(self):
        """Called before each test."""
        self.iasolver = IASolverBaseClass()

    def test_properties(self):
        K = 3
        Nr = np.array([2, 4, 6])
        Nt = np.array([2, 3, 5])
        Ns = np.array([1, 2, 3])
        self.iasolver.randomizeH(Nr, Nt, K)
        self.iasolver.randomizeF(Nt, Ns, K)

        # Test the properties
        self.assertEqual(self.iasolver.K, K)
        np.testing.assert_array_equal(self.iasolver.Nr, Nr)
        np.testing.assert_array_equal(self.iasolver.Nt, Nt)
        np.testing.assert_array_equal(self.iasolver.Ns, Ns)

    def test_randomizeF(self):
        K = 3
        Nt = np.array([2, 3, 5])
        Ns = np.array([1, 2, 3])
        self.iasolver.randomizeF(Nt, Ns, K)

        # The shape of the precoder is the number of users
        self.assertEqual(self.iasolver.F.shape, (K,))

        # The shape of the precoder of each user is Nt[user] x Ns[user]
        self.assertEqual(self.iasolver.F[0].shape, (Nt[0], Ns[0]))
        self.assertEqual(self.iasolver.F[1].shape, (Nt[1], Ns[1]))
        self.assertEqual(self.iasolver.F[2].shape, (Nt[2], Ns[2]))

        # Test if the generated precoder of each user has a Frobenius norm
        # equal to one.
        self.assertAlmostEqual(np.linalg.norm(self.iasolver.F[0], 'fro'), 1.)
        self.assertAlmostEqual(np.linalg.norm(self.iasolver.F[1], 'fro'), 1.)
        self.assertAlmostEqual(np.linalg.norm(self.iasolver.F[2], 'fro'), 1.)

        # Test when the number of streams and transmit antennas is an
        # scalar (the same value will be used for all users)
        Nt = 3
        Ns = 2
        self.iasolver.randomizeF(Nt, Ns, K)
        # The shape of the precoder of each user is Nt[user] x Ns[user]
        self.assertEqual(self.iasolver.F[0].shape, (Nt, Ns))
        self.assertEqual(self.iasolver.F[1].shape, (Nt, Ns))
        self.assertEqual(self.iasolver.F[2].shape, (Nt, Ns))

    def test_calc_Q(self):
        K = 3
        Nt = np.array([2, 2, 2])
        Nr = np.array([2, 2, 2])
        Ns = np.array([1, 1, 1])

        # Transmit power of all users
        P = np.array([1.2, 1.5, 0.9])

        self.iasolver.randomizeF(Nt, Ns, K)
        self.iasolver.randomizeH(Nr, Nt, K)

        # xxxxx Calculate the expected Q[0] after one step xxxxxxxxxxxxxxxx
        k = 0
        H01_F1 = np.dot(
            self.iasolver.get_channel(k, 1),
            self.iasolver.F[1]
        )
        H02_F2 = np.dot(
            self.iasolver.get_channel(k, 2),
            self.iasolver.F[2]
        )
        expected_Q0 = np.dot(P[1] * H01_F1,
                             H01_F1.transpose().conjugate()) + \
                      np.dot(P[2] * H02_F2,
                             H02_F2.transpose().conjugate())

        Qk = self.iasolver.calc_Q(k, P)
        # Test if Qk is equal to the expected output
        np.testing.assert_array_almost_equal(Qk, expected_Q0)
        # xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

        # xxxxx Calculate the expected Q[1] after one step xxxxxxxxxxxxxxxx
        k = 1
        H10_F0 = np.dot(
            self.iasolver.get_channel(k, 0),
            self.iasolver.F[0]
        )
        H12_F2 = np.dot(
            self.iasolver.get_channel(k, 2),
            self.iasolver.F[2]
        )
        expected_Q1 = np.dot(P[0] * H10_F0,
                             H10_F0.transpose().conjugate()) + \
                      np.dot(P[2] * H12_F2,
                             H12_F2.transpose().conjugate())

        Qk = self.iasolver.calc_Q(k, P)
        # Test if Qk is equal to the expected output
        np.testing.assert_array_almost_equal(Qk, expected_Q1)
        # xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

        # xxxxx Calculate the expected Q[2] after one step xxxxxxxxxxxxxxxx
        k = 2
        H20_F0 = np.dot(
            self.iasolver.get_channel(k, 0),
            self.iasolver.F[0]
        )
        H21_F1 = np.dot(
            self.iasolver.get_channel(k, 1),
            self.iasolver.F[1]
        )
        expected_Q2 = np.dot(P[0] * H20_F0,
                             H20_F0.transpose().conjugate()) + \
                      np.dot(P[1] * H21_F1,
                             H21_F1.transpose().conjugate())

        Qk = self.iasolver.calc_Q(k, P)
        # Test if Qk is equal to the expected output
        np.testing.assert_array_almost_equal(Qk, expected_Q2)
        # xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

    def test_solve(self):
        with self.assertRaises(NotImplementedError):
            self.iasolver.solve()


class AlternatingMinIASolverTestCase(unittest.TestCase):
    """Unittests for the AlternatingMinIASolver class in the ia module."""
    def setUp(self):
        """Called before each test."""
        self.alt = AlternatingMinIASolver()

    def test_updateC(self):
        K = 3
        Nr = np.array([2, 4, 6])
        Nt = np.array([2, 3, 5])
        Ns = np.array([1, 2, 3])
        # We only need to initialize a random channel here for this test
        # and "self.alt.randomizeH(Nr, Nt, K)" would be simpler. However,
        # in order to call the init_from_channel_matrix at least once in
        # these tests we are using it here.
        self.alt.init_from_channel_matrix(
            randn_c(np.sum(Nr), np.sum(Nt)),
            Nr,
            Nt,
            K)
        self.alt.randomizeF(Nt, Ns, K)

        # Dimensions of the interference subspace
        Ni = Nr - Ns

        self.alt.updateC()

        # xxxxx Calculate the expected C[0] after one step xxxxxxxxxxxxxxxx
        k = 0
        H01_F1 = np.dot(
            self.alt.get_channel(k, 1),
            self.alt.F[1]
        )
        H02_F2 = np.dot(
            self.alt.get_channel(k, 2),
            self.alt.F[2]
        )
        expected_C0 = np.dot(H01_F1, H01_F1.transpose().conjugate()) + \
                      np.dot(H02_F2, H02_F2.transpose().conjugate())
        expected_C0 = peig(expected_C0, Ni[k])[0]

        # Test if C[0] is equal to the expected output
        np.testing.assert_array_almost_equal(self.alt.C[0], expected_C0)
        # xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

        # xxxxx Calculate the expected C[1] after one step xxxxxxxxxxxxxxxx
        k = 1
        H10_F0 = np.dot(
            self.alt.get_channel(k, 0),
            self.alt.F[0]
        )
        H12_F2 = np.dot(
            self.alt.get_channel(k, 2),
            self.alt.F[2]
        )
        expected_C1 = np.dot(H10_F0, H10_F0.transpose().conjugate()) + \
                      np.dot(H12_F2, H12_F2.transpose().conjugate())
        expected_C1 = peig(expected_C1, Ni[k])[0]

        # Test if C[1] is equal to the expected output
        np.testing.assert_array_almost_equal(self.alt.C[1], expected_C1)
        # xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

        # xxxxx Calculate the expected C[2] after one step xxxxxxxxxxxxxxxx
        k = 2
        H20_F0 = np.dot(
            self.alt.get_channel(k, 0),
            self.alt.F[0]
        )
        H21_F1 = np.dot(
            self.alt.get_channel(k, 1),
            self.alt.F[1]
        )
        expected_C2 = np.dot(H20_F0, H20_F0.transpose().conjugate()) + \
                      np.dot(H21_F1, H21_F1.transpose().conjugate())
        expected_C2 = peig(expected_C2, Ni[k])[0]

        # Test if C[2] is equal to the expected output
        np.testing.assert_array_almost_equal(self.alt.C[2], expected_C2)
        # xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

    def test_updateF(self):
        K = 3
        Nr = np.array([2, 4, 6])
        Nt = np.array([2, 3, 5])
        Ns = np.array([1, 2, 3])
        self.alt.randomizeH(Nr, Nt, K)
        self.alt.randomizeF(Nt, Ns, K)

        self.alt.updateC()
        self.alt.updateF()

        # xxxxxxxxxx Aliases for each channel xxxxxxxxxxxxxxxxxxxxxxxxxxxxx
        H01 = self.alt.get_channel(0, 1)
        H02 = self.alt.get_channel(0, 2)

        H10 = self.alt.get_channel(1, 0)
        H12 = self.alt.get_channel(1, 2)

        H20 = self.alt.get_channel(2, 0)
        H21 = self.alt.get_channel(2, 1)
        # xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

        # xxxxxxxxxx Aliases for (I-Ck Ck^H)) for each k xxxxxxxxxxxxxxxxxx
        Y0 = np.eye(Nr[0], dtype=complex) - \
             np.dot(
                 self.alt.C[0],
                 self.alt.C[0].conjugate().transpose())

        Y1 = np.eye(Nr[1], dtype=complex) - \
             np.dot(
                 self.alt.C[1],
                 self.alt.C[1].conjugate().transpose())

        Y2 = np.eye(Nr[2], dtype=complex) - \
             np.dot(
                 self.alt.C[2],
                 self.alt.C[2].conjugate().transpose())
        # xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

        # xxxxx Calculate the expected F[0] after one step xxxxxxxxxxxxxxxx
        # l = 0 -> k = 1 and k = 2
        expected_F0 = np.dot(np.dot(H10.conjugate().transpose(), Y1), H10) + \
                      np.dot(np.dot(H20.conjugate().transpose(), Y2), H20)
        expected_F0 = leig(expected_F0, Ns[0])[0]
        # xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

        # xxxxx Calculate the expected F[1] after one step xxxxxxxxxxxxxxxx
        # l = 1 -> k = 0 and k = 2
        expected_F1 = np.dot(np.dot(H01.conjugate().transpose(), Y0), H01) + \
                      np.dot(np.dot(H21.conjugate().transpose(), Y2), H21)
        expected_F1 = leig(expected_F1, Ns[1])[0]
        # xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

        # xxxxx Calculate the expected F[1] after one step xxxxxxxxxxxxxxxx
        # l = 2 -> k = 0 and k = 1
        expected_F2 = np.dot(np.dot(H02.conjugate().transpose(), Y0), H02) + \
                      np.dot(np.dot(H12.conjugate().transpose(), Y1), H12)
        expected_F2 = leig(expected_F2, Ns[2])[0]
        # xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

        # xxxxxxxxxx Finally perform the tests xxxxxxxxxxxxxxxxxxxxxxxxxxxx
        np.testing.assert_array_almost_equal(self.alt.F[0], expected_F0)
        np.testing.assert_array_almost_equal(self.alt.F[1], expected_F1)
        np.testing.assert_array_almost_equal(self.alt.F[2], expected_F2)

    def test_updateW(self):
        K = 3
        Nr = np.array([2, 4, 6])
        Nt = np.array([2, 3, 5])
        Ns = np.array([1, 2, 3])
        self.alt.randomizeH(Nr, Nt, K)
        self.alt.randomizeF(Nt, Ns, K)

        # Call updateC, updateF and updateW
        self.alt.step()

        # xxxxx Calculates the expected receive filter for user 0 xxxxxxxxx
        tildeH0 = np.dot(
            self.alt.get_channel(0, 0),
            self.alt.F[0])
        tildeH0 = np.hstack([tildeH0, self.alt.C[0]])
        expected_W0 = np.linalg.inv(tildeH0)[0:self.alt.Ns[0]]
        # xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

        # xxxxx Calculates the expected receive filter for user 1 xxxxxxxxx
        tildeH1 = np.dot(
            self.alt.get_channel(1, 1),
            self.alt.F[1])
        tildeH1 = np.hstack([tildeH1, self.alt.C[1]])
        expected_W1 = np.linalg.inv(tildeH1)[0:self.alt.Ns[1]]
        # xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

        # xxxxx Calculates the expected receive filter for user 2 xxxxxxxxx
        tildeH2 = np.dot(
            self.alt.get_channel(2, 2),
            self.alt.F[2])
        tildeH2 = np.hstack([tildeH2, self.alt.C[2]])
        expected_W2 = np.linalg.inv(tildeH2)[0:self.alt.Ns[2]]
        # xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

        # xxxxxxxxxx Finally perform the tests xxxxxxxxxxxxxxxxxxxxxxxxxxxx
        np.testing.assert_array_almost_equal(self.alt.W[0], expected_W0)
        np.testing.assert_array_almost_equal(self.alt.W[1], expected_W1)
        np.testing.assert_array_almost_equal(self.alt.W[2], expected_W2)

    def test_getCost(self):
        K = 2
        Nr = np.array([3, 3])
        Nt = np.array([3, 3])
        Ns = np.array([2, 2])
        self.alt.randomizeH(Nr, Nt, K)
        self.alt.randomizeF(Nt, Ns, K)

        # Call updateC, updateF and updateW
        self.alt.step()

        Cost = 0
        k, l = (0, 1)
        H01_F1 = np.dot(
            self.alt.get_channel(k, l),
            self.alt.F[l])
        Cost = Cost + np.linalg.norm(
            H01_F1 -
            np.dot(
                np.dot(self.alt.C[k], self.alt.C[k].transpose().conjugate()),
                H01_F1
            ), 'fro') ** 2

        k, l = (1, 0)
        H10_F0 = np.dot(
            self.alt.get_channel(k, l),
            self.alt.F[l])
        Cost = Cost + np.linalg.norm(
            H10_F0 -
            np.dot(
                np.dot(self.alt.C[k], self.alt.C[k].transpose().conjugate()),
                H10_F0
            ), 'fro') ** 2

        self.assertAlmostEqual(self.alt.getCost(), Cost)

    def test_solve(self):
        self.alt.max_iterations = 1
        # We are only testing if this does not thrown an exception. That's
        # why there is no assert clause here
        self.alt.solve()


# TODO: finish implementation
class MaxSinrIASolverIASolverTestCase(unittest.TestCase):
    def setUp(self):
        """Called before each test."""
        self.iasolver = MaxSinrIASolverIASolver()

    def test_calc_Bkl_cov_matrix(self):
        K = 3
        Nt = np.ones(K, dtype=int) * 3
        Nr = np.ones(K, dtype=int) * 3
        Ns = np.ones(K, dtype=int) * 2

        # Transmit power of all users
        P = np.array([1.2, 1.5, 0.9])

        # xxxxx Debug xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
        np.random.seed(42)  # Used in the generation of teh random precoder
        self.iasolver._multiUserChannel.set_channel_seed(324)
        # xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

        self.iasolver.randomizeF(Nt, Ns, K)
        self.iasolver.randomizeH(Nr, Nt, K)

        # Calculates Bkl for all streams (l index) of all users (k index)
        for k in range(K):  # range(K) <-------

            first_part = 0.0  # First part in the equation of Bkl (the double
                              # summation)

            # The outer for loop will calculate
            # first_part = $\sum_{j=1}^{K} \frac{1.0}{Ns[k]} \text{aux}$
            for j in range(K):
                aux = 0.0  # The inner for loop will calculate
                            # $\text{aux} = \sum_{d=1}^{d^{[j]}} \mtH^{[kj]}\mtV_{\star d}^{[j]} \mtV_{\star d}^{[j]\dagger} \mtH^{[kj]\dagger}$
                Hkj = self.iasolver.get_channel(k, j)
                Hkj_H = Hkj.conjugate().transpose()

                for d in range(Ns[k]):
                    Vjd = self.iasolver.F[j][:, d:d + 1]
                    Vjd_H = Vjd.conjugate().transpose()
                    aux = aux + np.dot(np.dot(Hkj, np.dot(Vjd, Vjd_H)), Hkj_H)

                first_part = first_part + (P[j] / Ns[j]) * aux

            np.testing.assert_array_almost_equal(
                first_part,
                self.iasolver._calc_Bkl_cov_matrix_first_part(k, P)
            )

            # xxxxx Calculates the Second Part xxxxxxxxxxxxxxxxxxxxxxxxxxxx
            expected_Bkl = np.empty(Ns[k], dtype=np.ndarray)
            Hkk = self.iasolver.get_channel(k, k)
            Hkk_H = Hkk.transpose().conjugate()
            for l in range(Ns[k]):
                # Calculate the second part in Equation (28). The second part
                # is different for each value of l and is given by
                # second_part = $\frac{1.0}{Ns} \mtH^{[kk]} \mtV_{\star l}^{[k]} \mtV_{\star l}^{[k]\dagger} \mtH^{[kk] \dagger}$
                Vkl = self.iasolver.F[k][:, l:l+1]
                Vkl_H = Vkl.transpose().conjugate()
                second_part = np.dot(Hkk, np.dot(np.dot(Vkl, Vkl_H), Hkk_H))
                second_part = (P[k] / Ns[k]) * second_part
                expected_Bkl[l] = first_part - second_part + np.eye(Nr[k])

                np.testing.assert_array_almost_equal(
                    second_part,
                    self.iasolver._calc_Bkl_cov_matrix_second_part(k, l, P))

            Bkl_all_l = self.iasolver.calc_Bkl_cov_matrix_all_l(k, P)

            np.testing.assert_array_almost_equal(expected_Bkl[0],
                                                 Bkl_all_l[0])
            np.testing.assert_array_almost_equal(expected_Bkl[1],
                                                 Bkl_all_l[1])

    def test_calc_Ukl(self):
        K = 3
        Nt = np.ones(K, dtype=int) * 3
        Nr = np.ones(K, dtype=int) * 3
        Ns = np.ones(K, dtype=int) * 2

        # Transmit power of all users
        P = np.array([1.2, 1.5, 0.9])

        # xxxxx Debug xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
        np.random.seed(42)  # Used in the generation of teh random precoder
        self.iasolver._multiUserChannel.set_channel_seed(324)
        # xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

        self.iasolver.randomizeF(Nt, Ns, K)
        self.iasolver.randomizeH(Nr, Nt, K)

        # xxxxxxxxxx Calculates for k=0 xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
        for k in range(K):
            Hkk = self.iasolver.get_channel(k, k)
            Bkl_all_l = self.iasolver.calc_Bkl_cov_matrix_all_l(k, P)
            for l in range(Ns[k]):
                expected_Ukl = np.dot(
                    np.linalg.inv(Bkl_all_l[l]),
                    np.dot(Hkk, self.iasolver.F[k][:, l:l + 1]))
                expected_Ukl = expected_Ukl / np.linalg.norm(expected_Ukl, 'fro')
                Ukl = self.iasolver.calc_Ukl(Bkl_all_l[l], k, l)
                np.testing.assert_array_almost_equal(expected_Ukl, Ukl)

    def teste_calc_Uk(self):
        K = 3
        Nt = np.ones(K, dtype=int) * 3
        Nr = np.ones(K, dtype=int) * 3
        Ns = np.ones(K, dtype=int) * 2

        # Transmit power of all users
        P = np.array([1.2, 1.5, 0.9])

        # xxxxx Debug xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
        np.random.seed(42)  # Used in the generation of teh random precoder
        self.iasolver._multiUserChannel.set_channel_seed(324)
        # xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

        self.iasolver.randomizeF(Nt, Ns, K)
        self.iasolver.randomizeH(Nr, Nt, K)

        for k in range(K):
            Bkl_all_l = self.iasolver.calc_Bkl_cov_matrix_all_l(k, P)
            expected_Uk = np.empty(Ns[k], dtype=np.ndarray)
            Uk = self.iasolver.calc_Uk(Bkl_all_l, k)

            expected_Uk = np.empty([Nr[k], Ns[k]], dtype=complex)
            for l in range(Ns[k]):
                expected_Uk[:, l] = self.iasolver.calc_Ukl(Bkl_all_l[l], k, l)[:, 0]
            np.testing.assert_array_almost_equal(expected_Uk, Uk)

    def test_calc_SINR_k(self):
        # TODO: Finish implementation
        K = 3
        Nt = np.ones(K, dtype=int) * 3
        Nr = np.ones(K, dtype=int) * 3
        Ns = np.ones(K, dtype=int) * 2

        # Transmit power of all users
        P = np.array([1.2, 1.5, 0.9])

        # xxxxx Debug xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
        np.random.seed(42)  # Used in the generation of teh random precoder
        self.iasolver._multiUserChannel.set_channel_seed(324)
        # xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

        self.iasolver.randomizeF(Nt, Ns, K)
        self.iasolver.randomizeH(Nr, Nt, K)

        for k in range(K):
            print
            Hkk = self.iasolver.get_channel(k, k)
            Bkl_all_l = self.iasolver.calc_Bkl_cov_matrix_all_l(k, P)
            Uk = self.iasolver.calc_Uk(Bkl_all_l, k)

            SINR_k_all_l = self.iasolver.calc_SINR_k(Bkl_all_l, Uk, k, P)

            for l in range(Ns[k]):
                Ukl = Uk[:, l:l + 1]
                Ukl_H = Ukl.transpose().conjugate()
                Vkl = self.iasolver.F[k][:, l:l + 1]
                aux = np.dot(Ukl_H,
                             np.dot(Hkk, Vkl))

                expectedSINRkl = np.asscalar(
                    np.dot(aux, aux.transpose().conjugate()) * (P[k] / Ns[k]) / np.dot(Ukl_H, np.dot(Bkl_all_l[l], Ukl))
                )

                np.testing.assert_array_almost_equal(expectedSINRkl,
                                                     SINR_k_all_l[l])


# xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
if __name__ == "__main__":
    # plot_psd_OFDM_symbols()
    unittest.main()


## Use this if you want to optimize the code on the ia.ia module
# if __name__ == '__main__':
#     import time
#     from misc import pretty_time

#     tic = time.time()

#     K = 4
#     Nr = np.array([5, 5, 5, 5])
#     Nt = np.array([5, 5, 5, 5])
#     Ns = np.array([2, 2, 2, 2])
#     alt = AlternatingMinIASolver()
#     alt.randomizeH(Nr, Nt, K)
#     alt.randomizeF(Nt, Ns, K)

#     maxIter = 5000
#     Cost = np.zeros(maxIter)
#     for i in np.arange(maxIter):
#         alt.step()
#         Cost[i] = alt.getCost()

#     toc = time.time()
#     print pretty_time(toc - tic)

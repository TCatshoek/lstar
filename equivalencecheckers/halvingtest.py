8from itertools import product
from typing import Tuple, Iterable

from equivalencecheckers.equivalencechecker import EquivalenceChecker
from suls.sul import SUL

from scipy.sparse import lil_matrix
import numpy as np

from util.product import product_index, index_product, cumlen

import random

# Equivalence checking based on halving algorithm idea
# We use list of lists sparse matrix for efficiency
# Due to the way scipy implements lil-matrices (slow column slicing),
# S * A^n indexes the rows, and E the columns. (L* does it the opposite way)
# I'd use a csc matrix but those don't support efficiently
# changing the sparsity structure (eg. adding an entry where there wasn't one before)
class HalvingEquivalanceChecker(EquivalenceChecker):
    def __init__(self, sul: SUL, max_depth=5):
        super().__init__(sul)
        self._A = sul.get_alphabet()
        # self._S = S
        # self._E = E
        self.max_depth = max_depth

    def connect(self, S, E):
        self._S = S
        self._E = E

    # Use these getters to make sure we always get the sets in the same sorted order
    def getA(self):
        return list(sorted(self._A))

    def getE(self):
        return list(sorted(self._E))

    def getS(self):
        return list(sorted(self._S))

    def test_equivalence(self, test_sul: SUL) -> Tuple[bool, Iterable]:
        A = self.getA()
        S = self.getS()
        E = self.getE()

        n_cols = len(S) * cumlen(len(A), self.max_depth)
        n_rows = len(E)

        mat = lil_matrix((n_rows, n_cols))

        if hasattr(test_sul, 'cache'):
            # Fill mat with cached entries
            print("TODO: implement filling in cached entries")


        while mat.getnnz() < n_cols * n_rows:

            # Calculate row "interestingness"
            row_counts = mat.getnnz(axis=1) + 1
            row_smallestgroupsize = np.zeros(n_rows)
            for i in range(n_rows):
                unique, count = np.unique(mat[i, :].data[0], return_counts=True)
                row_smallestgroupsize[i] = np.min(count) if len(count) > 0 else 1

            row_interestingness = (row_counts / row_smallestgroupsize) / row_counts

            # What row is the most interesting
            row_idx = np.argmax(row_interestingness)
            e = E[row_idx]
            print("Most interesting:", row_idx)

            # Find a random, unfilled spot in this row
            # TODO: find a better solution for this,
            # finding a spot with a lot of columns could take long
            col_idx = random.randint(0, n_cols - 1)
            while col_idx in mat[row_idx, :].rows[0]:
                col_idx = (col_idx + 1) % n_cols

            sa = self.index2sa(col_idx)

            print(row_idx, col_idx)

            print(mat.toarray())

            equivalent, counterexample, output = self._are_equivalent(test_sul, sa + e)
            if not equivalent:
                return equivalent, counterexample
            else:
                mat[row_idx, col_idx] = 1 if output else -1


    def _are_equivalent(self, fsm, input):
        fsm.reset()
        hyp_output = fsm.process_input(input)
        self.sul.reset()
        sul_output = self.sul.process_input(input)
        #print(sul_output)

        return hyp_output == sul_output, input, hyp_output


    # TODO: interleave S entries instead of putting them all in a row
    def index2sa(self, index):
        A = self.getA()
        S = self.getS()
        maxdepth = self.max_depth

        # total cumulative length of A^n
        len_A = cumlen(len(A), maxdepth)

        idx_S = index // len_A
        idx_A = index % len_A

        # Calculate length "bins" to see how many times we repeat A
        lens = [cumlen(len(A), i) for i in range(1, maxdepth + 1)]

        n_A = 1
        for n, l in enumerate(lens):
            if idx_A >= l:
                n_A += 1

        idx_An = idx_A - ([0] + lens)[n_A - 1]

        a = index_product(idx_An, A, n_A)
        s = tuple(S[idx_S])

        return s + a

    def sa2index(self, s, a):
        A = self.getA()
        S = self.getS()
        maxdepth = self.max_depth

        s_idx = S.index(s)
        a_idx = product_index(a, A)

        a_n = len(a)

        # Calculate length "bins" to see how many times we repeat A
        lens = [(len(A) * i) for i in range(1, maxdepth + 1)]
        cum_A = sum(lens[0:a_n - 1])

        return s_idx * cumlen(len(A), maxdepth) + a_idx + cum_A


#
# #
# def index2sa(index, S, A, maxdepth):
#     # total cumulative length of A^n
#     len_A = cumlen(len(A), maxdepth)
#
#     idx_S = index // len_A
#     idx_A = index % len_A
#
#     # Calculate length "bins" to see how many times we repeat A
#     lens = [cumlen(len(A), i) for i in range(1, maxdepth + 1)]
#
#     n_A = 1
#     for n, l in enumerate(lens):
#         if idx_A >= l:
#             n_A += 1
#
#     idx_An = idx_A - ([0] + lens)[n_A - 1]
#
#     a = index_product(idx_An, A, n_A)
#     s = tuple(S[idx_S])
#
#     return s + a
# #
# def sa2index(s, a, S, A, maxdepth):
#
#     s_idx = S.index(s)
#     a_idx = product_index(a, A)
#
#     a_n = len(a)
#
#     # Calculate length "bins" to see how many times we repeat A
#     lens = [(len(A) * i) for i in range(1, maxdepth + 1)]
#     cum_A = sum(lens[0:a_n - 1])
#
#     return s_idx * cumlen(len(A), maxdepth) + a_idx + cum_A
#
# if __name__ == "__main__":
#     S = ['A', 'B']
#     A = [1, 2]
#     repeats = 3
#
#     for i in range(cumlen(len(A), repeats) * len(S)):
#         cur = index2sa(i, S, A, repeats)
#         print(cur[0], cur[1:], sa2index(cur[0], cur[1:], S, A, repeats))

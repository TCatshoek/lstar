from itertools import product
from typing import Tuple, Iterable

from equivalencecheckers.equivalencechecker import EquivalenceChecker
from suls.sul import SUL

from scipy.sparse import lil_matrix
import numpy as np
from scipy.stats import entropy
from util.product import product_index, index_product, cumlen
from collections import Counter
import random
from util.RNG import FormatPreserving
import os

# Equivalence checker which attempts to use the entropy
# of the distinguishing sequences to figure out which one is most interesting,
# and then uses random sampling to pick an access sequence to use
class EntropyEquivalanceChecker(EquivalenceChecker):
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

        # Keep track of unique responses and their counts per row
        response_mem = [None] * n_rows
        for i in range(n_rows):
            response_mem[i] = Counter()

        unique_responses = set()

        # Keep track of the total number of queries asked
        n_queries = 0

        if hasattr(test_sul, 'cache'):
            # Fill mat with cached entries
            print("TODO: implement filling in cached entries")

        randomizers = []
        for i in range(n_rows):
            randomizers.append(FormatPreserving(n_cols, os.urandom(128)))

        col_idxes = np.zeros(n_rows, dtype=int)

        tracking = set()

        while n_queries <= n_cols * n_rows:
            n_uniq = len(unique_responses)

            # ---- Calculate row "interestingness" using information entropy
            interestingness = [0] * n_rows

            if n_uniq > 1:
                for row_idx, row_counter in enumerate(response_mem):
                    # If not enough unique values seen, check out this row a bit more
                    if len(row_counter.keys()) < 1:
                        interestingness[row_idx] = 1
                    # We also need at least a few values to reduce the chance of getting stuck
                    elif sum(row_counter.values()) < 50:
                        interestingness[row_idx] = 1
                    # If a row is completely filled, it is not interesting anymore
                    elif sum(row_counter.values()) == n_cols:
                        interestingness[row_idx] = 0
                    # Else calculate the entropy
                    else:
                        row_counts = np.array(list(row_counter.values()))
                        row_entropy = entropy(row_counts / sum(row_counts), base=n_uniq)
                        interestingness[row_idx] = row_entropy if row_entropy > 0 else 1
            else:
                interestingness = [1] * n_rows

            print(response_mem)
            print(interestingness)

            row_idx = np.argmax(interestingness)

            # Pick a random spot from the interesting row
            col_idx = randomizers[row_idx].fpe(col_idxes[row_idx])
            col_idxes[row_idx] = (col_idxes[row_idx] + 1) % n_cols
            tracking.add(col_idx)

            sa = self.index2sa(col_idx)
            e = E[row_idx]

            equivalent, counterexample, output = self._are_equivalent(test_sul, sa + e)
            response_mem[row_idx][output] += 1
            n_queries += 1
            unique_responses.add(output)

            if not equivalent:
                return equivalent, counterexample

        # print(tracking)
        # print(set(range(n_cols)))

        return True, None


    def _are_equivalent(self, fsm, input):
        fsm.reset()
        hyp_output = fsm.process_input(input)
        self.sul.reset()
        sul_output = self.sul.process_input(input)
        print(input)
        print(sul_output)

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

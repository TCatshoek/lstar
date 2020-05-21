from typing import Tuple, Iterable

from numpy.random.mtrand import choice

from equivalencecheckers.equivalencechecker import EquivalenceChecker
from suls.sul import SUL
from util.distinguishingset import get_distinguishing_set
from util.transitioncover import get_state_cover_set


class AccSeqFuzzer(EquivalenceChecker):
    def __init__(self, sul: SUL, depth=10, num_samples=1000):
        super().__init__(sul)
        self.depth = depth
        self.num_samples = num_samples

    def test_equivalence(self, test_sul: SUL) -> Tuple[bool, Iterable]:
        A = list(test_sul.get_alphabet())
        P = get_state_cover_set(test_sul)
        W = get_distinguishing_set(test_sul)
        W.add(tuple())

        for acc_seq in P:
            # Generate random walk paths over alphabet A
            paths = choice(A, size=(self.num_samples, self.depth))
            equivalent = True
            counterexample = None

            for path in paths:
                for w in W:
                    equivalent, counterexample = self._are_equivalent(test_sul, acc_seq + tuple(path) + w)
                    if not equivalent:
                        return equivalent, counterexample

            return equivalent, counterexample

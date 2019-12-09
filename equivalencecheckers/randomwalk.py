from typing import Tuple, Iterable

from numpy.random.mtrand import choice

from equivalencecheckers.equivalencechecker import EquivalenceChecker
from suls.sul import SUL


class RandomWalkEquivalenceChecker(EquivalenceChecker):
    def __init__(self, sul: SUL, max_depth=10, num_samples=1000):
        super().__init__(sul)
        self.max_depth = max_depth
        self.num_samples = num_samples

    def test_equivalence(self, test_sul: SUL) -> Tuple[bool, Iterable]:
        A = list(test_sul.get_alphabet())

        # Generate random walk paths over alphabet A
        paths = choice(A, size=(self.num_samples, self.max_depth))
        counterexample = None

        for path in paths:
            self.sul.reset()
            test_sul.reset()

            self_output = self.sul.process_input(path)
            test_output = test_sul.process_input(path)

            if self_output != test_output:
                counterexample = tuple(path)
                break

        equivalent = counterexample is None
        return equivalent, counterexample
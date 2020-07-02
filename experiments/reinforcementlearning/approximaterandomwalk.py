from typing import Tuple, Iterable

from numpy.random.mtrand import choice

from equivalencecheckers.equivalencechecker import EquivalenceChecker
from suls.sul import SUL


class ApproximateRandomWalkEquivalenceChecker(EquivalenceChecker):
    def __init__(self, sul: SUL, max_depth=10, num_samples=1000, e=0.2):
        super().__init__(sul)
        self.max_depth = max_depth
        self.num_samples = num_samples
        self.e = e

    def test_equivalence(self, test_sul: SUL) -> Tuple[bool, Iterable]:
        A = list(test_sul.get_alphabet())

        # Generate random walk paths over alphabet A
        paths = choice(A, size=(self.num_samples, self.max_depth))
        counterexample = None

        for path in paths:
            for i in range(1, len(path)):
                self.sul.reset()
                test_sul.reset()

                self_output = self.sul.process_input(path[0:i])
                test_output = test_sul.process_input(path[0:i])

                if not self.eq(self_output, test_output):
                    counterexample = tuple(path[0:i])
                    break

            if counterexample is not None:
                break

        equivalent = counterexample is None
        return equivalent, (self_output, counterexample)

    def eq(self, el1, el2, e=None):
        if e is None:
            e = self.e

        try:
            diff = (max((el1, el2)) / min((el1, el2))) - 1
        except ZeroDivisionError:
            return max((el1, el2)) == min((el1, el2))

        if diff > e:
            return False

        return True
from itertools import product
from abc import ABC, abstractmethod
from suls.sul import SUL
from typing import Tuple, Iterable
from numpy.random import choice

class EquivalenceChecker(ABC):
    def __init__(self, sul):
        self.sul = sul

    @abstractmethod
    def test_equivalence(self, test_sul: SUL) -> Tuple[bool, Iterable]:
        pass


# Dumb brute force equivalence checker V0.01
class BFEquivalenceChecker(EquivalenceChecker):
    def __init__(self, sul: SUL, max_depth=5):
        super().__init__(sul)
        self.A = sul.get_alphabet()
        self.max_depth = max_depth


    def test_equivalence(self, test_sul: SUL) -> Tuple[bool, Iterable]:
        counterexample = None
        found = False

        for n in range(self.max_depth):
            tests = product(self.A, repeat=n)

            for test in tests:
                self.sul.reset()
                test_sul.reset()

                self_output = self.sul.process_input(test)
                test_output = test_sul.process_input(test)

                if self_output != test_output:
                    # Counterexample found
                    counterexample = test
                    found = True
                    break

            if found:
                break

        # If we didn't find a counterexample, assume equivalence
        equivalent = not found

        return equivalent, counterexample


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

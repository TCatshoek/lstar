from itertools import product
from typing import Tuple, Iterable

from equivalencecheckers.equivalencechecker import EquivalenceChecker
from suls.sul import SUL


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

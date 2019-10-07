from statemachine import StateMachine
from itertools import product

# Dumb brute force equivalence checker V0.01
class EquivalenceChecker:
    def __init__(self, dfa: StateMachine, max_depth=5):
        self.A = dfa.gather_alphabet()
        self.dfa = dfa
        self.max_depth = max_depth

    def test_equivalence(self, test_dfa: StateMachine):
        counterexample = None
        found = False

        for n in range(self.max_depth):
            tests = product(self.A, repeat=n)

            for test in tests:
                self.dfa.reset()
                self_output = self.dfa.process_input(test)
                test_dfa.reset()
                test_output = test_dfa.process_input(test)

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
import tempfile
from itertools import product
from typing import Tuple, Iterable
from util.distinguishingset import get_distinguishing_set
from util.transitioncover import get_state_cover_set
from equivalencecheckers.equivalencechecker import EquivalenceChecker
from suls.dfa import DFA
from suls.mealymachine import MealyMachine, MealyState
from suls.sul import SUL
from typing import Union
from itertools import product, chain

# Implements chow's W-method for equivalence checking
class WmethodEquivalenceChecker(EquivalenceChecker):
    def __init__(self, sul: SUL, m=5):
        super().__init__(sul)
        self.m = m

    def test_equivalence(self, fsm: Union[DFA, MealyMachine]) -> Tuple[bool, Iterable]:
        # First generate test sequences
        n = len(fsm.get_states())
        m = self.m

        if n > m:
            m = n

        assert m >= n, "hypothesis has more states than w-method bound"

        W = get_distinguishing_set(fsm)
        P = get_state_cover_set(fsm)
        X = fsm.get_alphabet()

        Z = W.copy()
        for i in range(1, (m-n) + 1):
            X_m_n = X if i == 1 else set(product(X, repeat=i))
            # Need to flatten the tuples because of how product works
            Z = set([tuple(chain.from_iterable(x)) for x in Z.union(product(X_m_n, W))])

        test_sequences = set([tuple(chain.from_iterable(x)) for x in list(product(P, Z))])

        print(test_sequences)

        # Apply the test sequences to the SUTs and compare
        equivalent = True
        counterexample = None
        for sequence in sorted(test_sequences, key=len):
            fsm.reset()
            hyp_output = fsm.process_input(sequence)
            self.sul.reset()
            sul_output = self.sul.process_input(sequence)

            if hyp_output != sul_output:
                equivalent = False
                counterexample = sequence
                break

        return equivalent, counterexample


if __name__ == "__main__":
    s1 = MealyState('1')
    s2 = MealyState('2')
    s3 = MealyState('3')
    s4 = MealyState('4')
    s5 = MealyState('5')

    s1.add_edge('a', 'nice', s2)
    s1.add_edge('b', 'nice', s3)

    s2.add_edge('a', 'nice!', s4)
    s2.add_edge('b', 'back', s1)

    s3.add_edge('a', 'nice', s4)
    s3.add_edge('b', 'back', s1)

    s4.add_edge('a', 'nice', s5)
    s4.add_edge('b', 'nice', s5)

    s5.add_edge('a', 'loop', s5)
    s5.add_edge('b', 'loop', s5)

    mm = MealyMachine(s1)

    eqc = WmethodEquivalenceChecker(mm, 7)

    print(eqc.test_equivalence(mm))
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
from tqdm import tqdm
from suls.rersconnectorv2 import RERSConnectorV2
from collections import deque

# Implements chow's W-method for equivalence checking
# Kinda horrible because it precalculates all inputs first and that's really costly
class WmethodEquivalenceChecker(EquivalenceChecker):
    def __init__(self, sul: SUL, m=5, overshoot=0):
        super().__init__(sul)
        self.m = m
        self.overshoot = overshoot

    def test_equivalence(self, fsm: Union[DFA, MealyMachine]) -> Tuple[bool, Iterable]:
        # First generate test sequences
        n = len(fsm.get_states())
        m = self.m

        if n > m:
            m = n + self.overshoot

        assert m >= n, "hypothesis has more states than w-method bound"

        W = get_distinguishing_set(fsm)
        P = get_state_cover_set(fsm)
        X = set([(x,) for x in fsm.get_alphabet()])

        Z = W.copy()
        for i in range(1, (m-n) + 1):
            X_m_n = X if i == 1 else set([tuple(chain.from_iterable(x)) for x in set(product(X, repeat=i))])
            #X_m_n =  X_m_n])
            # Need to flatten the tuples because of how product works
            Z = Z.union(set([tuple(chain.from_iterable(x)) for x in product(X_m_n, W)]))

        test_sequences = set([tuple(chain.from_iterable(x)) for x in set(product(P, Z))])

        # for pr in set(product(P, Z)):
        #     tmp = tuple(chain.from_iterable(pr))
        #     if '0' in tmp:
        #         print(pr)

        #print(test_sequences)

        # Apply the test sequences to the SUTs and compare
        equivalent = True
        counterexample = None
        for sequence in tqdm(test_sequences):
            fsm.reset()
            hyp_output = fsm.process_input(sequence)
            self.sul.reset()
            sul_output = self.sul.process_input(sequence)

            if hyp_output != sul_output:
                equivalent = False
                counterexample = sequence
                break

        return equivalent, counterexample


# Wmethod-ish eq checker with RERS-specific optimizations
class RersWmethodEquivalenceChecker(EquivalenceChecker):
    def __init__(self, sul: RERSConnectorV2, longest_first=False, m=5):
        super().__init__(sul)
        self.m = m
        self.longest_first = longest_first

    def test_equivalence(self, fsm: Union[DFA, MealyMachine]) -> Tuple[bool, Iterable]:
        print("[info] Starting equivalence test")
        # Don't bother with the distinguishing set for now
        #W = get_distinguishing_set(fsm)

        P = get_state_cover_set(fsm)
        print("[info] Got state cover set")
        A = sorted([(x,) for x in fsm.get_alphabet()])

        equivalent = True
        counterexample = None

        for access_sequence in sorted(P, key=len, reverse=self.longest_first):
            #print("[info] Trying access sequence:", access_sequence)
            to_visit = deque()
            to_visit.extend(A)

            while len(to_visit) > 0:
                cur = to_visit.popleft()
                #print(cur)
                # Check cache if this is invalid input
                if access_sequence + cur in self.sul.invalid_cache:
                    continue

                # Check cache if this is a known error
                prefix, value = self.sul.error_cache.shortest_prefix(" ".join([str(x) for x in access_sequence + cur]))
                if prefix is not None:
                    # Do check it tho
                    equivalent, counterexample = self._are_equivalent(fsm, access_sequence + cur)
                    if not equivalent:
                        return equivalent, counterexample
                    continue

                # If the test is of sufficient length, execute it
                #if len(cur) == self.m:
                #print("[Testing]", access_sequence + cur)
                equivalent, counterexample = self._are_equivalent(fsm, access_sequence + cur)
                if not equivalent:
                    return equivalent, counterexample

                # If not, keep building
                #else:
                if len(cur) < self.m:
                    for a in A:
                        if access_sequence + cur + a not in self.sul.invalid_cache:
                            to_visit.append(cur + a)

        return equivalent, counterexample

    # Wmethod-ish eq checker with RERS-specific optimizations
    class AsyncRersWmethodEquivalenceChecker(EquivalenceChecker):
        def __init__(self, sul: RERSConnectorV2, m=5):
            super().__init__(sul)
            self.m = m

        async def test_equivalence(self, fsm: Union[DFA, MealyMachine]) -> Tuple[bool, Iterable]:
            print("[info] Starting equivalence test")
            # Don't bother with the distinguishing set for now
            # W = get_distinguishing_set(fsm)

            P = get_state_cover_set(fsm)
            print("[info] Got state cover set")
            A = sorted([(x,) for x in fsm.get_alphabet()])

            equivalent = True
            counterexample = None

            for access_sequence in sorted(P, key=len):
                # print("[info] Trying access sequence:", access_sequence)
                to_visit = deque()
                to_visit.extend(A)

                while len(to_visit) > 0:
                    cur = to_visit.popleft()
                    # print(cur)
                    # Check cache if this is invalid input
                    if access_sequence + cur in self.sul.invalid_cache:
                        continue

                    # Check cache if this is a known error
                    prefix, value = self.sul.error_cache.shortest_prefix(
                        " ".join([str(x) for x in access_sequence + cur]))
                    if prefix is not None:
                        continue

                    # If the test is of sufficient length, execute it
                    # if len(cur) == self.m:
                    print("[Testing]", access_sequence + cur)
                    equivalent, counterexample = self._are_equivalent(fsm, access_sequence + cur)
                    if not equivalent:
                        return equivalent, counterexample

                    # If not, keep building
                    # else:
                    if len(cur) < self.m:
                        for a in A:
                            if access_sequence + cur + a not in self.sul.invalid_cache:
                                to_visit.append(cur + a)

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
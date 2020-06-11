import tempfile
from itertools import product
from typing import Tuple, Iterable

from pygtrie import PrefixSet

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
class WmethodEquivalenceChecker(EquivalenceChecker):
    def __init__(self, sul: SUL, m=5, longest_first=False):
        super().__init__(sul)
        self.m = m
        self.longest_first = longest_first

    def test_equivalence(self, fsm: Union[DFA, MealyMachine]) -> Tuple[bool, Iterable]:
        print("Starting EQ test")

        n = len(fsm.get_states())
        m = self.m

        assert m >= n, "hypothesis has more states than w-method bound"

        depth = m - n + 1

        print('Attempting to determine distinguishing set')
        W = get_distinguishing_set(fsm)
        #W.add(tuple())
        print('distinguishing:', W)
        P = get_state_cover_set(fsm)
        print('state cover:', P)
        X = fsm.get_alphabet() #set([(x,) for x in fsm.get_alphabet()])

        equivalent = True
        counterexample = None

        order = sorted(range(1, depth + 1), reverse=self.longest_first)


        for i in order:
            print(i, '/', depth)
            for p in P:
                for x in product(X, repeat=i):
                    for w in W:
                        test_sequence = p + x + w
                        print(test_sequence)
                        equivalent, counterexample = self._are_equivalent(fsm, test_sequence)
                        if not equivalent:
                            print("COUNTEREXAMPLE:", counterexample)
                            return equivalent, counterexample

        return equivalent, counterexample


# Wmethod EQ checker with early stopping
class SmartWmethodEquivalenceChecker(EquivalenceChecker):
    def __init__(self, sul: SUL, m=None, horizon=None, stop_on=set(), stop_on_startswith=set(), order_type='shortest first'):
        super().__init__(sul)
        self.m = m
        self.horizon = horizon
        assert (horizon is None or m is None) and not (m is None and horizon is None), "Set either m or horizon"

        # These are the outputs we want to cut our testing tree short on
        self.stop_on = stop_on
        self.stop_on_startswith = stop_on_startswith
        # This prefix set keeps track of what paths lead to the outputs we want to stop early on
        self.stopping_set = PrefixSet()

        # Keep track of how many times each access sequence has been part of a counterexample
        self.acc_seq_ce_counter = {}

        # Figure out how to order the access sequences
        order_types = {
            'longest first': lambda P: sorted(P, key=len, reverse=True),
            'shortest first': lambda P: sorted(P, key=len, reverse=False),
            'ce count': lambda P: sorted(P, key=lambda x: (self.acc_seq_ce_counter[x], -len(x)), reverse=True)
        }
        assert order_type in order_types.keys(), "Unknown access sequence ordering"
        self.order_type = order_type
        self.acc_seq_order = order_types[order_type]

    def test_equivalence(self, fsm: Union[DFA, MealyMachine]) -> Tuple[bool, Iterable]:
        print("[info] Starting equivalence test")
        if self.m is not None:
            n = len(fsm.get_states())
            m = self.m
            assert m >= n, "hypothesis has more states than w-method bound"
            depth = m - n
        else:
            depth = self.horizon

        print("Depth:", depth)

        print("[info] Calculating distinguishing set")
        W = get_distinguishing_set(fsm, check=False)

        P = get_state_cover_set(fsm)
        print("[info] Got state cover set")

        # Ensure all access sequences have a counter
        for p in P:
            if p not in self.acc_seq_ce_counter:
                self.acc_seq_ce_counter[p] = 0

        A = sorted([(x,) for x in fsm.get_alphabet()])

        equivalent = True
        counterexample = None

        for access_sequence in self.acc_seq_order(P):
            print("[info] Trying access sequence:", access_sequence)
            to_visit = deque()
            to_visit.extend(A)

            while len(to_visit) > 0:
                cur = to_visit.popleft()

                # Basically the usual W-method tests:
                for w in W:
                    equivalent, counterexample = self._are_equivalent(fsm, access_sequence + cur + w)
                    if not equivalent:
                        self.acc_seq_ce_counter[access_sequence] += 1
                        return equivalent, counterexample

                # Also test without distinguishing sequence, important for early stopping
                equivalent, counterexample = self._are_equivalent(fsm, access_sequence + cur)
                if not equivalent:
                    self.acc_seq_ce_counter[access_sequence] += 1
                    return equivalent, counterexample

                # Cut this branch short?
                if access_sequence + cur in self.stopping_set:
                    continue

                # If not, keep building
                #else:
                if len(cur) <= depth:
                    for a in A:
                        if access_sequence + cur + a not in self.stopping_set:
                            to_visit.append(cur + a)

            # Nothing found for this access sequence:
            self.acc_seq_ce_counter[access_sequence] = min(0, self.acc_seq_ce_counter[access_sequence])
            self.acc_seq_ce_counter[access_sequence] -= 1

        return equivalent, counterexample

    def _are_equivalent(self, fsm, input):
        #print("[info] Testing:", input)
        fsm.reset()
        hyp_output = fsm.process_input(input)
        self.sul.reset()
        sul_output = self.sul.process_input(input)

        if self._teacher is not None:
            self._teacher.test_query_counter += 1

        if sul_output in self.stop_on or any([sul_output.startswith(x) for x in self.stop_on_startswith]):
            #print('[info] added input to early stopping set')
            self.stopping_set.add(input)

        equivalent = hyp_output == sul_output
        if not equivalent:
            print("EQ CHECKER", input, "HYP", hyp_output, "SUL", sul_output)
            self._onCounterexample(input)

        return equivalent, input


# Wmethod EQ checker with early stopping, access sequence scheduling
class SmartWmethodEquivalenceCheckerV2(EquivalenceChecker):
    def __init__(self, sul: SUL, m=None, horizon=None, stop_on=set(), stop_on_startswith=set(), order_type='shortest first'):
        super().__init__(sul)
        self.m = m
        self.horizon = horizon
        assert (horizon is None or m is None) and not (m is None and horizon is None), "Set either m or horizon"

        # These are the outputs we want to cut our testing tree short on
        self.stop_on = stop_on
        self.stop_on_startswith = stop_on_startswith
        # This prefix set keeps track of what paths lead to the outputs we want to stop early on
        self.stopping_set = PrefixSet()

        # Figure out how to order the access sequences
        order_types = {
            'longest first': lambda P: sorted(P, key=len, reverse=True),
            'shortest first': lambda P: sorted(P, key=len, reverse=False),
        }
        assert order_type in order_types.keys(), "Unknown access sequence ordering"
        self.order_type = order_type
        self.acc_seq_order = order_types[order_type]

    def test_equivalence(self, fsm: Union[DFA, MealyMachine]) -> Tuple[bool, Iterable]:
        print("[info] Starting equivalence test")
        if self.m is not None:
            n = len(fsm.get_states())
            m = self.m
            assert m >= n, "hypothesis has more states than w-method bound"
            depth = m - n
        else:
            depth = self.horizon

        print("Depth:", depth)

        print("[info] Calculating distinguishing set")
        W = get_distinguishing_set(fsm, check=False)

        P = get_state_cover_set(fsm)
        print("[info] Got state cover set")

        A = sorted([(x,) for x in fsm.get_alphabet()])

        equivalent = True
        counterexample = None

        acc_seq_tasks = deque(
            zip(
                self.acc_seq_order(P),
                [deque([a for a in A if a not in self.stopping_set]) for x in range(len(P))]
            )
        )

        while len(acc_seq_tasks) > 0:
            access_sequence, to_visit = acc_seq_tasks.popleft()
            print("[info] Trying access sequence:", access_sequence)
            assert len(to_visit) > 0

            cur = to_visit.popleft()

            # Test without distinguishing sequence, important for early stopping
            equivalent, counterexample = self._are_equivalent(fsm, access_sequence + cur)
            if not equivalent:
                return equivalent, counterexample

            if access_sequence + cur not in self.stopping_set:
                # Basically the usual W-method tests:
                for w in W:
                    equivalent, counterexample = self._are_equivalent(fsm, access_sequence + cur + w)
                    if not equivalent:
                        return equivalent, counterexample

                # If not, keep building
                if len(cur) <= depth:
                    for a in A:
                        if access_sequence + cur + a not in self.stopping_set:
                            to_visit.append(cur + a)

            if len(to_visit) > 0:
                acc_seq_tasks.append((access_sequence, to_visit))
            else:
                print(access_sequence)

        return equivalent, counterexample

    def _are_equivalent(self, fsm, input):
        print("[info] Testing:", input)
        fsm.reset()
        hyp_output = fsm.process_input(input)
        self.sul.reset()
        sul_output = self.sul.process_input(input)

        if self._teacher is not None:
            self._teacher.test_query_counter += 1

        if sul_output in self.stop_on or any([sul_output.startswith(x) for x in self.stop_on_startswith]):
            #print('[info] added input to early stopping set')
            self.stopping_set.add(input)

        equivalent = hyp_output == sul_output
        if not equivalent:
            print("EQ CHECKER", input, "HYP", hyp_output, "SUL", sul_output)
            self._onCounterexample(input)

        return equivalent, input

# Wmethod-ish eq checker with RERS-specific optimizations
class RersWmethodEquivalenceChecker(EquivalenceChecker):
    def __init__(self, sul: RERSConnectorV2, longest_first=False, m=5):
        super().__init__(sul)
        self.m = m
        self.longest_first = longest_first

    def test_equivalence(self, fsm: Union[DFA, MealyMachine]) -> Tuple[bool, Iterable]:
        print("[info] Starting equivalence test")
        # Don't bother with the distinguishing set for now
        W = get_distinguishing_set(fsm)

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
                for w in [tuple()] + list(W):
                    equivalent, counterexample = self._are_equivalent(fsm, access_sequence + cur + w)
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
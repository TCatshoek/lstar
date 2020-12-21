from equivalencecheckers.equivalencechecker import EquivalenceChecker
from suls.sul import SUL
from typing import Tuple, Iterable, Callable, Optional
import random

from util.markov import MarkovChain

class MarkovEquivalenceChecker(EquivalenceChecker):
    def __init__(self, sul, counterexampletracker, ngramsize=3, n_queries=10000, len_increase_factor=2):
        super().__init__(sul)
        self.ct = counterexampletracker
        self.ngramsize = ngramsize
        self.n_queries = n_queries
        self.len_increase_factor = len_increase_factor

    def test_equivalence(self, test_sul: SUL) -> Tuple[bool, Optional[Iterable]]:
        # Get the currently known counterexamples
        counterexamples = self.ct.storage

        # Bail if we don't have any counterexamples yet
        if len(counterexamples) < 1:
            return True, None

        # Figure out how long the shortest and longest counterexamples are
        shortest = min([len(ce) for ce in counterexamples])
        longest = max([len(ce) for ce in counterexamples])

        # Train a markov chain on them
        mc = MarkovChain()
        mc.fit(counterexamples, self.ngramsize)

        for i in range(self.n_queries):
            # Generate a new sequence
            new_seq_len = random.randint(shortest, longest * self.len_increase_factor)
            new_sequence = mc.generate(new_seq_len)

            #print("Trying:", new_sequence)

            equivalent, input = self._are_equivalent(test_sul, new_sequence)
            if not equivalent:
                return False, input

        return True, None

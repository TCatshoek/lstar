from abc import ABC, abstractmethod
from suls.sul import SUL
from typing import Tuple, Iterable, Callable, Optional


class EquivalenceChecker(ABC):
    def __init__(self, sul):
        self.sul = sul

        # Noop init
        self._onCounterexample: Callable[[Iterable], None] = lambda x: None

    @abstractmethod
    def test_equivalence(self, test_sul: SUL) -> Tuple[bool, Optional[Iterable]]:
        pass

    def onCounterexample(self, fun: Callable[[Iterable], None]):
        self._onCounterexample = fun

    # Todo: fix this so it compares the whole output sequence instead of just the last output
    def _are_equivalent(self, fsm, input):
        fsm.reset()
        hyp_output = fsm.process_input(input)
        self.sul.reset()
        sul_output = self.sul.process_input(input)
        #print(sul_output)

        equivalent = hyp_output == sul_output
        if not equivalent:
            self._onCounterexample(input)

        return equivalent, input


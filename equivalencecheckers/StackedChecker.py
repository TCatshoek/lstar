from typing import List, Optional, Iterable, Tuple, Callable

from equivalencecheckers.equivalencechecker import EquivalenceChecker
from suls.sul import SUL


class StackedChecker(EquivalenceChecker):
    def __init__(self, *args):
        super().__init__(None)
        self.checkers: List[EquivalenceChecker] = []

        for arg in args:
            self.checkers.append(arg)

    def test_equivalence(self, test_sul: SUL) -> Tuple[bool, Optional[Iterable]]:
        for checker in self.checkers:
            print('EQ check using', checker)
            equivalent, input = checker.test_equivalence(test_sul)

            if not equivalent:
                return False, input

        return True, None

    def onCounterexample(self, fun: Callable[[Iterable], None]):
        for checker in self.checkers:
            checker.onCounterexample(fun)

    def _are_equivalent(self, fsm, input):
        assert False, "Don't call the _are_equivalent of the stacker directly"

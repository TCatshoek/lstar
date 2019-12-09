from abc import ABC, abstractmethod
from suls.sul import SUL
from typing import Tuple, Iterable


class EquivalenceChecker(ABC):
    def __init__(self, sul):
        self.sul = sul

    @abstractmethod
    def test_equivalence(self, test_sul: SUL) -> Tuple[bool, Iterable]:
        pass





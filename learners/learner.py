from abc import ABC, abstractmethod
from teachers.teacher import Teacher
from suls.sul import SUL

class Learner(ABC):
    def __init__(self, teacher: Teacher):
        self.teacher = teacher

    @abstractmethod
    def run(self) -> SUL:
        pass
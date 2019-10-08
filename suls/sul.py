from abc import ABC, abstractmethod


class SUL(ABC):

    @abstractmethod
    def process_input(self, inputs):
        pass

    @abstractmethod
    def reset(self):
        pass

    @abstractmethod
    def get_alphabet(self):
        pass
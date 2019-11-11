from suls.sul import SUL
from typing import Iterable
from functools import reduce
import re

# Define a DFA using a regex
# TODO: Better alphabet extraction
class RegexMachine(SUL):
    def __init__(self, expression):
        self.expression = expression

    def process_input(self, inputs):
        if not isinstance(inputs, Iterable):
            inputs = [inputs]

        # Get string representation of the input sequence
        if len(inputs) == 0:
            input = ''
        else:
            input = reduce(lambda x, y: str(x) + str(y), inputs)

        match = re.search(self.expression, input)

        if match is not None:
            return match.group() == input
        else:
            return False

    def reset(self):
        pass

    # assume the alphabet is all alphabetical characters in the regex
    def get_alphabet(self):
        pattern = re.compile('[^a-zA-Z]')
        return set(pattern.sub('', self.expression))

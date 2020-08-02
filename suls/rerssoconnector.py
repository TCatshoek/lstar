from suls.rersconnectorv4 import RERSConnectorV4
from suls.sul import SUL
from subprocess import check_output
import re

from ctypes import *

class RERSSOConnector(SUL):
    def __init__(self, path_to_so):
        self.path_to_so = path_to_so

        # Hook up the shared library
        self.dll = CDLL(path_to_so)

        # Set types
        self.dll.reset.restype = None
        self.dll.calculate_output.argtypes = [c_int]
        self.dll.calculate_output.restype = c_int

        # Be sure to initialize all variables in the RERS code
        self.dll.reset()

    def process_input(self, inputs):
        output = None
        for input in inputs:
            output = self.dll.calculate_output(int(input))
            if output < -1:
                return f'error_{str((output * -1) - 2)}'

        if output == -1:
            return "invalid_input"

        return str(output)

    def reset(self):
        self.dll.reset()

    def get_alphabet(self):
        # Grep the source file for the line defining the input alphabet
        tmp = check_output(["grep", "-o", "int inputs\[\] \= {\(.*\)};", f"{self.path_to_so.replace('.so', '')}.c"])
        # Extract it and put it into a list
        return re.search('{(.*)}', tmp.decode()).group(1).split(',')


if __name__ == "__main__":

    n = 10000

    #asyncio.run(main(n))

    path = "/home/tom/projects/lstar/rers/TrainingSeqReachRers2019/Problem11/Problem11.so"
    r = RERSSOConnector(path)
    alphabet = r.get_alphabet()

    path = "/home/tom/projects/lstar/rers/TrainingSeqReachRers2019/Problem11/Problem11"
    r2 = RERSConnectorV4(path)

    from numpy.random import choice
    import time

    inputs = []
    for i in range(n):
        inputs.append(list(choice(alphabet, 100)))

    #inputs = [['9', '7', '7'], ['8', '9', '7', '7']]
    start = time.perf_counter()

    for input in inputs:
        print("Sending", input)
        r.reset()
        result = r.process_input(input)

        # result2 = r2.process_input(input)
        # print()
        # print('Result from SO:', result)
        # print('Result from Connector:', result2)
        # assert(result == result2)

    end = time.perf_counter() - start
    print(f'Took {end:0.5f} seconds')

    print("DONE")





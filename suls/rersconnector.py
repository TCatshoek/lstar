from suls.sul import SUL
import pexpect
from subprocess import check_output
import re

# This class serves as an adaptor to the RERS 2019 problems
# It uses pexpect to interact with the compiled c programs
# It also provides early stopping functionality for queries known
# to be prefixed by invalid input
class RERSConnector(SUL):
    def __init__(self, path_to_binary):
        self.path = path_to_binary
        self.p = pexpect.spawn(self.path, encoding='utf-8')
        self.invalid_prefixes = set()
        self.error_hit_prefixes = set()
        self.needs_reset = True
        self.cache = {}

    def process_input(self, inputs):
        inputs = tuple(inputs)
        print("[Query]", inputs)

        # Check if the input is already in cache
        if inputs in self.cache.keys():
            self.needs_reset = False
            print("[Cache hit]")
            return self.cache[inputs]

        # Check if a prefix of the current input sequence has already been invalidated
        for i in range(len(inputs)):
            if inputs[0:i+1] in self.invalid_prefixes:
                print("[Skipped - Invalid prefix]")
                self.needs_reset = False
                self.cache[inputs] = False
                return False

        # Check if a prefix of the current input already hit a verifier error
        for i in range(len(inputs)):
            if inputs[0:i+1] in self.error_hit_prefixes:
                print("[Skipped - Verifier error found]")
                self.needs_reset = False
                self.cache[inputs] = True
                return True

        # If not, actually send the input to the SUT
        for input in inputs:
            self.needs_reset = True
            print("[Send]", input)
            self.p.sendline(input)

            index = self.p.expect([
                '[0-9]+\r\n([0-9]+)\r\n',
                'Invalid input:.*$'
            ])

            # We have an accepted input or a verifier error
            if index == 0:
                # Keep track of the matched regex in case we need to still print it
                prev_match = self.p.match

                # Check if we have hit a verifier error
                idx_2 = self.p.expect(['error_[0-9]+', pexpect.TIMEOUT], timeout=0.05)
                if idx_2 == 0:
                    print("[OK]", prev_match.group(1))
                    print("[Verifier ERROR]", self.p.match.group(0))
                    self.error_hit_prefixes.add(inputs)
                    self.cache[inputs] = True
                    return True
                else:
                    print("[OK]", prev_match.group(1))

            # We have an invalid input
            elif index == 1:
                print("[ERROR]", self.p.match.group(0))
                self.invalid_prefixes.add(inputs)
                self.cache[inputs] = False
                return False

        self.cache[inputs] = False
        return False


    def reset(self):
        if self.needs_reset:
            print("[Reset]")
            self.p.terminate()
            self.p = pexpect.spawn(self.path, encoding='utf-8')

    def get_alphabet(self):
        # Grep the source file for the line defining the input alphabet
        tmp = check_output(["grep", "-o", "int inputs\[\] \= {\(.*\)};", f"{self.path}.c"])
        # Extract it and put it into a list
        return re.search("{(.*)}", tmp.decode()).group(1).split(',')


if __name__ == "__main__":
    r = RERSConnector('../rers/SeqReachabilityRers2019/Problem11/Problem11')
    alphabet = r.get_alphabet()

    from numpy.random import choice
    input = list(choice(alphabet, 200))
    input = ["3", "10"]
    print("Sending", input)
    r.process_input(input)

    print("DONE")
from suls.sul import SUL
import pexpect
from subprocess import check_output, CalledProcessError, STDOUT
import re
import pygtrie

class RERSConnectorV2(SUL):
    def __init__(self, path_to_binary, terminator="0"):
        self.path = path_to_binary
        self.needs_reset = True
        self.cache = {}
        self.error_cache = pygtrie.StringTrie(separator=" ")
        self.invalid_cache = pygtrie.PrefixSet()

        self.terminator = terminator
        assert terminator not in self.get_alphabet(), f"Terminator {terminator} in alphabet, please choose a different one"

    def _interact(self, inputs):
        try:
            a = check_output(
                f'echo "{" ".join([str(x) for x in inputs])} 0" | {self.path}',
                stderr=STDOUT,
                shell=True)
        except CalledProcessError as e:
            a = e.output

        output_lines = a.decode().split('\n')

        result = None
        for idx, line in enumerate(output_lines):
            if len(line) > 0:
                if match := re.match("[0-9]+$", line):
                    result = match.group(0)
                elif re.match("Invalid input:", line):
                    #self.invalid_cache.add(inputs[0:idx + 1])
                    result = "Invalid input"
                elif match := re.match("error_[0-9]+", line):
                    tmp = match.group(0)
                    self.error_cache[" ".join(inputs)] = tmp
                    return tmp

                if "error" not in output_lines[idx + 1]:
                    self.cache[inputs[0:idx + 1]] = result

        self.cache[inputs] = result
        return result


    def process_input(self, inputs):
        inputs = tuple(inputs)


        # Check if the input is already in cache
        if inputs in self.cache.keys():
            self.needs_reset = False
            #print("[Cache hit]", inputs)
            return self.cache[inputs]

        # Check prefixes
        if inputs in self.invalid_cache:
            #print("[Invalid]", inputs)
            return "Invalid input"

        # We need a string representing the input, actions separated with a space
        inputs_string = " ".join(inputs)
        prefix, value = self.error_cache.shortest_prefix(inputs_string)
        if prefix is not None:
            #print("[Known Error]", inputs)
            return value

        # If no cache hit, actually send the input to the SUT
        #print("[Query]", inputs)
        return self._interact(inputs)

    def reset(self):
        pass

    def get_alphabet(self):
        # Grep the source file for the line defining the input alphabet
        tmp = check_output(["grep", "-o", "int inputs\[\] \= {\(.*\)};", f"{self.path}.c"])
        # Extract it and put it into a list
        return re.search('{(.*)}', tmp.decode()).group(1).split(',')


if __name__ == "__main__":

    r = RERSConnectorV2('../rers/TrainingSeqReachRers2019/Problem11/Problem11')
    alphabet = r.get_alphabet()
    from numpy.random import choice

    for i in range(100):

        input = list(choice(alphabet, 1))
        print("Sending", input)
        result = r.process_input(input)
        print("Result:", result)

    print("DONE")
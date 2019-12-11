from suls.sul import SUL
import pexpect
from subprocess import check_output
import re
from abc import ABC, abstractmethod
from typing import Tuple

import threading
import time

# Restarting a process with pexpect takes a long time,
# So lets try creating a pool-ish thing that starts
# Them in the background, so they're ready to go when
# We need em
class PexpectPool:
    def __init__(self, path, n):
        self.path = path
        self.n = n
        self.cur_idx = 0
        self.processes = [None]*n
        self.available = [False]*n
        self._lock = threading.Lock()

        threads = []
        for i in range(n):
            print('starting', i)
            threads.append(threading.Thread(target=self._start, args=(i,)))
            threads[i].start()
            print('started', i)

        for thread in threads:
            print("started", thread)
            thread.join()

    def get(self):
        with self._lock:
            # Find the nearest slot that is ready to go
            while True not in self.available:
                time.sleep(0.01)

            idx = self.available.index(True)
            self.available[idx] = False

            print('[CHECKOUT]', idx)

            # Create a new process in the background soon
            threading.Timer(0.5, self._start, args=[idx]).start()
            return self.processes[idx]

    def _start(self, index):

        self.processes[index] = pexpect.spawn(self.path, encoding='utf-8')
        self.available[index] = True

    def reset(self, process):
        threading.Thread(target=process.terminate)



# This class serves as an adaptor to the RERS 2019 problems
# It uses pexpect to interact with the compiled c programs
# It also provides early stopping functionality for queries known
# to be prefixed by invalid input or hitting a verifier error
class RERSConnector(SUL, ABC):
    def __init__(self, path_to_binary):
        self.path = path_to_binary
        self.pool = PexpectPool(self.path, 10)
        self.p = self.pool.get()
        self.needs_reset = True
        self.cache = {}

    @abstractmethod
    def _interact(self, inputs):
        pass

    @abstractmethod
    def _checkinvalidprefixes(self, inputs) -> Tuple[bool, object]:
        pass

    def process_input(self, inputs):
        inputs = tuple(inputs)
        print("[Query]", inputs)

        # Check if the input is already in cache
        if inputs in self.cache.keys():
            self.needs_reset = False
            print("[Cache hit]")
            return self.cache[inputs]

        # Check prefixes
        hit, result = self._checkinvalidprefixes(inputs)
        if hit:
            return result

        # If no cache hit, actually send the input to the SUT
        return self._interact(inputs)

    def reset(self):
        if self.needs_reset:
            print("[Reset]")
            self.pool.reset(self.p)
            self.p = self.pool.get()

    def get_alphabet(self):
        # Grep the source file for the line defining the input alphabet
        tmp = check_output(["grep", "-o", "int inputs\[\] \= {\(.*\)};", f"{self.path}.c"])
        # Extract it and put it into a list
        return re.search('{(.*)}', tmp.decode()).group(1).split(',')


# Connects and interacts with the RERS programs, returning booleans for DFA learning
# True is returned on a verifier error (so these turn into an accepting state)
# False is returned otherwise
class BooleanRERSConnector(RERSConnector):

    def __init__(self, path_to_binary):
        super().__init__(path_to_binary)
        self.invalid_prefixes = set()
        self.error_hit_prefixes = set()

    def _checkinvalidprefixes(self, inputs):
        for i in range(len(inputs)):
            curprefix = inputs[0:i+1]
            # Check if a prefix of the current input sequence has already been invalidated
            if curprefix in self.invalid_prefixes:
                print("[Skipped - Invalid prefix]")
                self.needs_reset = False
                #self.cache[inputs] = False
                return True, False
            # Check if a prefix of the current input already hit a verifier error
            if curprefix in self.error_hit_prefixes:
                print("[Skipped - Verifier error found]")
                self.needs_reset = False
                #self.cache[inputs] = True
                return True, True
        # Or, if no cache hit:
        return False, None

    # Performs the interaction with the RERS SUT
    def _interact(self, inputs):
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

        # Or we got through the entire input string without hitting a verifier error / invalid input
        self.cache[inputs] = False
        return False


# Interacts with the compiled RERS programs,
# But returns strings instead of booleans for mealy machine learning.
class StringRERSConnector(RERSConnector):

    def __init__(self, path_to_binary):
        super().__init__(path_to_binary)
        self.invalid_prefixes = {}
        self.error_hit_prefixes = {}

    def _checkinvalidprefixes(self, inputs):
        for i in range(len(inputs)):
            curprefix = inputs[0:i+1]
            # Check if a prefix of the current input sequence has already been invalidated
            if curprefix in self.invalid_prefixes.keys():
                print("[Skipped - Invalid prefix]")
                result = self.invalid_prefixes[curprefix]
                self.needs_reset = False
                #self.cache[inputs] = result
                return True, result
            # Check if a prefix of the current input already hit a verifier error
            if curprefix in self.error_hit_prefixes.keys():
                print("[Skipped - Verifier error found]")
                result = self.error_hit_prefixes[curprefix]
                self.needs_reset = False
                #self.cache[inputs] = result
                return True, result
        # Or, if no cache hit:
        return False, None

    def _interact(self, inputs):
        # Keep track of what the last response from the SUT was
        result = None

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
                    result = self.p.match.group(0)
                    print("[OK]", prev_match.group(1))
                    print("[Verifier ERROR]", result)
                    self.error_hit_prefixes[inputs] = result
                    self.cache[inputs] = result
                    return result
                else:
                    result = prev_match.group(1)
                    print("[OK]", result)

            # We have an invalid input
            elif index == 1:
                result = "Invalid Input"
                print("[ERROR]", self.p.match.group(0))
                self.invalid_prefixes[inputs] = result
                self.cache[inputs] = result
                return result

        # Or we got through the entire input string without hitting a verifier error / invalid input
        self.cache[inputs] = result
        return result


if __name__ == "__main__":

    r = BooleanRERSConnector('../rers/TrainingSeqReachRers2019/Problem11/Problem11')
    alphabet = r.get_alphabet()

    from numpy.random import choice
    input = list(choice(alphabet, 200))
    input = ["9", "10"]
    print("Sending", input)
    result = r.process_input(input)
    print("Result:", result)

    print("DONE")
from suls.sul import SUL
from subprocess import check_output, Popen, STDOUT, PIPE
from queue import Queue, Empty
from threading import Thread
import re
import pygtrie
import hashlib
from pathlib import Path
import pickle
import os
import sys

class RERSConnectorV3(SUL):
    def __init__(self, path_to_binary, path_to_cache=None, save_every_n=100000):
        self.path = path_to_binary
        self.needs_reset = True
        self.cache = {}
        self.error_cache = pygtrie.StringTrie(separator=" ")
        self.invalid_cache = pygtrie.PrefixSet()

        # Set up external process and communication
        self.proc = Popen(path_to_binary, bufsize=0, stdout=PIPE, stdin=PIPE, stderr=STDOUT)
        self.q = Queue()
        self.t = Thread(target=self._enqueue, args=(self.proc.stdout, self.q))
        self.t.daemon = True
        self.t.start()

        # Save cache to file every n queries
        self.save_every_n = save_every_n
        self.n_queries = 0

        if path_to_cache is None:
            print("No cache path given, not using cache")
            self.cachepath = None
        else:
            print("Cache dir:", str(Path(path_to_cache).absolute()))
            # Hash the binary to find it's cache folder
            with open(self.path, 'rb') as f:
                hash = hashlib.sha256(f.read()).hexdigest()

            # Check if cache exists for the given binary
            self.cachepath = Path(path_to_cache).joinpath(hash)
            if self.cachepath.is_dir():
                self._load_cache()
            else:
                os.mkdir(self.cachepath)

    def _enqueue(self, out, queue):
        while True:
            line = out.readline()
            #print("GOT", line)
            queue.put(line)

    def _load_cache(self):
        with self.cachepath.joinpath('cache').open('rb') as f:
            try:
                self.cache = pickle.load(f)
            except EOFError:
                print("Error loading query cache")
                self.cache = {}
        with self.cachepath.joinpath('error_cache').open('rb') as f:
            self.error_cache = pickle.load(f)
        with self.cachepath.joinpath('invalid_cache').open('rb') as f:
            self.invalid_cache = pickle.load(f)

    def _save_cache(self):
        if self.cachepath == None:
            return

        print("Saving cache to file...")
        with self.cachepath.joinpath('cache').open('wb') as f:
            pickle.dump(self.cache, f)
        with self.cachepath.joinpath('error_cache').open('wb') as f:
            pickle.dump(self.error_cache, f)
        with self.cachepath.joinpath('invalid_cache').open('wb') as f:
            pickle.dump(self.invalid_cache, f)

    def _interact(self, inputs):

        self.proc.stdin.write((" ".join([str(x) for x in inputs]) + " 0 \n").encode('utf-8'))

        lines = []

        shouldstop = False
        while not shouldstop:
            out = self.q.get().decode().strip()

            if out == "Reset":
                shouldstop = True

            lines.append(out)



        return self.decode_result(lines, inputs)

    def decode_result(self, lines, inputs):
        lines += ['']

        result = None
        for idx, line in enumerate(lines):
            if len(line) > 0:
                if match := re.match("[0-9]+$", line):
                    result = match.group(0)
                elif re.match("Invalid input:", line):
                    self.invalid_cache.add(inputs[0:idx + 1])
                    result = "invalid_input"
                elif match := re.match("error_[0-9]+", line):
                    tmp = match.group(0)
                    self.error_cache[" ".join(inputs)] = tmp
                    return tmp

                if "error" not in lines[idx + 1]:
                    self.cache[inputs[0:idx + 1]] = result

        self.cache[inputs] = result

        self.n_queries += 1
        if self.n_queries % self.save_every_n == 0:
            self._save_cache()

        return result


    def process_input(self, inputs):
        inputs = tuple(inputs)


        #Check if the input is already in cache
        if inputs in self.cache.keys():
            self.needs_reset = False
            #print("[Cache hit]", inputs)
            return self.cache[inputs]

        # Check prefixes
        # if inputs in self.invalid_cache:
        #     #print("[Invalid]", inputs)
        #     return "invalid_input"

        #We need a string representing the input, actions separated with a space
        inputs_string = " ".join(inputs)
        prefix, value = self.error_cache.shortest_prefix(inputs_string)
        if prefix is not None:
            #print("[Known Error]", inputs)
            return value

        # If no cache hit, actually send the input to the SUT
        print(f"\r[Query] {inputs}", end="", flush=True)
        sys.stdout.flush()
        return self._interact(inputs)

    def reset(self):
        pass

    def get_alphabet(self):
        # Grep the source file for the line defining the input alphabet
        tmp = check_output(["grep", "-o", "int inputs\[\] \= {\(.*\)};", f"{self.path}.c"])
        # Extract it and put it into a list
        return re.search('{(.*)}', tmp.decode()).group(1).split(',')


if __name__ == "__main__":

    n = 1000

    #asyncio.run(main(n))

    path = "/home/tom/projects/lstar/rers/TrainingSeqReachRers2019/Problem11/Problem11_patched"
    r = RERSConnectorV3(path)
    alphabet = r.get_alphabet()

    from numpy.random import choice
    import time

    inputs = []
    for i in range(n):
        inputs.append(list(choice(alphabet, 10)))

    #inputs = [['9', '7', '7'], ['8', '9', '7', '7']]
    start = time.perf_counter()

    for input in inputs:
        print("Sending", input)
        result = r.process_input(input)
        print("Result:", result)

    end = time.perf_counter() - start
    print(f'Took {end:0.5f} seconds')

    print("DONE")





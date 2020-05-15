from suls.sul import SUL
import pexpect
from subprocess import check_output, CalledProcessError, STDOUT
import re
import pygtrie
import hashlib
from pathlib import Path
import pickle
import os
import asyncio

from suls.rersconnectorv4.build.connector import RERSConnectorV3 as CConnector

class RERSConnectorV3(SUL):
    def __init__(self, path_to_binary, path_to_cache=None, save_every_n=1000, terminator="0"):
        self.path = path_to_binary
        self.needs_reset = True
        self.cache = {}
        self.error_cache = pygtrie.StringTrie(separator=" ")
        self.invalid_cache = pygtrie.PrefixSet()

        self.connector = CConnector(path_to_binary)

        self.terminator = terminator
        assert terminator not in self.get_alphabet(), f"Terminator {terminator} in alphabet, please choose a different one"

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

    def _load_cache(self):
        with self.cachepath.joinpath('cache').open('rb') as f:
            self.cache = pickle.load(f)
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
        output = self.connector.interact_fast(" ".join([str(x) for x in inputs]) + " 0 ")
        self.cache[inputs] = output
        return output


    def decode_result(self, lines, inputs):

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


        # Check if the input is already in cache
        # if inputs in self.cache.keys():
        #     self.needs_reset = False
        #     #print("[Cache hit]", inputs)
        #     return self.cache[inputs]

        # # Check prefixes
        # # if inputs in self.invalid_cache:
        # #     #print("[Invalid]", inputs)
        # #     return "invalid_input"

        # We need a string representing the input, actions separated with a space
        # inputs_string = " ".join(inputs)
        # prefix, value = self.error_cache.shortest_prefix(inputs_string)
        # if prefix is not None:
        #     #print("[Known Error]", inputs)
        #     return value

        # If no cache hit, actually send the input to the SUT
        #print("[Query]", inputs)
        return self._interact(inputs)

    async def process_input_async(self, inputs):
        inputs = tuple(inputs)

        # Check if the input is already in cache
        if inputs in self.cache.keys():
            self.needs_reset = False
            # print("[Cache hit]", inputs)
            return self.cache[inputs]

        # We need a string representing the input, actions separated with a space
        inputs_string = " ".join(inputs)
        prefix, value = self.error_cache.shortest_prefix(inputs_string)
        if prefix is not None:
            # print("[Known Error]", inputs)
            return value

        return await self._interact_async(inputs)

    def reset(self):
        pass

    def get_alphabet(self):
        # Grep the source file for the line defining the input alphabet
        tmp = check_output(["grep", "-o", "int inputs\[\] \= {\(.*\)};", f"{self.path}.c"])
        # Extract it and put it into a list
        return re.search('{(.*)}', tmp.decode()).group(1).split(',')


from numpy.random import choice

async def consume(q, r):
    while True:
        input = await q.get()
        result = await r.process_input_async(input)
        print(result)
        q.task_done()

async def produce(q, n, alphabet):
    for i in range(n):
        input = list(choice(alphabet, 30))
        await q.put(input)

import time
async def main(n_queries):
    r = RERSConnectorV2('../rers/TrainingSeqReachRers2019/Problem11/Problem11')
    alphabet = r.get_alphabet()

    q = asyncio.Queue()

    producer = asyncio.create_task(produce(q, n_queries, alphabet))
    await asyncio.gather(producer)

    start = time.perf_counter()

    consumers = [asyncio.create_task(consume(q, r)) for n in range(100)]

    await q.join()
    for c in consumers:
        c.cancel()

    end = time.perf_counter() - start

    print(f'Took {end:0.5f} seconds')

    print("DONE")


if __name__ == "__main__":

    n = 10000

    #asyncio.run(main(n))

    r = RERSConnectorV2('../rers/TrainingSeqReachRers2019/Problem11/Problem11')
    alphabet = r.get_alphabet()



    from numpy.random import choice


    inputs = []
    for i in range(n):
        inputs.append(list(choice(alphabet, 1)))

    start = time.perf_counter()

    for input in inputs:
        print("Sending", input)
        result = r.process_input(input)
        print("Result:", result)

    end = time.perf_counter() - start
    print(f'Took {end:0.5f} seconds')

    print("DONE")

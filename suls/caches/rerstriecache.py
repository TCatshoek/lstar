from suls.caches.abscache import AbsCache
from suls.rersconnectorv3 import RERSConnectorV3
from suls.sul import SUL
from pygtrie import StringTrie, PrefixSet
from pathlib import Path
import pickle


# RERS specific trie cache, uses separate tries for different outcomes
# Uses a pygtrie trie as storage, slower than a dict but more memory efficient
class RersTrieCache(AbsCache):
    def __init__(self, sul: RERSConnectorV3 = None, separator=" ", storagepath=None, saveinterval=100000):
        super().__init__(sul, storagepath, saveinterval)
        self.separator = separator
        self.cache = StringTrie(separator=separator)
        self.error_cache = StringTrie(separator=separator)
        self.invalid_cache = PrefixSet()

        # hookup rers cache
        self.sul.hookup_cache(self.cache,
                              self.error_cache,
                              self.invalid_cache)

        self.passthrough = False

    def process_input(self, inputs):
        if self.passthrough:
            return self.sul.process_input(inputs)

        # The trie keys are strings using a given separator to separate the nodes
        trie_inputs = self.separator.join(inputs)

        if trie_inputs in self.cache:
            self.cachehits += 1
            return self.cache[trie_inputs]
        else:
            # Check if we have a shorter prefix that is a known error state
            prefix, output = self.error_cache.shortest_prefix(trie_inputs)
            if prefix is not None:
                return output

            # If not, it's a cache miss
            self.cachemisses += 1

            # Retrieve output and add it to the correct cache
            output = self.sul.process_input(inputs)
            if output.startswith("error"):
                self.error_cache[trie_inputs] = output
            elif output.startswith("Invalid"):
                self.invalid_cache[trie_inputs] = output
            else:
                self.cache[trie_inputs] = output

            # Save if necessary
            self.querycounter += 1
            if self.querycounter > self.saveinterval:
                self.save()
                self.querycounter = 0

            return output

    def save(self, storagepath=None):
        if storagepath is None:
            storagepath = self.storagepath

        assert storagepath is not None, "Please make sure storage path is set"

        with open(Path(storagepath).joinpath("cache.p"), "wb") as file:
            pickle.dump(self.cache, file)
        with open(Path(storagepath).joinpath("error_cache.p"), "wb") as file:
            pickle.dump(self.error_cache, file)
        with open(Path(storagepath).joinpath("invalid_cache.p"), "wb") as file:
            pickle.dump(self.invalid_cache, file)

    def load(self, storagepath):
        with open(Path(storagepath).joinpath("cache.p"), "rb") as file:
            self.cache = pickle.load(file)
        with open(Path(storagepath).joinpath("error_cache.p"), "rb") as file:
            self.error_cache = pickle.load(file)
        with open(Path(storagepath).joinpath("invalid_cache.p"), "rb") as file:
            self.invalid_cache = pickle.load(file)

        return self

    def set_passthrough(self, state):
        self.passthrough = state
        return self

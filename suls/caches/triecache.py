from suls.caches.abscache import AbsCache
from suls.sul import SUL
from pygtrie import StringTrie


# Simple cache wrapper for SULs
# Uses a pygtrie trie as storage, slower than a dict but more memory efficient
class TrieCache(AbsCache):
    def __init__(self, sul: SUL = None, separator=" ", storagepath=None, saveinterval=100000):
        super().__init__(sul, storagepath, saveinterval)
        self.cache = StringTrie(separator=separator)
        self.separator = separator

    def process_input(self, inputs):

        # The trie keys are strings using a given separator to separate the nodes
        trie_inputs = self.separator.join(inputs)

        if trie_inputs in self.cache:
            self.cachehits += 1
            return self.cache[trie_inputs]
        else:
            self.cachemisses += 1
            output = self.sul.process_input(inputs)
            self.cache[trie_inputs] = output

            self.querycounter += 1
            if self.querycounter > self.saveinterval:
                self.save()
                self.querycounter = 0

            return output
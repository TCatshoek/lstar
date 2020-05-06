from suls.caches.abscache import AbsCache


# Simple cache wrapper for SULs
# Uses a python dict as storage, fast but not very memory efficient
class DictCache(AbsCache):
    def __init__(self, sul: SUL = None, storagepath=None, saveinterval=100000):
        super().__init__(sul, storagepath, saveinterval)
        self.cache = {}

    # ---SUL wrapper methods---
    def process_input(self, inputs):
        if inputs in self.cache:
            self.cachehits += 1
            return self.cache[inputs]
        else:
            self.cachemisses += 1
            output = self.sul.process_input(inputs)
            self.cache[inputs] = output

            self.querycounter += 1
            if self.querycounter > self.saveinterval:
                self.save()
                self.querycounter = 0

            return output

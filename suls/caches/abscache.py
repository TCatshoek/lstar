import pickle
from abc import ABC
from suls.sul import SUL


# Base functionality for a cache
# Saving, loading, setting common options
class AbsCache(SUL, ABC):
    def __init__(self, sul:SUL, storagepath=None, saveinterval=None):
        # Defining instance vars like this is kinda awkward?
        # Should find a better way
        self.sul = sul
        self.cache = None
        self.storagepath = storagepath
        self.saveinterval = saveinterval

        self.cachehits = 0
        self.cachemisses = 0
        self.querycounter = 0

    def reset(self):
        self.sul.reset()

    def get_alphabet(self):
        self.sul.get_alphabet()

    def wrap_sul(self, sul):
        self.sul = sul
        return self

    def set_storage_path(self, storagepath):
        self.storagepath = storagepath
        return self

    def set_save_interval(self, saveinterval):
        self.saveinterval = saveinterval
        return self

    def save(self, storagepath=None):
        if storagepath is None:
            storagepath = self.storagepath

        assert storagepath is not None, "Please make sure storage path is set"

        with open(storagepath, "wb") as file:
            pickle.dump(self.cache, file)

    def load(self, path):
        with open(path, "rb") as file:
            self.cache = pickle.load(file)
        return self

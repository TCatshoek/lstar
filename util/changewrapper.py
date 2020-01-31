# ADAPTED FROM: https://stackoverflow.com/questions/9871169/check-if-huge-list-in-python-has-changed

# TODO: possibly incomplete
changer_methods = set("""
__setitem__ __setslice__ __delitem__ update append extend
 add insert pop popitem remove setdefault __iadd__ clear
 difference_update discard intersection_update
 symmetric_difference_update update
 """.split())

class _NotifierSet(set):
    def __init__(self, seq=()):
        super().__init__(seq)

        self.has_changed = False

    def clear_changed(self):
        self.has_changed = False

    def set_changed(self):
        self.has_changed = True

def decorator(func, callback):
    def wrapper(*args, **kw):
        callback(args[0])
        return func(*args, **kw)
    wrapper.__name__ = func.__name__
    return wrapper

new_dct = _NotifierSet.__dict__.copy()
for k, v in set.__dict__.items():
    if k in changer_methods:
        new_dct[k] = decorator(v, _NotifierSet.set_changed)

NotifierSet = type("NotifierSet", (_NotifierSet,), new_dct)

if __name__ == "__main__":
    a = NotifierSet()
    print(a.has_changed)
    a.add(1)
    print(a.has_changed)
    a.clear_changed()
    print(a.has_changed)
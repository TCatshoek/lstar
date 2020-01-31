# ADAPTED FROM: https://stackoverflow.com/questions/9871169/check-if-huge-list-in-python-has-changed

# TODO: possibly incomplete
changer_methods = set("""
__setitem__ __setslice__ __delitem__ update append extend
 add insert pop popitem remove setdefault __iadd__ clear
 difference_update discard intersection_update
 symmetric_difference_update update
 """.split())

# Keeps track of changes
class _NotifierSet(set):
    def __init__(self, seq=()):
        super().__init__(seq)

        self.change_counter = 0

    def on_changed(self):
        self.change_counter += 1

def decorator(func, callback):
    def wrapper(*args, **kw):
        callback(args[0])
        return func(*args, **kw)
    wrapper.__name__ = func.__name__
    return wrapper

new_dct = _NotifierSet.__dict__.copy()
for k, v in set.__dict__.items():
    if k in changer_methods:
        new_dct[k] = decorator(v, _NotifierSet.on_changed)

NotifierSet = type("NotifierSet", (_NotifierSet,), new_dct)

if __name__ == "__main__":
    a = NotifierSet()
    print(a.change_counter)
    a.add(1)
    print(a.change_counter)
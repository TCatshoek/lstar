
# Memoization decorator
from collections import namedtuple

from learners.learner import Learner
from teachers.teacher import Teacher
from util.changewrapper import NotifierSet


ChangeCounterPair = namedtuple('Mem', 'S E')
#
# def depends_on_S_E(func):
#     def wrapper(*args):
#
#         self = args[0]
#         change_counter_S = self.S.change_counter
#         change_counter_E = self.E.change_counter
#
#         try:
#             last_seen_S, last_seen_E = self._watch[func.__name__]
#         except KeyError:
#             self._watch[func.__name__] = ChangeCounterPair(-1, -1)
#             last_seen_S, last_seen_E = -1, -1
#
#         if (last_seen_S != change_counter_S) or (last_seen_E != change_counter_E):
#             print('cache miss')
#             tmp = func(*args)
#             self._mem[func.__name__] = tmp
#             self._watch[func.__name__] = ChangeCounterPair(change_counter_S, change_counter_E)
#             return tmp
#         else:
#             print('cache hit')
#             return self._mem[func.__name__]
#
#     return wrapper


# Memoization decorator
def depends_on_S_E(func):
    def wrapper(*args):

        self = args[0]
        change_counter_S = self.S.change_counter
        change_counter_E = self.E.change_counter

        try:
            last_seen_S, last_seen_E = self._watch[func.__name__]
        except KeyError:
            self._watch[func.__name__] = ChangeCounterPair(-1, -1)
            last_seen_S, last_seen_E = -1, -1

        if (last_seen_S != change_counter_S) or (last_seen_E != change_counter_E):
            print('cache reset')
            # If S or E changed, Invalidate memory
            self._mem[func.__name__] = {}
            self._watch[func.__name__] = ChangeCounterPair(change_counter_S, change_counter_E)

        if args in self._mem[func.__name__].keys():
            print('cache hit')
            return self._mem[func.__name__][args]
        else:
            print('cache miss')
            tmp = func(*args)
            self._mem[func.__name__][args] = tmp
            return tmp

    return wrapper

class Test:
    def __init__(self):
        # Observation table (S, E, T)
        # NotifierSets raise a flag once they're modified
        # This is used to avoid repeating expensive computations
        self.S = NotifierSet()

        # Don't redo expensive computations unless necessary
        self._mem = {}
        self._watch = {}

    @depends_on_S_E
    def sum_s_e(self):
        return sum(self.S) + sum(self.E)

if __name__ == '__main__':
    t = Test()
    print('sum', t.sum_s_e())
    t.S.add(1)
    print('sum', t.sum_s_e())
    print('sum', t.sum_s_e())
    t.E.add(1)
    print('sum', t.sum_s_e())
    print('sum', t.sum_s_e())

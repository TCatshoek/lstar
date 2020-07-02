import tempfile


from suls.mealymachine import MealyMachine, MealyState
from itertools import product, chain, combinations
from functools import reduce
from equivalencecheckers.bruteforce import BFEquivalenceChecker
from learners.learner import Learner
from teachers.teacher import Teacher
from typing import Set, Tuple, Dict, Callable, Iterable
from tabulate import tabulate
from util.changewrapper import NotifierSet
from collections import namedtuple
from pathlib import Path
import random
import string
from datetime import datetime
import pickle

ChangeCounterPair = namedtuple('Mem', 'S E')

# Memoization decorator
def depends_on_S(func):
    def wrapper(*args):

        self = args[0]
        change_counter = self.S.change_counter

        try:
            last_seen = self._watch[func.__name__]
        except KeyError:
            self._watch[func.__name__] = 0
            last_seen = 0

        if last_seen != change_counter:
            tmp = func(*args)
            self._mem[func.__name__] = tmp
            self._watch[func.__name__] = change_counter
            return tmp
        else:
            return self._mem[func.__name__]

    return wrapper

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
            # If S or E changed, Invalidate memory
            self._mem[func.__name__] = {}
            self._watch[func.__name__] = ChangeCounterPair(change_counter_S, change_counter_E)

        if args in self._mem[func.__name__].keys():
            return self._mem[func.__name__][args]
        else:
            tmp = func(*args)
            self._mem[func.__name__][args] = tmp
            return tmp

    return wrapper


# Generic memoization decorator
def memoize(f):
    memo = {}

    def wrapper(*args):
        if args not in memo:
            memo[args] = f(*args)
        return memo[args]

    return wrapper


# Implements the L* algorithm by Dana Angluin, modified for mealy machines as per
# https://link.springer.com/chapter/10.1007%2F978-3-642-05089-3_14
class ApproximateMealyLearner(Learner):
    def __init__(self, teacher: Teacher, e=0.1):
        super().__init__(teacher)

        # Observation table (S, E, T)
        # NotifierSets raise a flag once they're modified
        # This is used to avoid repeating expensive computations
        self.S = NotifierSet()
        self.E = NotifierSet()

        # S starts with the empty string
        self.S.add(tuple())

        self.T = {}
        self.T_count = {}

        # Alphabet A
        self.A = set([(x,) for x in teacher.get_alphabet()])

        # at the start, E = A
        for a in self.A:
            self.E.add(a)

        # for i in range(2, 3):
        #     for a in product(teacher.get_alphabet(), repeat=i):
        #         self.E.add(a)

        # Don't redo expensive computations unless necessary
        self._mem = {}
        self._watch = {}

        # Checkpoints?
        self._save_checkpoints = False
        self._checkpointname = None
        self._checkpointdir = None

        # Approximation error allowance
        self.e = e

        self.locked = False

    def enable_checkpoints(self, dir, checkpointname=None):
        # Try getting checkpoint name from SUL
        if checkpointname is None:
            try:
                cpn = Path(self.teacher.sul.path).stem
            except:
                cpn = ''.join([random.choice(string.ascii_letters + string.digits) for n in range(6)])
        else:
            cpn = checkpointname

        self._checkpointname = cpn
        self._save_checkpoints = True

        # Check if checkpoint dir exists
        Path(f'{dir}/{cpn}').mkdir(parents=True, exist_ok=True)
        self._checkpointdir = dir

        return self

    def make_checkpoint(self):
        state = {
            "S": self.S,
            "E": self.E,
            "T": self.T
        }

        print("Making checkpoint...")
        now = str(datetime.now()).replace(' ', '_').replace('.', ':')
        with open(Path(self._checkpointdir).joinpath(self._checkpointname + '/' + now), 'wb') as f:
            pickle.dump(state, f)

    def load_checkpoint(self, path):
        with open(path, 'rb') as f:
            state = pickle.load(f)
            for k, v in state.items():
                self.__dict__[k] = v
        return self

    # Membership query
    def query(self, query):
        if self.locked:
            return self.T[query]

        output = self.teacher.member_query(query)

        return self.process_output(query, output)

    # Keeps a cumulative moving average
    def process_output(self, query, output):
        if query in self.T.keys():
            count = self.T_count[query]
            cur_value = self.T[query]

            new_value = (output + (count * cur_value)) / (count + 1)
            self.T_count[query] += 1
            self.T[query] = new_value

            return new_value
        else:
            self.T[query] = output
            self.T_count[query] = 1
            return output

    # Calculates S·A
    #@depends_on_S
    def _SA(self):
        return set([tuple(chain.from_iterable(x)) for x in list(product(self.S, self.A))]).union(self.A)

    # Calculates S ∪ S·A
    #@depends_on_S
    def _SUSA(self) -> Set[Tuple]:
        SA = self._SA()

        #print('S·A', SA)

        return self.S.union(SA)

    def _tostr(self, actionlist):
        if len(actionlist) == 0:
            return 'λ'
        else:
            return reduce(lambda x, y: str(x) + ',' + str(y), actionlist)

    #@memoize
    def _rebuildquery(self, strquery):
        return tuple([int(a) for a in filter(lambda x: x != 'λ', strquery.split(','))])

    # row(s), s in S ∪ S·A
    #@depends_on_S_E
    def _get_row(self, s: Tuple):
        if s not in self._SUSA():
            raise Exception("s not in S ∪ S·A")

        row = [self.query(s + e) for e in self.E]

        return row

    def _get_col(self, e: Tuple):
        if e not in self.E:
            raise Exception("e not in E")

        col = [self.query(s + e) for s in self._SUSA()]

        return col

    #@depends_on_S_E
    def _is_closed(self):
        is_closed = True

        S_rows = [self._get_row(s) for s in self.S]

        for t in self._SA():
            tmp = self.approximate_in(self._get_row(t), S_rows)
            is_closed &= tmp
            if not tmp:
                print("Not closed because row", t)
                #break

        return is_closed

    def approximate_in(self, row, rows, e=None):
        if e is None:
            e = self.e

        for row2 in rows:
            if self.row_eq(row, row2, e):
                return True

        return False

    #@depends_on_S_E
    def _is_consistent(self):
        is_consistent = True

        # Gather equal rows
        #eqrows = [(s1, s2) for (s1, s2) in combinations(self.S, 2) if self._get_row(s1) == self._get_row(s2)]
        eqrows = [(s1, s2) for (s1, s2) in combinations(self.S, 2) if self.row_eq(self._get_row(s1), self._get_row(s2))]

        # Check if all these rows are still consistent after appending a
        for (s1, s2) in eqrows:
            for a in self.A:
                cur_consistent = self.row_eq(self._get_row(s1 + a), self._get_row(s2 + a))
                # if not cur_consistent:
                # print("Inconsistency found:", f'{s1},{a}', f'{s2},{a}')
                is_consistent &= cur_consistent

        return is_consistent

    def print_observationtable(self):
        # No
        #return

        rows = []

        S = sorted([str(self._tostr(a)) for a in list(self.S)])
        SA = sorted([str(self._tostr(a)) for a in list(self._SA())])
        E = sorted([str(self._tostr(e)) for e in self.E]) if len(self.E) > 0 else []

        rows.append([" ", "T"] + E)
        for s in S:
            row = ["S", s]
            for e in E:
                row.append(self.query(self._rebuildquery(f'{s},{e}')))
            rows.append(row)

        rows_sa = []
        for sa in SA:
            row = ["SA", sa]
            for e in E:
                row.append(self.query(self._rebuildquery(f'{sa},{e}')))
            rows_sa.append(row)

        print(tabulate(rows + rows_sa, headers="firstrow",tablefmt="fancy_grid"))

    def row_eq(self, row1, row2, e=None):
        if e is None:
            e = self.e

        for items in zip(row1, row2):
            try:
                diff = (max(items) / min(items)) - 1
            except ZeroDivisionError:
                return max(items) == min(items)

            if diff > e:
                return False

        return True

    def el_eq(self, el1, el2, e=None):
        if e is None:
            e = self.e

        try:
            diff = (max((el1, el2)) / min((el1, el2))) - 1
        except ZeroDivisionError:
            return max((el1, el2)) == min((el1, el2))

        if diff > e:
            return False

        return True


    def step(self):
        consistent = self._is_consistent()
        closed = self._is_closed()

        print('Closed:', closed)
        print('Consistent:', consistent)

        break_consistent = False

        if not consistent:
            # Gather equal rows
            eqrows = [(s1, s2) for (s1, s2) in combinations(self.S, 2) if self.row_eq(self._get_row(s1), self._get_row(s2))]

            # Check if T(s1·a·e) != T(s2·a·e), and add a·e to E if so.
            AE = list(product(self.A, self.E))
            for (s1, s2) in eqrows:
                for (a, e) in AE:
                    T_s1ae = self.query(s1 + a + e)
                    T_s2ae = self.query(s2 + a + e)

                    if not self.el_eq(T_s1ae, T_s2ae):
                        print('Adding', self._tostr(a + e), 'to E')
                        self.E.add(a + e)
                        break_consistent = True
                        break

                if break_consistent:
                    break

            # Rebuild observation table
            #self.print_observationtable()

        if not closed:
            # Gather all rows in S
            S_rows = [self._get_row(s) for s in self.S]

            # Find a row(s·a) that is not in [row(s) for all s in S]
            SA = product(self.S, self.A)
            for (s, a) in SA:
                row_sa = self._get_row(s + a)
                if not self.approximate_in(row_sa, S_rows):
                    self.S.add(s + a)
                    #break

        self.print_observationtable()

    def lock(self):
        self.locked = True

    def unlock(self):
        self.locked = False

    def get_closest(self, row, rows):
        distances = [self.rmse(row, other_row) for other_row in rows]
        return rows[self.argmin(distances)]

    def argmax(self, list):
        f = lambda i: list[i]
        return max(range(len(list)), key=f)

    def argmin(self, list):
        f = lambda i: list[i]
        return min(range(len(list)), key=f)

    def rmse(self, row1, row2):
        mse = 0
        for (a, b) in zip(row1, row2):
            mse += abs(a - b)**2

        mse = mse / len(row1)

        return mse**0.5

    # Builds the hypothesised dfa using the currently available information
    def build_dfa(self):
        self.lock()

        # Gather states from S
        S = self.S

        # The rows can function as index to the 'state' objects
        state_rows = set([tuple(self._get_row(s)) for s in S])
        initial_state_row = tuple(self._get_row(tuple()))


        # Generate state names for convenience
        state_names = {state_row: f's{n + 1}' for (n, state_row) in enumerate(state_rows)}

        # Build the state objects and get the initial and accepting states
        states: Dict[Tuple, MealyState] = {state_row: MealyState(state_names[state_row]) for state_row in state_rows}
        initial_state = states[initial_state_row]

        # Add the connections between states
        A = [a for (a,) in self.A]
        # Keep track of states already visited
        visited_rows = []
        for s in S:
            s_row = tuple(self._get_row(s))
            if s_row not in visited_rows:
                for a in A:
                    sa_row = tuple(self._get_row(s + (a,)))
                    if self.approximate_in(sa_row, states.keys()):
                        try:
                            next_state_row = self.get_closest(sa_row, list(state_rows))
                            cur_output = self.query(s + (a,))
                            states[s_row].add_edge(a, cur_output, states[next_state_row])
                        except:
                            # Can't add the same edge twice
                            pass
                    else:
                        print("*sad noises*")
            else:
                visited_rows.append(s_row)

        self.unlock()
        return MealyMachine(initial_state)

    def run(self, show_intermediate=False, render_options=None, on_hypothesis: Callable[[MealyMachine], None] = None) -> MealyMachine:
        self.print_observationtable()

        equivalent = False

        while not equivalent:
            self.print_observationtable()
            while not (self._is_closed() and self._is_consistent()):
                self.step()

            if self._save_checkpoints:
                self.make_checkpoint()

            # Are we equivalent?
            hypothesis = self.build_dfa()

            print("HYPOTHESIS")
            print(hypothesis)

            if on_hypothesis is not None:
                on_hypothesis(hypothesis)

            if show_intermediate:
                hypothesis.render_graph(render_options=render_options)

            equivalent, (c_output, counterexample) = self.teacher.equivalence_query(hypothesis)

            self.process_output(counterexample, c_output)

            if equivalent:
                return hypothesis

            print('COUNTEREXAMPLE', counterexample)
            hypothesis.reset()
            print('Hypothesis output:', hypothesis.process_input(counterexample))
            print('SUL output:', self.query(counterexample))

            print()

            # if not, add counterexample and prefixes to S
            for i in range(1, len(counterexample) + 1):
                self.S.add(counterexample[0:i])
            # Instead, add counterexample to E
            #self.E.add(counterexample)


if __name__ == "__main__":
    import gym
    from experiments.reinforcementlearning.approximaterandomwalk import ApproximateRandomWalkEquivalenceChecker
    from experiments.reinforcementlearning.openaigym import GymSUL

    e = 0.5

    env = gym.make('FrozenLake-v0', is_slippery=False)
    sul = GymSUL(env, n_access_samples=1, n_samples=100)

    eqc = ApproximateRandomWalkEquivalenceChecker(sul, e=e)

    teacher = Teacher(sul, eqc)

    learner = ApproximateMealyLearner(teacher, e=e)
    learner.load_checkpoint('/home/tom/projects/lstar/experiments/reinforcementlearning/testlol/qviTkw/2020-06-18_19:15:32:294680')

    learner.build_dfa().render_graph()
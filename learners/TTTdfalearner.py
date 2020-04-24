from suls.dfa import DFA, State
from itertools import product, chain, combinations
from functools import reduce
from equivalencecheckers.bruteforce import BFEquivalenceChecker
from learners.learner import Learner
from teachers.teacher import Teacher
from typing import Set, Tuple
from tabulate import tabulate

# Implements the L* algorithm by Dana Angluin
class DFALearner(Learner):
    def __init__(self, teacher: Teacher):
        super().__init__(teacher)

        # Observation table (S, E, T)
        self.S = set()
        self.E = set()

        self.S.add(tuple())
        self.E.add(tuple())

        self.T = {}

        # Alphabet A
        self.A = set([(x,) for x in teacher.get_alphabet()])

    # Membership query
    def query(self, query):
        #print("Query:", query)
        if query in self.T.keys():
            #print("Returning cached")
            return self.T[query]
        else:
            accepted = self.teacher.member_query(query)
            self.T[query] = accepted
            return accepted

    # Calculates S·A
    def _SA(self):
        return set([tuple(chain.from_iterable(x)) for x in list(product(self.S, self.A))]).union(self.A)

    # Calculates S ∪ S·A
    def _SUSA(self) -> Set[Tuple]:
        SA = self._SA()

        #print('S·A', SA)

        return self.S.union(SA)

    def _tostr(self, actionlist):
        if len(actionlist) == 0:
            return 'λ'
        else:
            return reduce(lambda x, y: str(x) + ',' + str(y), actionlist)

    def _rebuildquery(self, strquery):
        return tuple(filter(lambda x: x != 'λ', strquery.split(',')))

    # row(s), s in S ∪ S·A
    def _get_row(self, s: Tuple):
        if s not in self._SUSA():
            raise Exception("s not in S ∪ S·A")

        row = [self.query(s + e) for e in self.E]

        return row

    def _is_closed(self):
        is_closed = True

        S_rows = [self._get_row(s) for s in self.S]

        for t in self._SA():
            is_closed &= self._get_row(t) in S_rows

        return is_closed

    def _is_consistent(self):
        is_consistent = True

        # Gather equal rows
        eqrows = [(s1, s2) for (s1, s2) in combinations(self.S, 2) if self._get_row(s1) == self._get_row(s2)]

        # Check if all these rows are still consistent after appending a
        for (s1, s2) in eqrows:
            for a in self.A:
                cur_consistent = self._get_row(s1 + a) == self._get_row(s2 + a)
                # if not cur_consistent:
                # print("Inconsistency found:", f'{s1},{a}', f'{s2},{a}')
                is_consistent &= cur_consistent

        return is_consistent


    def print_observationtable(self):
        rows = []

        S = sorted([self._tostr(a) for a in list(self.S)])
        SA = sorted([self._tostr(a) for a in list(self._SA())])
        E = sorted([self._tostr(e) for e in self.E]) if len(self.E) > 0 else []

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

        print(tabulate(rows + rows_sa, headers="firstrow", tablefmt="fancy_grid"))

    def step(self):
        if not self._is_consistent():
            # Gather equal rows
            eqrows = [(s1, s2) for (s1, s2) in combinations(self.S, 2) if self._get_row(s1) == self._get_row(s2)]

            # Check if T(s1·a·e) != T(s2·a·e), and add a·e to E if so.
            AE = list(product(self.A, self.E))
            for (s1, s2) in eqrows:
                for (a, e) in AE:
                    T_s1ae = self.query(s1 + a + e)
                    T_s2ae = self.query(s2 + a + e)

                    if T_s1ae != T_s2ae:
                        print('Adding', self._tostr(a + e), 'to E')
                        self.E.add(a + e)

            # Rebuild observation table
            self.print_observationtable()

        if not self._is_closed():
            # Gather all rows in S
            S_rows = [self._get_row(s) for s in self.S]

            # Find a row(s·a) that is not in [row(s) for all s in S]
            SA = product(self.S, self.A)
            for (s, a) in SA:
                row_sa = self._get_row(s + a)
                if row_sa not in S_rows:
                    self.S.add(s + a)

            self.print_observationtable()

        print('Closed:', self._is_closed())
        print('Consistent:', self._is_consistent())

    # Builds the hypothesised dfa using the currently available information
    def build_dfa(self):
        # Gather states from S
        S = self.S

        # The rows can function as index to the 'state' objects
        state_rows = set([tuple(self._get_row(s)) for s in S])
        initial_state_row = tuple(self._get_row(tuple()))
        accepting_states_rows = set([tuple(self._get_row(s)) for s in S if self.query(s)])

        # Generate state names for convenience
        state_names = {state_row: f's{n + 1}' for (n, state_row) in enumerate(state_rows)}

        # Build the state objects and get the initial and accepting states
        states = {state_row: State(state_names[state_row]) for state_row in state_rows}
        initial_state = states[initial_state_row]
        accepting_states = [states[a_s] for a_s in accepting_states_rows]

        # Add the connections between states
        A = [a for (a,) in self.A]
        # Keep track of states already visited
        visited_rows = []
        for s in S:
            s_row = tuple(self._get_row(s))
            if s_row not in visited_rows:
                for a in A:
                    sa_row = tuple(self._get_row(s + (a,)))
                    if sa_row in states.keys():
                        try:
                            states[s_row].add_edge(a, states[sa_row])
                        except:
                            # Can't add the same edge twice
                            pass
            else:
                visited_rows.append(s_row)

        return DFA(initial_state, accepting_states)

    def run(self, show_intermediate=False) -> DFA:
        self.print_observationtable()

        equivalent = False

        while not equivalent:
            while not (self._is_closed() and self._is_consistent()):
                self.step()

            # Are we equivalent?
            hypothesis = self.build_dfa()

            print("HYPOTHESIS")
            print(hypothesis)

            if show_intermediate:
                hypothesis.render_graph("tmp")

            equivalent, counterexample = self.teacher.equivalence_query(hypothesis)

            if equivalent:
                return hypothesis

            print('COUNTEREXAMPLE', counterexample)

            # if not, add counterexample and prefixes to S
            for i in range(1, len(counterexample) + 1):
                self.S.add(counterexample[0:i])


if __name__ == "__main__":
    s1 = State('s1')
    s2 = State('s2')
    s3 = State('s3')


    s1.add_edge('a', s2)

    s2.add_edge('b', s3)

    s3.add_edge('c', s3)

    sm = DFA(s1, [s3])

    eqc = BFEquivalenceChecker(sm)

    teacher = Teacher(sm, eqc)

    learner = DFALearner(teacher)

    hyp = learner.run()


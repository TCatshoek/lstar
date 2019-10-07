from prettytable import PrettyTable
from statemachine import StateMachine, State
from itertools import product, chain, combinations
from functools import reduce
from equivalencechecker import EquivalenceChecker

class DFALearner:
    def __init__(self, alphabet, dfa: StateMachine, equivalencechecker:EquivalenceChecker):
        # Observation table (S, E, T)
        self.S = set()
        self.E = set()
        self.T = {}

        # Alphabet A
        self.A = set([(x,) for x in alphabet])

        # DFA under test
        self.dfa = dfa

        # Equivalence checker "oracle"
        self.eqc = equivalencechecker

    # Acceptance query
    def query(self, query):
        self.dfa.reset()

        if query in self.T.keys():
            return self.T[query]
        else:
            accepted = self.dfa.process_input(query)
            self.T[query] = accepted
            return accepted

    # Calculates S·A
    def _SA(self):
        if len(self.S) > 0:
            SA = set([tuple(chain.from_iterable(x)) for x in list(product(self.S, self.A))]).union(self.A)
        else:
            SA = self.A
        return SA

    # Calculates S ∪ S·A
    def _SUSA(self):
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
    def _get_row(self, s):

        s = self._tostr(self._rebuildquery(s))

        SUSA = ['λ'] + sorted([self._tostr(a) for a in list(self._SUSA())])
        if s not in SUSA:
            raise Exception("s not in S ∪ S·A")

        E = sorted([self._tostr(e) for e in self.E]) if len(self.E) > 0 else []
        E = ['λ'] + E

        row = [self.query(self._rebuildquery(f'{s},{e}')) for e in E]

        return row

    def _is_closed(self):
        is_closed = True

        # Get sorted, comma separated string representation of S
        S = ['λ'] + sorted([self._tostr(a) for a in list(self.S)])

        S_rows = [self._get_row(s) for s in S]

        for t in [self._tostr(x) for x in self._SA()]:
            is_closed &= self._get_row(t) in S_rows

        return is_closed

    def _is_consistent(self):
        is_consistent = True

        # Gather equal rows
        S = ['λ'] + sorted([self._tostr(a) for a in list(self.S)])
        eqrows = [(s1, s2) for (s1, s2) in combinations(S, 2) if self._get_row(s1) == self._get_row(s2)]

        # Check if all these rows are still consistent after appending a
        for (s1, s2) in eqrows:
            for a in [self._tostr(a) for a in self.A]:
                cur_consistent = self._get_row(f'{s1},{a}') == self._get_row(f'{s2},{a}')
                if not cur_consistent:
                    print("Inconsistency found:", f'{s1},{a}', f'{s2},{a}')
                is_consistent &= cur_consistent

        return is_consistent


    def print_observationtable(self):
        table = PrettyTable()

        # Get sorted, comma separated string representation of S ∪ S·A
        SUSA = ['λ'] + sorted([self._tostr(a) for a in list(self._SUSA())])
        table.add_column("T", SUSA)

        # Get sorted string representation of E
        E = sorted([self._tostr(e) for e in self.E]) if len(self.E) > 0 else []
        E = ['λ'] + E
        #print('E', E)

        for e in E:
            table.add_column(str(e), [self.query(self._rebuildquery(f'{s},{e}')) for s in SUSA])

        print(table)

    def step(self):
        if not self._is_consistent():

            print("Attempting to make consistent")

            # Gather equal rows
            S = ['λ'] + sorted([self._tostr(a) for a in list(self.S)])
            eqrows = [(s1, s2) for (s1, s2) in combinations(S, 2) if self._get_row(s1) == self._get_row(s2)]

            # Gather A
            A = sorted([self._tostr(a) for a in list(self.A)])

            # Gather E
            E = ['λ'] + (sorted([self._tostr(e) for e in self.E]) if len(self.E) > 0 else [])

            # Check if T(s1·a·e) != T(s2·a·e), and add a·e to E if so.
            AE = list(product(A, E))
            for (s1, s2) in eqrows:
                for (a, e) in AE:
                    T_s1ae = self.query(self._rebuildquery(f'{s1},{a},{e}'))
                    T_s2ae = self.query(self._rebuildquery(f'{s2},{a},{e}'))

                    if T_s1ae != T_s2ae:
                        print('Adding', self._tostr(self._rebuildquery(f'{a},{e}')), 'to E')
                        self.E.add(self._rebuildquery(f'{a},{e}'))

            # Rebuild observation table
            self.print_observationtable()

        if not self._is_closed():
            # Gather all rows in S
            S = ['λ'] + sorted([self._tostr(a) for a in list(self.S)])
            S_rows = [self._get_row(s) for s in S]

            # Gather A
            A = sorted([self._tostr(a) for a in list(self.A)])

            # Find a row(s·a) that is not in [row(s) for all s in S]
            SA = product(S, A)
            for (s, a) in SA:
                row_sa = self._get_row(f'{s},{a}')
                if row_sa not in S_rows:
                    self.S.add(self._rebuildquery(f'{s},{a}'))

            self.print_observationtable()

        print('Closed:', self._is_closed())
        print('Consistent:', self._is_consistent())

    # Builds the hypothesised dfa using the currently available information
    def build_dfa(self):
        # Gather states from S
        S = ['λ'] + sorted([self._tostr(a) for a in list(self.S)])

        # The rows can function as index to the 'state' objects
        state_rows = set([tuple(self._get_row(s)) for s in S])
        initial_state_row = tuple(self._get_row('λ'))
        accepting_states_rows = set([tuple(self._get_row(s)) for s in S if self.query(self._rebuildquery(s))])

        # Generate state names for convenience
        state_names = {state_row: f's{n + 1}' for (n, state_row) in enumerate(state_rows)}

        # Build the state objects and get the initial and accepting states
        states = {state_row: State(state_names[state_row]) for state_row in state_rows}
        initial_state = states[initial_state_row]
        accepting_states = [states[a_s] for a_s in accepting_states_rows]

        # Add the connections between states
        A = sorted([self._tostr(a) for a in list(self.A)])
        # Keep track of states already visited
        visited_rows = []
        for s in S:
            s_row = tuple(self._get_row(s))
            if s_row not in visited_rows:
                for a in A:
                    sa_row = tuple(self._get_row(f'{s},{a}'))
                    if sa_row in states.keys():
                        # TODO: Connections to self?
                        if s_row != sa_row:
                            try:
                                states[s_row].add_edge(a, states[sa_row])
                            except:
                                print('SKIPPING ADD', states[s_row], a, states[sa_row])
            else:
                visited_rows.append(s_row)

        return StateMachine(initial_state, accepting_states)

    def run_lstar(self):
        self.print_observationtable()

        equivalent = False

        while not equivalent:
            while not (self._is_closed() and self._is_consistent()):
                self.step()

            # Are we equivalent?
            hypothesis = self.build_dfa()

            print("HYPOTHESIS")
            print(hypothesis)

            print("ACTUAL")
            print(self.dfa)

            equivalent, counterexample = self.eqc.test_equivalence(hypothesis)

            if equivalent:
                return hypothesis

            print('COUNTER', counterexample)

            # if not, add counterexample and prefixes to S
            for i in range(1, len(counterexample)):
                self.S.add(counterexample[0:i])





if __name__ == "__main__":
    s1 = State(1)
    s2 = State(2)
    s3 = State(3)


    s1.add_edge('a', s2)

    s2.add_edge('b', s3)

    s3.add_edge('c', s1)

    sm = StateMachine(s1, [s3])

    eqc = EquivalenceChecker(sm)

    learner = DFALearner(sm.gather_alphabet(), sm, eqc)

    hyp = learner.run_lstar()

    print(hyp)


from prettytable import PrettyTable
from statemachine import StateMachine, State
from itertools import product, chain, combinations
from functools import reduce

class DFALearner:
    def __init__(self, alphabet, dfa):
        # Observation table (S, E, T)
        self.S = set()
        self.E = set()
        self.T = {}

        # Alphabet A
        self.A = set([(x,) for x in alphabet])

        # DFA under test
        self.dfa = dfa

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
            SA = set([tuple(chain.from_iterable(x)) for x in list(product(self.S, self.A))])
        else:
            SA = self.A
        return SA

    # Calculates S ∪ S·A
    def _SUSA(self):
        SA = self._SA()

        #print('S·A', SA)

        return self.S.union(SA)

    def _tostr(self, actionlist):
        return reduce(lambda x, y: str(x) + ',' + str(y), actionlist)

    def _rebuildquery(self, strquery):
        return tuple(filter(lambda x: x != 'λ', strquery.split(',')))

    # row(s), s in S ∪ S·A
    def _get_row(self, s):
        SUSA = ['λ'] + sorted([self._tostr(a) for a in list(self._SUSA())])
        if s not in SUSA:
            raise Exception("s not in S ∪ S·A")

        E = sorted([self._tostr(self.E)]) if len(self.E) > 0 else []
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
            for a in self.A:
                is_consistent &= self._get_row(f'{s1},{a}') == self._get_row(f'{s2},{a}')

        return is_consistent


    def print_observationtable(self):
        table = PrettyTable()

        # Get sorted, comma separated string representation of S ∪ S·A
        SUSA = ['λ'] + sorted([self._tostr(a) for a in list(self._SUSA())])
        table.add_column("T", SUSA)

        # Get sorted string representation of E
        E = sorted([self._tostr(self.E)]) if len(self.E) > 0 else []
        E = ['λ'] + E
        #print('E', E)

        for e in E:
            table.add_column(str(e), [self.query(self._rebuildquery(f'{s},{e}')) for s in SUSA])

        print(table)

    def step(self):
        if not self._is_consistent():

            # Gather equal rows
            S = ['λ'] + sorted([self._tostr(a) for a in list(self.S)])
            eqrows = [(s1, s2) for (s1, s2) in combinations(S, 2) if self._get_row(s1) == self._get_row(s2)]




if __name__ == "__main__":
    s1 = State(1)
    s2 = State(2)
    s3 = State(3)

    s1.add_edge('to2', s2)
    s2.add_edge('to3', s3)
    s3.add_edge('to1', s1)

    sm = StateMachine(s1, [s3])

    learner = DFALearner(sm.gather_alphabet(), sm)

    learner.print_observationtable()

    print("closed", learner._is_closed())
    print("consistent", learner._is_consistent())
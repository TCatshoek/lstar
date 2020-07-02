from itertools import product

from equivalencecheckers.wmethod import WmethodEquivalenceChecker
from suls.dfa import DFA, State
from util.distinguishingset import get_distinguishing_set
from util.transitioncover import get_state_cover_set

s1 = State('q0')
s2 = State('q1')
s3 = State('q2')

s1.add_edge('a', s2)
s1.add_edge('b', s1)
s2.add_edge('b', s2)
s2.add_edge('a', s3)
s3.add_edge('a', s3)
s3.add_edge('b', s3)


sm = DFA(s1, [s3])

sm.render_graph('example_dfa_wmethod', format='png')

hs1 = State('q0')
hs1.add_edge('a', hs1)
hs1.add_edge('b', hs1)


hyp = DFA(hs1, [])

hyp.render_graph('example_hyp_wmethod', format='png')

eqc = WmethodEquivalenceChecker(sm, m=3)
print("Counterexample: ", eqc.test_equivalence(hyp))

m = 3

acc_seqs = get_state_cover_set(hyp)
print("Access sequences:", acc_seqs)

test_seqs = []
for i in range(0, (m - len(hyp.get_states()))):
    test_seqs += list(product(sm.get_alphabet(), repeat=i+1))
print("Test seqs", test_seqs)

dist_set = get_distinguishing_set(hyp)
print("Distinguishing set:", dist_set)
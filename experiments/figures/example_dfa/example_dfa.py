from suls.dfa import State, DFA

s1 = State('q0')
s2 = State('q1')
s3 = State('q2')

s1.add_edge('a', s2)
s1.add_edge('b', s1)
s2.add_edge('b', s3)
s2.add_edge('a', s2)
s3.add_edge('a', s3)
s3.add_edge('b', s3)

dfa = DFA(s1, [s3])

dfa.render_graph('example_dfa', format='png')
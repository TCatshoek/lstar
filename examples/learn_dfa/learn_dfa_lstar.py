import tempfile

from equivalencecheckers.bruteforce import BFEquivalenceChecker
from learners.dfalearner import DFALearner
from suls.re_machine import RegexMachine
from suls.dfa import State, DFA
from teachers.teacher import Teacher

# Set up a simple state machine (S1) =a> (S2) =b> ((S3))

s1 = State('s1')
s2 = State('s2')
s3 = State('s3')

s1.add_edge('a', s2)
s2.add_edge('b', s3)

sm = DFA(s1, [s3])

# Since we are learning a DFA, we need edges for the whole alphabet in every state
s1.add_edge('b', s1)
s2.add_edge('a', s2)
s3.add_edge('a', s3)
s3.add_edge('b', s3)

s1 = State('q0')
s2 = State('q1')
s3 = State('q2')

s1.add_edge('a', s2)
s1.add_edge('b', s1)
s2.add_edge('b', s1)
s2.add_edge('a', s3)
s3.add_edge('a', s3)
s3.add_edge('b', s1)


sm = DFA(s1, [s3])

# Or use a regex to define the state machine
sm = RegexMachine('(ab)+')

# We are using the brute force equivalence checker
eqc = BFEquivalenceChecker(sm, max_depth=10)

# Set up the teacher, with the system under learning and the equivalence checker
teacher = Teacher(sm, eqc)

# Set up the learner who only talks to the teacher
learner = DFALearner(teacher)

# Get the learners hypothesis
hyp = learner.run(show_intermediate=True)

hyp.render_graph(tempfile.mktemp('.gv'))

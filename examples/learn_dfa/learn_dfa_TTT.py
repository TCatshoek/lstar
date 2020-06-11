import tempfile

from equivalencecheckers.bruteforce import BFEquivalenceChecker
from learners.TTTdfalearner import TTTDFALearner
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

# Or use a regex to define the state machine
#sm = RegexMachine('b*a+b.*')

# We are using the brute force equivalence checker
eqc = BFEquivalenceChecker(sm)

# Set up the teacher, with the system under learning and the equivalence checker
teacher = Teacher(sm, eqc)

# Set up the learner who only talks to the teacher
learner = TTTDFALearner(teacher)

# Get the learners hypothesis
hyp = learner.run()

hyp.render_graph(tempfile.mktemp('.gv'))
learner.DTree.render_graph()

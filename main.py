from learners.dfalearner import DFALearner
from equivalencecheckers.equivalencechecker import BFEquivalenceChecker
from suls.statemachine import State, StateMachine
from suls.re_machine import RegexMachine
from teachers.teacher import Teacher

# # Set up a simple state machine (S1) =a> (S2) =b> ((S3))
# s1 = State('s1')
# s2 = State('s2')
# s3 = State('s3')
#
# s1.add_edge('a', s2)
# s2.add_edge('b', s3)
#
# sm = StateMachine(s1, [s3])
#
# # Since we are learning a DFA, we need edges for the whole alphabet in every state
# s1.add_edge('b', s1)
# s2.add_edge('a', s2)
# s3.add_edge('a', s3)
# s3.add_edge('b', s3)
#
# # We are using the brute force equivalence checker
# eqc = BFEquivalenceChecker(sm)
#
# # Set up the teacher, with the system under learning and the equivalence checker
# teacher = Teacher(sm, eqc)
#
# # Set up the learner who only talks to the teacher
# learner = DFALearner(teacher)
#
# # Get the learners hypothesis
# hyp = learner.run()
#
# print('ACTUAL', sm)

# Set up a simple state machine (S1) =a> (S2) =b> ((S3))
sm = RegexMachine('(b*abb*)b*')

# We are using the brute force equivalence checker
eqc = BFEquivalenceChecker(sm, max_depth=10)

# Set up the teacher, with the system under learning and the equivalence checker
teacher = Teacher(sm, eqc)

# Set up the learner who only talks to the teacher
learner = DFALearner(teacher)

# Get the learners hypothesis
hyp = learner.run()

print('ACTUAL', sm)

hyp.render_graph('test.gv')
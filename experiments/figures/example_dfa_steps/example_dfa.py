import tempfile

from equivalencecheckers.bruteforce import BFEquivalenceChecker
from learners.dfalearner import DFALearner
from suls.dfa import State, DFA
from teachers.teacher import Teacher

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

# We are using the brute force equivalence checker
eqc = BFEquivalenceChecker(dfa)

# Set up the teacher, with the system under learning and the equivalence checker
teacher = Teacher(dfa, eqc)

# Set up the learner who only talks to the teacher
learner = DFALearner(teacher)

# First step -----------------------------------
while not (learner._is_closed() and learner._is_consistent()):
    learner.step()

hyp1 = learner.build_dfa()
hyp1.render_graph('step1', format='png')

# Find counterexample
equivalent, counterexample = learner.teacher.equivalence_query(hyp1)
print('COUNTEREXAMPLE', counterexample)

for i in range(1, len(counterexample) + 1):
    learner.S.add(counterexample[0:i])

hyp2 = learner.build_dfa()
hyp2.render_graph('step2', format='png')

learner.print_observationtable()

# second step -----------------------------------
while not (learner._is_closed() and learner._is_consistent()):
    learner.step()

hyp1 = learner.build_dfa()
hyp1.render_graph('step3', format='png')

# Find counterexample
equivalent, counterexample = learner.teacher.equivalence_query(hyp1)
print('COUNTEREXAMPLE', counterexample)

for i in range(1, len(counterexample) + 1):
    learner.S.add(counterexample[0:i])

hyp2 = learner.build_dfa()
hyp2.render_graph('step4', format='png')

# # third step -----------------------------------
# while not (learner._is_closed() and learner._is_consistent()):
#     learner.step()
#
# hyp1 = learner.build_dfa()
# hyp1.render_graph('step5', format='png')
#
# # Find counterexample
# equivalent, counterexample = learner.teacher.equivalence_query(hyp1)
# print('COUNTEREXAMPLE', counterexample)
#
# for i in range(1, len(counterexample) + 1):
#     learner.S.add(counterexample[0:i])
#
# hyp2 = learner.build_dfa()
# hyp2.render_graph('step6', format='png')
#



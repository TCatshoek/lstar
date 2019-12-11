import tempfile

from equivalencecheckers.wmethod import WmethodEquivalenceChecker
from learners.dfalearner import DFALearner
from equivalencecheckers.randomwalk import RandomWalkEquivalenceChecker
from equivalencecheckers.bruteforce import BFEquivalenceChecker
#from equivalencecheckers.rers_checker import BFEquivalenceChecker
from learners.mealylearner import MealyLearner
from suls.dfa import State, DFA
from suls.re_machine import RegexMachine
from suls.rersconnector import StringRERSConnector
from suls.rersconnectorv2 import RERSConnectorV2
from teachers.teacher import Teacher
from rers.check_result import check_result

# Try to learn a state machine for one of the RERS problems
sm = RERSConnectorV2('rers/TrainingSeqReachRers2019/Problem12/Problem12')

# We are using the brute force equivalence checker
#eqc = BFEquivalenceChecker(sm, max_depth=15)
eqc = WmethodEquivalenceChecker(sm, m=10, overshoot=6)
#eqc = RandomWalkEquivalenceChecker(sm, max_depth=30, num_samples=100000)

# Set up the teacher, with the system under learning and the equivalence checker
teacher = Teacher(sm, eqc)

# Set up the learner who only talks to the teacher
learner = MealyLearner(teacher)

# Get the learners hypothesis
hyp = learner.run(show_intermediate=True)

print("SUCCES", check_result(hyp, 'rers/TrainingSeqReachRers2019/Problem12/reachability-solution-Problem12.csv'))

hyp.render_graph(tempfile.mktemp('.gv'))

import tempfile

from equivalencecheckers.wmethod import WmethodEquivalenceChecker, RersWmethodEquivalenceChecker
from equivalencecheckers.StackedChecker import StackedChecker
from equivalencecheckers.genetic import GeneticEquivalenceChecker
from learners.mealylearner import MealyLearner

from suls.rersconnectorv3 import RERSConnectorV3
from teachers.teacher import Teacher
from rers.check_result import check_result

from util.instrumentation import CounterexampleTracker

import sys
sys.path.extend(['/home/tom/projects/lstar'])

ct = CounterexampleTracker()
#ct.load('test2')

problem = "Problem12"

cache = '../../cache'
cache = None
# Try to learn a state machine for one of the RERS problems
sm = RERSConnectorV3(f'../../rers/TrainingSeqReachRers2019/{problem}/{problem}', cache)

eqc = StackedChecker(
    GeneticEquivalenceChecker(sm, ct, pop_n=10000),
    RersWmethodEquivalenceChecker(sm, False, m=15)
)
# Store found counterexamples
eqc.onCounterexample(ct.add)

# Set up the teacher, with the system under learning and the equivalence checker
teacher = Teacher(sm, eqc)

# Set up the learner who only talks to the teacher
learner = MealyLearner(teacher)
learner.enable_checkpoints('checkpoints3')
#learner.load_checkpoint('/home/tom/projects/lstar/experiments/counterexampletracker/checkpoints2/Problem12/2020-03-31_15:27:37:164641')
# Get the learners hypothesis
hyp = learner.run(show_intermediate=True)

print("SUCCES", check_result(hyp, f'../../rers/TrainingSeqReachRers2019/{problem}/reachability-solution-{problem}.csv'))

hyp.render_graph(tempfile.mktemp('.gv'))


import tempfile

from equivalencecheckers.wmethod import WmethodEquivalenceChecker, RersWmethodEquivalenceChecker
from equivalencecheckers.StackedChecker import StackedChecker
from equivalencecheckers.genetic import GeneticEquivalenceChecker
from learners.mealylearner import MealyLearner
from suls.caches.rerstriecache import RersTrieCache

from suls.rersconnectorv4 import RERSConnectorV4
from teachers.teacher import Teacher
from rers.check_result import check_result

from util.instrumentation import CounterexampleTracker

import sys
sys.path.extend(['/home/tom/projects/lstar'])

ct = CounterexampleTracker()
ct.load(f'counterexamples_{problem}.p')

problem = "Problem12"

cache = '../../cache/problem12_genetic'
#cache = None
# Try to learn a state machine for one of the RERS problems
sul = RersTrieCache(
    RERSConnectorV4(f'../../rers/TrainingSeqReachRers2019/{problem}/{problem}'),
    storagepath=cache
)#.load(cache)

eqc = StackedChecker(
    GeneticEquivalenceChecker(sul, ct, pop_n=10000),
    RersWmethodEquivalenceChecker(sul, False, m=15)
)
# Store found counterexamples
def onct(ctex):
    ct.add(ctex)
    ct.save(f'counterexamples_{problem}.p')
eqc.onCounterexample(onct)

# Set up the teacher, with the system under learning and the equivalence checker
teacher = Teacher(sul, eqc)

# Set up the learner who only talks to the teacher
learner = MealyLearner(teacher)
learner.enable_checkpoints('checkpoints3')
learner.load_checkpoint('/home/tom/projects/lstar/experiments/counterexampletracker/checkpoints3/cZsmSu/2020-05-06_20:00:33:790987')
# Get the learners hypothesis
hyp = learner.run(show_intermediate=True)

print("SUCCES", check_result(hyp, f'../../rers/TrainingSeqReachRers2019/{problem}/reachability-solution-{problem}.csv'))

hyp.render_graph(tempfile.mktemp('.gv'))

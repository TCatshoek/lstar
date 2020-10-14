
import tempfile

from equivalencecheckers.wmethod import WmethodEquivalenceChecker, RersWmethodEquivalenceChecker, \
    SmartWmethodEquivalenceChecker, SmartWmethodEquivalenceCheckerV2, SmartWmethodEquivalenceCheckerV4
from equivalencecheckers.StackedChecker import StackedChecker
from equivalencecheckers.genetic import GeneticEquivalenceChecker
from learners.TTTmealylearner import TTTMealyLearner
from learners.mealylearner import MealyLearner
from suls.caches.rerstriecache import RersTrieCache

from suls.rersconnectorv4 import RERSConnectorV4
from suls.rerssoconnector import RERSSOConnector
from teachers.teacher import Teacher
from rers.check_result import check_result

from util.instrumentation import CounterexampleTracker

import sys

from util.statstracker import StatsTracker

sys.path.extend(['/home/tom/projects/lstar'])

# Try to learn a state machine for one of the RERS problems
problem = "Problem13"
problemset = "TrainingSeqReachRers2019"

ct = CounterexampleTracker()
#ct.load(f'counterexamples_{problem}.p')

# Setup logging
statstracker = StatsTracker({
    'membership_query': 0,
    'equivalence_query': 0,
    'test_query': 0,
    'state_count': 0,
    'error_count': 0,
    'errors': set()
},
    log_path=f'{problem}_mutating.log',
    write_on_change={'errors'}
)

sul = RERSSOConnector(f"../../../rers/{problemset}/{problem}/{problem}.so")

eqc = StackedChecker(
    GeneticEquivalenceChecker(sul, ct, pop_n=10000),
    SmartWmethodEquivalenceCheckerV4(sul,
                                     horizon=12,
                                     stop_on={'invalid_input'},
                                     stop_on_startswith={'error'},
                                     order_type='ce count')
)
# Store found counterexamples
def onct(ctex):
    ct.add(ctex)
    ct.save(f'counterexamples_{problem}.p')
eqc.onCounterexample(onct)

# Set up the teacher, with the system under learning and the equivalence checker
teacher = Teacher(sul, eqc)

# Set up the learner who only talks to the teacher
learner = TTTMealyLearner(teacher)
#learner.enable_checkpoints('checkpoints3')
#learner.load_checkpoint('/home/tom/projects/lstar/experiments/counterexampletracker/checkpoints3/cZsmSu/2020-05-06_20:00:33:790987')
# Get the learners hypothesis
hyp = learner.run(
    show_intermediate=False,
    render_options={'ignore_self_edges': ['error', 'invalid']},
    on_hypothesis=lambda x: check_result(x, f'../../../rers/TrainingSeqReachRers2019/{problem}/reachability-solution-{problem}.csv')
)

print("SUCCES", check_result(hyp, f'../../../rers/TrainingSeqReachRers2019/{problem}/reachability-solution-{problem}.csv'))

hyp.render_graph(render_options={'ignore_self_edges': ['error', 'invalid']})

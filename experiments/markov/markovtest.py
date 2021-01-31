import tempfile
from pathlib import Path

from equivalencecheckers.markovequivalencechecker import MarkovEquivalenceChecker
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

from util.savehypothesis import savehypothesis
from util.statstracker import StatsTracker

sys.path.extend(['/home/tom/projects/lstar'])

horizon = 6

problem = "Problem13"
prefix = f"wmethod{horizon}markov"
problemset = "TrainingSeqReachRers2019"

ct = CounterexampleTracker()

logdir = Path(f'./{prefix}/logs/{problemset}')
logdir.mkdir(parents=True, exist_ok=True)

# Setup logging
statstracker = StatsTracker({
    'membership_query': 0,
    'equivalence_query': 0,
    'test_query': 0,
    'state_count': 0,
    'error_count': 0,
    'errors': set()
},
    log_path=logdir.joinpath(f'{problem}.log'),
    write_on_change={'state_count', 'error_count'}
)

sul = RERSSOConnector(f"../../rers/{problemset}/{problem}/{problem}.so")

eqc = StackedChecker(
    MarkovEquivalenceChecker(sul, ct),
    SmartWmethodEquivalenceCheckerV4(sul,
                                     horizon=horizon,
                                     stop_on={'invalid_input'},
                                     stop_on_startswith={'error'},
                                     order_type='ce count')
)


# Store found counterexamples
ctpath = Path(f'./{prefix}/counterexamples')
ctpath.mkdir(exist_ok=True, parents=True)
def onct(ctex):
    ct.add(ctex)
    ct.save(ctpath.joinpath(f'counterexamples_{problem}.p'))
eqc.onCounterexample(onct)

# Set up the teacher, with the system under learning and the equivalence checker
teacher = Teacher(sul, eqc)

# Set up the learner who only talks to the teacher
learner = TTTMealyLearner(teacher)
# learner.enable_checkpoints('checkpoints3')
# learner.load_checkpoint('/home/tom/projects/lstar/experiments/counterexampletracker/checkpoints3/cZsmSu/2020-05-06_20:00:33:790987')

def stack(*args):
    def chained(hypothesis):
        for function in args:
            function(hypothesis)
    return chained

# Get the learners hypothesis
hyp = learner.run(
    show_intermediate=False,
    render_options={'ignore_self_edges': ['error', 'invalid']},
    on_hypothesis=stack(
        savehypothesis(f'{prefix}/hypotheses/{problemset}/{problem}', f'{problem}'),
        lambda x: check_result(x, f'../../rers/TrainingSeqReachRers2019/{problem}/reachability-solution-{problem}.csv')
    )
)

print("SUCCES", check_result(hyp, f'../../rers/TrainingSeqReachRers2019/{problem}/reachability-solution-{problem}.csv'))

#hyp.render_graph(render_options={'ignore_self_edges': ['error', 'invalid']})

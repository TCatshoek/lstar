import sys

from equivalencecheckers.genetic import GeneticEquivalenceChecker
from equivalencecheckers.nusmv import NuSMVEquivalenceChecker
#
# sys.path.extend(['/home/tom/projects/lstar'])
# import os
# os.chdir('/home/tom/projects/lstar/experiments/rers')
#
# print(os.getcwd())

from pathlib import Path
from equivalencecheckers.AFLequivalencecheckerV2 import AFLEquivalenceCheckerV2, EQCheckType
from equivalencecheckers.StackedChecker import StackedChecker
from equivalencecheckers.wmethod import SmartWmethodEquivalenceCheckerV2, SmartWmethodEquivalenceCheckerV4
from learners.TTTmealylearner import TTTMealyLearner
from rers.check_result import check_result
from suls.rerssoconnector import RERSSOConnector
from teachers.teacher import Teacher
from util.instrumentation import CounterexampleTracker
from util.statstracker import StatsTracker, count_hypothesis_stats
from util.savehypothesis import savehypothesis
from util.mealy2nusmv import mealy2nusmv_withintermediate, rersltl2smv_withintermediate
from datetime import datetime
from util.nusmv import NuSMVUtils
import argparse


horizon = 12
run_start = datetime.now().strftime('%Y-%m-%d_%H:%M:%S')

problem = 'Problem19'
problemset = "SeqReachabilityRers2019"
prefix = "wmethod12"

path = f"../../rers/{problemset}/{problem}/{problem}.so"

now = datetime.now().strftime('%Y-%m-%d_%H:%M:%S')

logdir = Path(f'./{prefix}/logs/{problemset}')
logdir.mkdir(parents=True, exist_ok=True)

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

sul = RERSSOConnector(path)

ct = CounterexampleTracker()

eqc = StackedChecker(
    #GeneticEquivalenceChecker(sul, ct, pop_n=10000),
    SmartWmethodEquivalenceCheckerV4(sul,
                                     horizon=horizon,
                                     stop_on={'invalid_input'},
                                     stop_on_startswith={'error'},
                                     order_type="ce count")
)

# Store found counterexamples
ctpath = Path(f'{prefix}/counterexamples')
ctpath.mkdir(exist_ok=True, parents=True)
def onct(ctex):
    ct.add(ctex)
    ct.save(ctpath.joinpath(f'counterexamples_{problem}.p'))
eqc.onCounterexample(onct)

# Set up the teacher, with the system under learning and the equivalence checker
teacher = Teacher(sul, eqc)

# Set up the learner who only talks to the teacher
learner = TTTMealyLearner(teacher)

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
        lambda h: check_result(h, f'../../rers/{problemset}/{problem}/constraints-solution-{problem}.txt')
    )
)

statstracker.write_log()

hyp.render_graph(render_options={'ignore_self_edges': ['error', 'invalid']})
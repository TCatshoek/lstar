import sys
sys.path.extend(['/home/tom/projects/lstar'])
import os
os.chdir('/home/tom/projects/lstar/experiments/learningfuzzing')

print(os.getcwd())

from pathlib import Path
from equivalencecheckers.AFLequivalencecheckerV2 import AFLEquivalenceCheckerV2
from equivalencecheckers.StackedChecker import StackedChecker
import tempfile
from equivalencecheckers.wmethod import WmethodEquivalenceChecker, RersWmethodEquivalenceChecker, \
    SmartWmethodEquivalenceChecker, SmartWmethodEquivalenceCheckerV2
from learners.TTTmealylearner import TTTMealyLearner
from suls.rerssoconnector import RERSSOConnector
from teachers.teacher import Teacher
from util.mealy2nusmv import  mealy2nusmv_withintermediate, rersltl2smv_withintermediate
from util.statstracker import StatsTracker, count_hypothesis_stats
from util.savehypothesis import savehypothesis
from datetime import datetime
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("problemset", help="the folder containing the rers problems, e.g. SeqLtlRers2020")
parser.add_argument("problem", help="the rers problem to be targeted, e.g. Problem1")
parser.add_argument("--horizon", type=int, help="w-method horizon")
args = parser.parse_args()

problem = args.problem
problemset = args.problemset
# problem = 'Problem11'
# problemset = 'TrainingSeqReachRers2019'
path = f"../../rers/{problemset}/{problem}/{problem}.so"

horizon = 12
if args.horizon:
    horizon = int(args.horizon)

now = datetime.now().strftime('%Y-%m-%d_%H:%M:%S')

logdir = Path(f'./logs/{problem}_afl_wtraces')
logdir.mkdir(parents=True, exist_ok=True)

statstracker = StatsTracker({
    'membership_query': 0,
    'equivalence_query': 0,
    'test_query': 0,
    'state_count': 0,
    'error_count': 0,
    'errors': set()
},
    log_path=logdir.joinpath(f'{problem}_{now}_afl_wtraces.log'),
    write_on_change={'state_count', 'error_count'}
)

sul = RERSSOConnector(path)
afl_dir = f'/home/tom/projects/lstar/experiments/learningfuzzing/{problemset}/{problem}'
bin_path = f'/home/tom/projects/lstar/experiments/learningfuzzing/{problemset}/{problem}/{problem}'

eqc = StackedChecker(
    AFLEquivalenceCheckerV2(sul, afl_dir, bin_path, feedback='w_traces'),
    SmartWmethodEquivalenceCheckerV2(sul,
                                     horizon=horizon,
                                     stop_on={'invalid_input'},
                                     stop_on_startswith={'error'})
)

# Set up the teacher, with the system under learning and the equivalence checker
teacher = Teacher(sul, eqc)

# Set up the learner who only talks to the teacher
learner = TTTMealyLearner(teacher)

# Get the learners hypothesis
hyp = learner.run(
    show_intermediate=False,
    render_options={'ignore_self_edges': ['error', 'invalid']},
    on_hypothesis=savehypothesis(f'hypotheses/afl_plain/{problem}', f'{problem}')
)


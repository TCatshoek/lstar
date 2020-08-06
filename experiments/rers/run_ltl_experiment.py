import sys
sys.path.extend(['/home/tom/projects/lstar'])
import os
os.chdir('/home/tom/projects/lstar/experiments/rers')

print(os.getcwd())

from pathlib import Path
from equivalencecheckers.AFLequivalencecheckerV2 import AFLEquivalenceCheckerV2, EQCheckType
from equivalencecheckers.StackedChecker import StackedChecker
from equivalencecheckers.wmethod import SmartWmethodEquivalenceCheckerV2
from learners.TTTmealylearner import TTTMealyLearner
from suls.rerssoconnector import RERSSOConnector
from teachers.teacher import Teacher
from util.statstracker import StatsTracker, count_hypothesis_stats
from util.savehypothesis import savehypothesis
from util.mealy2nusmv import mealy2nusmv_withintermediate, rersltl2smv_withintermediate
from datetime import datetime
from util.nusmv import NuSMVUtils
import argparse

# parser = argparse.ArgumentParser()
# parser.add_argument("problemset", help="the folder containing the rers problems, e.g. SeqLtlRers2020")
# parser.add_argument("problem", help="the rers problem to be targeted, e.g. Problem1")
# parser.add_argument("afl_dir", help="the directory containing the fuzzed rers problems")
# parser.add_argument("--horizon", type=int, help="w-method horizon")
# args = parser.parse_args()
#
# problem = args.problem
# problemset = args.problemset
afl_basedir = '/home/tom/afl/2020_ltl'
problem = 'Problem1'
problemset = 'SeqLtlRers2020'
#problemset = 'TrainingSeqLtlRers2020'

path = f"../../rers/{problemset}/{problem}/{problem}.so"

horizon = 1
# if args.horizon:
#     horizon = int(args.horizon)

now = datetime.now().strftime('%Y-%m-%d_%H:%M:%S')

logdir = Path(f'./logs/{problem}_ltl')
logdir.mkdir(parents=True, exist_ok=True)

statstracker = StatsTracker({
    'membership_query': 0,
    'equivalence_query': 0,
    'test_query': 0,
    'state_count': 0,
    'error_count': 0,
    'errors': set()
},
    log_path=logdir.joinpath(f'{problem}_{now}_ltl.log'),
    write_on_change={'state_count', 'error_count'}
)

sul = RERSSOConnector(path)
# afl_dir = f'{args.afl_dir}/{problemset}/{problem}'
# bin_path = f'{args.afl_dir}/{problemset}/{problem}/{problem}'
afl_dir = f'{afl_basedir}/{problemset}/{problem}'
bin_path = f'{afl_basedir}/{problemset}/{problem}/{problem}'
eqc = StackedChecker(
    AFLEquivalenceCheckerV2(sul, afl_dir, bin_path, eqchecktype=EQCheckType.BOTH),
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
    on_hypothesis=savehypothesis(f'hypotheses/ltl/{problem}', f'{problem}')
)

constrpath = f'/home/tom/projects/lstar/rers/{problemset}/{problem}/constraints-{problem}.txt'
mappingpath = f'/home/tom/projects/lstar/rers/{problemset}/{problem}/{problem}_alphabet_mapping_C_version.txt'

nusmv = NuSMVUtils(constrpath, mappingpath)

result = nusmv.run_ltl_check(hyp)

print(result)

#
# mealy_lines = mealy2nusmv_withintermediate(hyp)
# ltl_lines = rersltl2smv_withintermediate(constrpath, mappingpath)
#
# smvdir = Path(f'./smv/{problemset}')
# smvdir.mkdir(parents=True, exist_ok=True)
#
# with open(smvdir.joinpath(f'{problem}.smv'), 'w') as file:
#     file.writelines(mealy_lines)
#
#     # file.writelines(ltl_lines)
#     # somehow writelines only writes the first line??
#
#     for line in ltl_lines:
#         file.write(f'{line}\n')

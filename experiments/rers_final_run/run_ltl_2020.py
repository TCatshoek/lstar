import sys

from equivalencecheckers.libfuzzerequivalencechecker import LibFuzzerEquivalenceChecker
from equivalencecheckers.nusmv import NuSMVEquivalenceChecker

#sys.path.extend(['/home/tom/projects/lstar'])
#import os
#os.chdir('/home/tom/projects/lstar/experiments/rers')

#print(os.getcwd())

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


problems = ['Problem9']
problemset = 'TrainingSeqLtlRers2020'
problemset = 'SeqLtlRers2020'
horizon = 3

scores = []
times = []

for problem in problems:

    logdir = Path(f'./logs/{problemset}')
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
    start = datetime.now()

    from rers.check_ltl_result import check_result

    constrpath = f'/home/tom/projects/lstar/rers/{problemset}/{problem}/constraints-{problem}.txt'
    mappingpath = f'/home/tom/projects/lstar/rers/{problemset}/{problem}/{problem}_alphabet_mapping_C_version.txt'

    if '2020' in problemset or problemset == 'SeqLtlRers2019':
        solutionspath = f'/home/tom/projects/lstar/rers/{problemset}/{problem}/constraints-solution-{problem}.txt'
    else:
        solutionspath = f'/home/tom/projects/lstar/rers/{problemset}/{problem}/constraints-solution.csv'

    path = f"../../rers/{problemset}/{problem}/{problem}.so"
    sul = RERSSOConnector(path)

    fuzzerpath = Path(f'/home/tom/projects/lstar/libfuzzer/{problemset}/{problem}')

    eqc = StackedChecker(
        SmartWmethodEquivalenceCheckerV2(sul,
                                         horizon=1,
                                         stop_on={'invalid_input'},
                                         stop_on_startswith={'error'}),
        LibFuzzerEquivalenceChecker(sul,
                                    corpus_path=Path(fuzzerpath).joinpath("corpus"),
                                    fuzzer_path=Path(fuzzerpath).joinpath(f'{problem}_fuzz')),
        NuSMVEquivalenceChecker(sul, constrpath, mappingpath,
                                n_unrolls=1000,
                                enable_dtraces=True),
        SmartWmethodEquivalenceCheckerV2(sul,
                                         horizon=horizon,
                                         stop_on={'invalid_input'},
                                         stop_on_startswith={'error'}),

    )

    # Set up the teacher, with the system under learning and the equivalence checker
    teacher = Teacher(sul, eqc)

    # Set up the learner who only talks to the teacher
    learner = TTTMealyLearner(teacher)

    # Get the learners hypothesis
    hyp = learner.run(
        show_intermediate=False,
        on_hypothesis=savehypothesis(f'hypotheses/{problemset}/{problem}', f'{problem}')
    )

    end_learning = datetime.now()

    # hyp.render_graph()

    nusmv = NuSMVUtils(constrpath, mappingpath)

    ltl_answers = nusmv.run_ltl_check(hyp)

    if 'Training' in problemset or problemset == 'SeqLtlRers2019':
        scores.append(check_result(ltl_answers, solutionspath))

    Path(f'results/{problemset}').mkdir(exist_ok=True, parents=True)

    problem_number = problem.replace('Problem', '')

    # write nusmv results
    with open(f'results/{problemset}/{problem}.csv', 'w') as f:
        for i, r in enumerate(ltl_answers):
            f.write(f'{problem_number}, {i}, {r[1]}\n')

    end = datetime.now()

    print('Learning time', end_learning - start)
    print('Checking time', end - end_learning)
    print('Total time', end - start)
    times.append(end - start)

print("-------RESULTS-------")
for problem, (correct, total), total_time in zip(problems, scores, times):
    print(f'{problem}: {correct}/{total} - {total_time}')

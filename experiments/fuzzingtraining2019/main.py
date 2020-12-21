from datetime import datetime
from pathlib import Path

from equivalencecheckers.AFLequivalencecheckerV2 import AFLEquivalenceCheckerV2
from equivalencecheckers.libfuzzerequivalencechecker import LibFuzzerEquivalenceChecker, EQCheckType
from equivalencecheckers.nusmv import NuSMVEquivalenceChecker
from learners.TTTmealylearner import TTTMealyLearner
from rers.check_result import check_result
from suls.rerssoconnector import RERSSOConnector
from teachers.teacher import Teacher
from util.savehypothesis import savehypothesis
from util.statstracker import StatsTracker

problem = 'Problem13'
problemset = 'TrainingSeqReachRers2019'

so_path = f"../../rers/{problemset}/{problem}/{problem}.so"

now = datetime.now().strftime('%Y-%m-%d_%H:%M:%S')

logdir = Path(f'./logs/{problem}')
logdir.mkdir(parents=True, exist_ok=True)

statstracker = StatsTracker({
    'membership_query': 0,
    'equivalence_query': 0,
    'test_query': 0,
    'state_count': 0,
    'error_count': 0,
    'errors': set()
},
    log_path=logdir.joinpath(f'{problem}_{now}.log'),
    write_on_change={'state_count', 'error_count'}
)

sul = RERSSOConnector(so_path)

basepath = Path("/home/tom/afl/thesis_benchmark_3/libFuzzer/").joinpath(problemset).joinpath(problem)
corpus_path = basepath.joinpath("corpus")
fuzzer_path = basepath.joinpath(f"{problem}_fuzz")
eqc = LibFuzzerEquivalenceChecker(sul,
                                  corpus_path=corpus_path,
                                  fuzzer_path=fuzzer_path,
                                  eqchecktype=EQCheckType.BOTH,
                                  enable_dtraces=False,
                                  minimize=False)

# Set up the teacher, with the system under learning and the equivalence checker
teacher = Teacher(sul, eqc)

# Set up the learner who only talks to the teacher
learner = TTTMealyLearner(teacher)

# Get the learners hypothesis
hyp = learner.run(
    show_intermediate=False,
    render_options={'ignore_self_edges': ['error', 'invalid']},
    on_hypothesis=savehypothesis(f'hypotheses/{problem}', f'{problem}')
)

hyp.render_graph(render_options={'ignore_self_edges': ['error', 'invalid']})
check_result(hyp, f'../../rers/{problemset}/{problem}/reachability-solution-{problem}.csv')
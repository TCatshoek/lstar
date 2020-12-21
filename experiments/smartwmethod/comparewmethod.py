import tempfile

from equivalencecheckers.accseqfuzzer import AccSeqFuzzer
from equivalencecheckers.wmethod import WmethodEquivalenceChecker, RersWmethodEquivalenceChecker, \
    SmartWmethodEquivalenceChecker, SmartWmethodEquivalenceCheckerV2, WmethodHorizonEquivalenceChecker, \
    SmartWmethodEquivalenceCheckerV3, SmartWmethodEquivalenceCheckerV4
from learners.TTTmealylearner import TTTMealyLearner
from suls.caches.rerstriecache import RersTrieCache
from suls.rersconnectorv4 import RERSConnectorV4
from suls.rerssoconnector import RERSSOConnector
from teachers.teacher import Teacher
from rers.check_result import check_result

# Try to learn a state machine for one of the RERS problems
# Problem 11 is the easiest training problem
from util.statstracker import StatsTracker

problem = "Problem11"
problemset = 'TrainingSeqReachRers2019'
problem_path = path = f"../../rers/{problemset}/{problem}/{problem}.so"

type = 'smart'
horizon = 12

# Setup logging
statstracker = StatsTracker({
    'membership_query': 0,
    'equivalence_query': 0,
    'test_query': 0,
    'state_count': 0,
    'error_count': 0,
    'errors': set()
},
    log_path=f'{problem}_{type}_{horizon}.log',
    write_on_change={'errors', 'state_count', 'equivalence_query'}
)

sul = RERSSOConnector(problem_path)

# We use a specialized W-method equivalence checker which features
# early stopping on invalid inputs, which speeds things up a lot
if type == 'smart':
    eqc = SmartWmethodEquivalenceCheckerV4(sul,
                                         horizon=horizon,
                                         stop_on={'invalid_input'},
                                         stop_on_startswith={'error'},
                                         order_type='ce count')
else:
    eqc = WmethodHorizonEquivalenceChecker(sul, horizon)


#eqc = AccSeqFuzzer(sul, depth=100, num_samples=1000)
# Set up the teacher, with the system under learning and the equivalence checker
teacher = Teacher(sul, eqc)

# Set up the learner who only talks to the teacher
# We let it save checkpoints of every intermediate hypothesis
learner = TTTMealyLearner(teacher)#.enable_checkpoints("checkpoints")

# Get the learners hypothesis
hyp = learner.run(
    show_intermediate=False,
    render_options={'ignore_self_edges': ['error', 'invalid']},
    on_hypothesis=lambda x: check_result(x, f'../../rers/TrainingSeqReachRers2019/{problem}/reachability-solution-{problem}.csv')
)

statstracker.write_log()

print("SUCCES", check_result(hyp, f'../../rers/TrainingSeqReachRers2019/{problem}/reachability-solution-{problem}.csv'))

hyp.render_graph(render_options={'ignore_self_edges': ['error', 'invalid']})


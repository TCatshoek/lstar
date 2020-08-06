
import tempfile

from equivalencecheckers.wmethod import WmethodEquivalenceChecker, RersWmethodEquivalenceChecker, \
    SmartWmethodEquivalenceChecker, SmartWmethodEquivalenceCheckerV2
from learners.TTTmealylearner import TTTMealyLearner
from learners.dfalearner import DFALearner
from equivalencecheckers.randomwalk import RandomWalkEquivalenceChecker
from equivalencecheckers.bruteforce import BFEquivalenceChecker
#from equivalencecheckers.rers_checker import BFEquivalenceChecker
from equivalencecheckers.entropy import EntropyEquivalanceChecker
from learners.mealylearner import MealyLearner
from suls.caches.rerstriecache import RersTrieCache
from suls.caches.triecache import TrieCache
from suls.dfa import State, DFA
from suls.re_machine import RegexMachine
from suls.rersconnector import StringRERSConnector
from suls.rersconnectorv3 import RERSConnectorV3
from suls.rersconnectorv4 import RERSConnectorV4
from suls.rerssoconnector import RERSSOConnector
from teachers.teacher import Teacher
from rers.check_result import check_result
from util.mealy2nusmv import  mealy2nusmv_withintermediate, rersltl2smv_withintermediate

from util.statstracker import StatsTracker

problem = "Problem12"
problemset = "SeqReachabilityRers2020"
path = f"/home/tom/projects/lstar/rers/{problemset}/{problem}/{problem}.so"


statstracker = StatsTracker({
    'membership_query': 0,
    'equivalence_query': 0,
    'test_query': 0,
    'state_count': 0,
    'error_count': 0,
    'errors': set()
},
    log_path=f'{problem}.log',
    write_on_change={'errors'}
)


# sul = RERSSOConnector(f'rers/TrainingSeqReachRers2019/{problem}/{problem}.so')
#sul = RERSConnectorV3(f'rers/TrainingSeqReachRers2019/{problem}/{problem}', 'cache')
sul = RERSSOConnector(path)

eqc = SmartWmethodEquivalenceCheckerV2(sul,
                                     horizon=12,
                                     stop_on={'invalid_input'},
                                     stop_on_startswith={'error'})

# Set up the teacher, with the system under learning and the equivalence checker
teacher = Teacher(sul, eqc)

# Set up the learner who only talks to the teacher
learner = TTTMealyLearner(teacher)
#learner.load_checkpoint('checkpoints/Problem12/2020-03-09_22:50:47:638270')

# Get the learners hypothesis
hyp = learner.run(
    show_intermediate=True,
    render_options={'ignore_self_edges': ['error', 'invalid']}
    #on_hypothesis=lambda x: check_result(x, f'rers/TrainingSeqReachRers2019/{problem}/reachability-solution-{problem}.csv')
)
#print("SUCCES", check_result(hyp, f'rers/TrainingSeqReachRers2019/{problem}/reachability-solution-{problem}.csv'))

hyp.render_graph(tempfile.mktemp('.gv'), render_options={'ignore_self_edges': ['error', 'invalid']})

constrpath = f'/home/tom/projects/lstar/rers/{problemset}/{problem}/constraints-{problem}.txt'
mappingpath = f'/home/tom/projects/lstar/rers/{problemset}/{problem}/{problem}_alphabet_mapping_C_version.txt'
mealy_lines = mealy2nusmv_withintermediate(hyp, None)
ltl_lines = rersltl2smv_withintermediate(constrpath, mappingpath)

with open('test.smv', 'w') as file:
    file.writelines(mealy_lines)
    file.writelines(ltl_lines)
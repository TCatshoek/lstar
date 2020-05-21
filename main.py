
import tempfile

from equivalencecheckers.wmethod import WmethodEquivalenceChecker, RersWmethodEquivalenceChecker
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
from teachers.teacher import Teacher
from rers.check_result import check_result

problem = "Problem12"

cache = f'cache/{problem}'
#cache = None

# Try to learn a state machine for one of the RERS problems
sul = RersTrieCache(
    RERSConnectorV4(f'rers/TrainingSeqReachRers2019/{problem}/{problem}'),
    storagepath=cache
)

#sul = RERSConnectorV3(f'rers/TrainingSeqReachRers2019/{problem}/{problem}', 'cache')

eqc = RersWmethodEquivalenceChecker(sul, False, m=15)

# Set up the teacher, with the system under learning and the equivalence checker
teacher = Teacher(sul, eqc)

# Set up the learner who only talks to the teacher
learner = MealyLearner(teacher).enable_checkpoints("checkpoints")
#learner.load_checkpoint('checkpoints/Problem12/2020-03-09_22:50:47:638270')

# Get the learners hypothesis
hyp = learner.run(show_intermediate=True)

import pickle
pickle.dump(hyp, open('hyp.p', 'wb'))

print("SUCCES", check_result(hyp, f'rers/TrainingSeqReachRers2019/{problem}/reachability-solution-{problem}.csv'))

hyp.render_graph(tempfile.mktemp('.gv'))


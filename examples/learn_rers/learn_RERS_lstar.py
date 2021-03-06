import tempfile

from equivalencecheckers.wmethod import WmethodEquivalenceChecker, RersWmethodEquivalenceChecker, \
    SmartWmethodEquivalenceChecker
from learners.TTTmealylearner import TTTMealyLearner
from learners.mealylearner import MealyLearner
from suls.caches.rerstriecache import RersTrieCache
from suls.rersconnectorv4 import RERSConnectorV4
from teachers.teacher import Teacher
from rers.check_result import check_result

# Try to learn a state machine for one of the RERS problems
# Problem 11 is the easiest training problem
problem = "Problem12"

# Since we are interacting with a real system, we will want to cache
# the responses so we don't unnecessarily repeat expensive queries
cache = f'cache/{problem}'
# The query caches are implemented as wrappers around the SUL classes
# they work transparently and only catch queries that have been asked previously
sul = RersTrieCache(
    RERSConnectorV4(f'../../rers/TrainingSeqReachRers2019/{problem}/{problem}'),
    storagepath=cache
).load(cache)

# We use a specialized W-method equivalence checker which features
# early stopping on invalid inputs, which speeds things up a lot
#eqc = RersWmethodEquivalenceChecker(sul, False, m=15)
eqc = SmartWmethodEquivalenceChecker(sul,
                                     horizon=10,
                                     stop_on={'invalid_input'},
                                     stop_on_startswith={'error'})
# Set up the teacher, with the system under learning and the equivalence checker
teacher = Teacher(sul, eqc)

# Set up the learner who only talks to the teacher
# We let it save checkpoints of every intermediate hypothesis
learner = MealyLearner(teacher)\
    .enable_checkpoints("checkpoints", problem)

# Get the learners hypothesis
hyp = learner.run(
    show_intermediate=True,
    render_options={'ignore_self_edges': ['error', 'invalid']},
    on_hypothesis=lambda x: check_result(x, f'../../rers/TrainingSeqReachRers2019/{problem}/reachability-solution-{problem}.csv')
)

print("SUCCES", check_result(hyp, f'../../rers/TrainingSeqReachRers2019/{problem}/reachability-solution-{problem}.csv'))

hyp.render_graph(render_options={'ignore_self_edges': ['error', 'invalid']})


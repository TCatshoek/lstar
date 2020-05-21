import tempfile

from equivalencecheckers.wmethod import WmethodEquivalenceChecker, RersWmethodEquivalenceChecker, \
    SmartWmethodEquivalenceChecker
from learners.TTTmealylearner import TTTMealyLearner
from learners.mealylearner import MealyLearner
from suls.caches.rerstriecache import RersTrieCache
from suls.rersconnectorv4 import RERSConnectorV4
from teachers.teacher import Teacher
from rers.check_result import check_result


problem = "m34"

cache = f'cache2/{problem}'

path = f'../../rers/rers_19_industrial_reachability_training/arithmetic/{problem}'

sul = RersTrieCache(
    RERSConnectorV4(f'{path}/{problem}_Reach'),
    storagepath=cache
)

# We use a specialized W-method equivalence checker which features
# early stopping on invalid inputs, which speeds things up a lot
# eqc = RersWmethodEquivalenceChecker(sul, False, m=5)
eqc = SmartWmethodEquivalenceChecker(sul,
                                     horizon=5,
                                     stop_on={'invalid_input'},
                                     stop_on_startswith={'error'})

# Set up the teacher, with the system under learning and the equivalence checker
teacher = Teacher(sul, eqc)

# Set up the learner who only talks to the teacher
# We let it save checkpoints of every intermediate hypothesis
learner = MealyLearner(teacher)\
    .enable_checkpoints("checkpoints", problem)\
    #.load_checkpoint('/home/tom/projects/lstar/examples/learn_rers/checkpoints/m34/2020-05-16_15:42:30:713416')
# Get the learners hypothesis
hyp = learner.run(
    show_intermediate=True,
    render_options={'ignore_self_edges': ['error', 'invalid']},
    on_hypothesis=lambda x: check_result(x, f'{path}/solution_{problem}_reachability.csv')
)

print("SUCCES", check_result(hyp, f'{path}/solution_{problem}_reachability.csv'))

hyp.render_graph(tempfile.mktemp('.gv'))


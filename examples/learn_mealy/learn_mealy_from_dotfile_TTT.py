import tempfile

from equivalencecheckers.bruteforce import BFEquivalenceChecker
from equivalencecheckers.wmethod import WmethodEquivalenceChecker, SmartWmethodEquivalenceChecker
from learners.TTTmealylearner import TTTMealyLearner
from learners.mealylearner import MealyLearner
from suls.caches.dictcache import DictCache
from suls.mealymachine import MealyState, MealyMachine
from teachers.teacher import Teacher
from util.dotloader import load_mealy_dot

problem = 'm54'
path = f"/home/tom/projects/lstar/rers/industrial/{problem}.dot"
cache = f'cache/{problem}'

# mm = DictCache(
#     load_mealy_dot(path),
#     storagepath=cache
# )#.load(cache)

mm = load_mealy_dot(path)

mm.render_graph(render_options={
    'ignore_self_edges': ['error', 'invalid'],
    'ignore_edges': ['error']
})

# Use the W method equivalence checker
eqc = SmartWmethodEquivalenceChecker(mm,
                                     #horizon=3,
                                     m=len(mm.get_states()),
                                     stop_on={'error'},
                                     order_type='ce count')

eqc.onCounterexample(lambda x: print('Counterexample:', x))

teacher = Teacher(mm, eqc)

# We are learning a mealy machine
learner = TTTMealyLearner(teacher)

hyp = learner.run(
    show_intermediate=False
    #render_options={'ignore_self_edges': ['error', 'invalid']},
)

#hyp.render_graph(tempfile.mktemp('.gv'))
learner.DTree.render_graph()
hyp.render_graph(render_options={
    'ignore_self_edges': ['error', 'invalid'],
    #'ignore_edges': ['error']
})
assert len(hyp.get_states()) == len(mm.get_states())

print("done")
import tempfile

from equivalencecheckers.bruteforce import BFEquivalenceChecker
from equivalencecheckers.wmethod import WmethodEquivalenceChecker, SmartWmethodEquivalenceChecker
from learners.mealylearner import MealyLearner
from suls.mealymachine import MealyState, MealyMachine
from teachers.teacher import Teacher
from util.dotloader import load_mealy_dot

path = "/home/tom/projects/lstar/rers/industrial/m34.dot"

mm = load_mealy_dot(path)
#mm.render_graph(tempfile.mktemp('.gv'))

# Use the W method equivalence checker
eqc = SmartWmethodEquivalenceChecker(mm,
                                     m=len(mm.get_states()),
                                     stop_on={'error'})

eqc.onCounterexample(lambda x: print('Counterexample:', x))

teacher = Teacher(mm, eqc)

# We are learning a mealy machine
learner = MealyLearner(teacher)\
    .load_checkpoint('/tmp/checkpoints/m34/2020-05-15_20:53:14:317958')

hyp = learner.run(show_intermediate=False)

#hyp.render_graph(tempfile.mktemp('.gv'))

assert len(hyp.get_states()) == len(mm.get_states())

print("done")
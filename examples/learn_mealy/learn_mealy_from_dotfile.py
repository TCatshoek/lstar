import tempfile

from equivalencecheckers.bruteforce import BFEquivalenceChecker
from learners.mealylearner import MealyLearner
from suls.mealymachine import MealyState, MealyMachine
from teachers.teacher import Teacher
from util.dotloader import load_mealy_dot

path = "/home/tom/projects/lstar/rers/industrial/m54.dot"

mm = load_mealy_dot(path)
mm.render_graph(tempfile.mktemp('.gv'))

# Use the W method equivalence checker
eqc = BFEquivalenceChecker(mm, max_depth=8)

teacher = Teacher(mm, eqc)

# We are learning a mealy machine
learner = MealyLearner(teacher)

hyp = learner.run()

hyp.render_graph(tempfile.mktemp('.gv'))

print("done")
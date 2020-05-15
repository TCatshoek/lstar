import tempfile

from equivalencecheckers.bruteforce import BFEquivalenceChecker
from equivalencecheckers.wmethod import WmethodEquivalenceChecker
from learners.TTTmealylearner import TTTMealyLearner
from suls.mealymachine import MealyState, MealyMachine
from teachers.teacher import Teacher

# Set up an example mealy machine
s1 = MealyState('1')
s2 = MealyState('2')
s3 = MealyState('3')

s1.add_edge('a', 'nice', s2)
s1.add_edge('b', 'B', s1)
s2.add_edge('a', 'nice', s3)
s2.add_edge('b', 'back', s1)
s3.add_edge('a', 'A', s3)
s3.add_edge('b', 'back', s1)

mm = MealyMachine(s1)

# Use the W method equivalence checker
eqc = WmethodEquivalenceChecker(mm)

teacher = Teacher(mm, eqc)

# We are learning a mealy machine
learner = TTTMealyLearner(teacher)

hyp = learner.run()

hyp.render_graph(tempfile.mktemp('.gv'))
learner.DTree.render_graph(tempfile.mktemp('.gv'))
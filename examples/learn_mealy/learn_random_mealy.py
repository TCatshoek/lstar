from equivalencecheckers.wmethod import SmartWmethodEquivalenceChecker
from learners.mealylearner import MealyLearner
from teachers.teacher import Teacher
from util.mealygenerator import minimize, MakeRandomMealyMachine

# Randomly generate a mealy machine
A = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j']
O = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10']
mm = MakeRandomMealyMachine(200, A, O)
# It may not be minimal, so minimize it
mm = minimize(mm)

# Use the W method equivalence checker with early stopping
eqc = SmartWmethodEquivalenceChecker(mm,
                                     m=len(mm.get_states()),
                                     stop_on={'error'})

teacher = Teacher(mm, eqc)

learner = MealyLearner(teacher)

hyp = learner.run(show_intermediate=False)

assert len(hyp.get_states()) == len(mm.get_states())

print("done")
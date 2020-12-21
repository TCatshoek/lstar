from suls.mealymachine import MealyMachine
from suls.mealymachine import MealyState as State
from util.mealy2nusmv import mealy2nusmv_withintermediate
q0 = State('q0')
q1 = State('q1')

q0.add_edge('a', 'A', q1)

mm = MealyMachine(q0)

for line in mealy2nusmv_withintermediate(mm):
    print(line, end='')
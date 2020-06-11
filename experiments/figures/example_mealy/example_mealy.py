from suls.mealymachine import MealyState, MealyMachine

s1 = MealyState('q0')
s2 = MealyState('q1')
s3 = MealyState('q2')

s1.add_edge('a', '1', s2)
s1.add_edge('b', '0', s1)
s2.add_edge('b', '2', s3)
s2.add_edge('a', '0', s2)
s3.add_edge('a', '3', s3)
s3.add_edge('b', '3',s3)

dfa = MealyMachine(s1)

dfa.render_graph('example_mealy', format='png')
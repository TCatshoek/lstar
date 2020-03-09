import tempfile

import numpy as np
from graphviz import Digraph

from equivalencecheckers.bruteforce import BFEquivalenceChecker
#from experiments.tsp.tsplearner import TSPLearner
from experiments.tsp.tsplearner import TSPLearner
from learners.mealylearner import MealyLearner
from suls.mealymachine import MealyState
from suls.sul import SUL
from teachers.teacher import Teacher


class TSPProblem:
    def __init__(self, width=100, height=100):
        self.cities = None
        self.distances = None
        self.width = width
        self.height = height

    def make_random(self, n_cities):
        # Do all the math in numpy because fast
        self.cities = np.random.rand(n_cities, 2) * np.array([self.width, self.height])
        # Unreadable, but FAST
        self.distances = np.sqrt(np.sum(np.square(self.cities.reshape(len(self.cities), -1, 2) - self.cities.reshape(-1, len(self.cities), 2)), axis=2))
        return self

    def get_dist(self, frm, to):
        return self.distances[frm, to]

class TSPSul(SUL):
    def __init__(self, problem, initial_state):
        self.problem = problem
        self.initial_state = initial_state
        self.state = initial_state

    def process_input(self, inputs):
        if len(inputs) < 1:
            return None

        output = 0

        # We impose the restriction of not being able to visit a city twice,
        # Except for returning to the initial city as the last action
        visited = set()
        visited.add(str(self.initial_state))

        for idx, input in enumerate(inputs):
            # Last action can only be returning to the initial city:
            if idx == len(self.problem.cities) - 1:
                if int(input) == self.initial_state:
                    output += self.problem.get_dist(self.state, int(input))
                    self.state = int(input)
                else:
                    return 'invalid_input'

            else:
                if input not in visited:
                    output += self.problem.get_dist(self.state, int(input))
                    self.state = int(input)
                    visited.add(input)
                else:
                    return 'invalid_input'

        return output

    def reset(self):
        self.state = self.initial_state

    def get_alphabet(self):
        return [str(x) for x in list(range(len(self.problem.cities)))]


def filter_errs(hyp):
    for state in hyp.get_states():
        todelete = []

        for action, (nextstate, output) in state.edges.items():
            if output == 'invalid_input':
                todelete.append(action)

        for action in todelete:
            del state.edges[action]

def cleanup(hyp):
    for state in hyp.get_states():
        for action, (nextstate, output) in state.edges.items():
            state.edges[action] = (nextstate, f'{output:.2f}')


def draw(hyp, filename):
    g = Digraph('G', filename=filename)
    g.attr(rankdir='LR')

    # Collect nodes and edges
    to_visit = [hyp.initial_state]
    visited = []

    # Hacky way to draw start arrow pointing to first node
    g.attr('node', shape='none')
    g.node('startz', label='', _attributes={'height': '0', 'width': '0'})

    # Draw initial state
    g.attr('node', shape='circle')
    g.node(hyp.initial_state.name, label='0')

    g.edge('startz', hyp.initial_state.name)

    laststeps = []
    lastname = None

    while len(to_visit) > 0:
        cur_state = to_visit.pop()
        visited.append(cur_state)

        g.attr('node', shape='circle')
        for action, (other_state, output) in cur_state.edges.items():
            # Draw other states, but only once
            if other_state not in visited and other_state not in to_visit:
                to_visit.append(other_state)
                if action == '0':
                    laststeps.append(float(output))
                    lastname = other_state.name
                else:
                    g.node(other_state.name, label=output)

            # Draw edges too
            if action == '0':
                g.edge(cur_state.name, other_state.name, label=f'{action}/{output}')
            else:
                g.edge(cur_state.name, other_state.name, label=f'{action}')

    g.node(lastname, label=str(min(laststeps)))

    g.view()

if __name__ == "__main__":
    tspprob = TSPProblem().make_random(5)
    tsp = TSPSul(tspprob, 0)

    eqc = BFEquivalenceChecker(tsp, max_depth=6)

    teacher = Teacher(tsp, eqc)

    learner = TSPLearner(teacher, tsp=tsp)

    hyp = learner.run(show_intermediate=False)
    #filter_errs(hyp)
    cleanup(hyp)
    #raw(hyp, tempfile.mktemp('.gv'))
    hyp.render_graph(tempfile.mktemp('.gv'))

    # tspprob = TSPProblem().make_random(5)
    # tsp = TSPSul(tspprob, 0)


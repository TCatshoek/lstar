import tempfile
from collections import Iterable

from equivalencecheckers.bruteforce import BFEquivalenceChecker
from learners.mealylearner import MealyLearner
from suls.mealymachine import MealyMachine
from suls.sul import SUL

from enum import Enum

from teachers.teacher import Teacher

from itertools import product

import matplotlib.pyplot as plt


class World(SUL):
    def __init__(self, map, rewards, endstates, initial_pos=(0, 0)):
        self.initial_pos = initial_pos
        self.pos = initial_pos

        self.map = map
        self.rewards = rewards
        self.endstates = endstates

    class Directions(Enum):
        up = 0
        down = 1
        right = 2
        left = 3

    def _step(self, direction):
        newpos = self._getnextpos(direction)

        out = None
        if self.pos in self.endstates:
            out = "end"
        else:
            if self._isvalid(newpos):
                self.pos = newpos
                out = self.rewards[newpos]
            else:
                out = 0

        return out

    def _getnextpos(self, direction):
        # pos is row, col format, top right is 0,0
        cur_row, cur_col = self.pos
        newpos = {
            self.Directions.up: (cur_row - 1, cur_col),
            self.Directions.down: (cur_row + 1, cur_col),
            self.Directions.right: (cur_row, cur_col + 1),
            self.Directions.left: (cur_row, cur_col - 1),
        }
        return newpos[direction]

    def _isvalid(self, pos):
        return self.map[pos] == 1

    def process_input(self, inputs):
        # if not isinstance(inputs, Iterable):
        #     inputs = [inputs]

        output = None
        for input in inputs:
            output = self._step(self.Directions[input])
            # if output == "invalid":
            #     return output

        return output

    def reset(self):
        self.pos = self.initial_pos

    def get_alphabet(self):
        return [d.name for d in self.Directions]

    def show(self):
        tmp = np.copy(self.map)
        tmp[self.initial_pos] = 2
        for endstate in self.endstates:
            tmp[endstate] = 3

        plt.imshow(tmp)
        plt.show()

# Computes the future rewards
def value_iterate(dfa: MealyMachine, gamma, epsilon=0.0001):
    states = dfa.get_states()
    actions = dfa.get_alphabet()

    Q = {}
    Q_1 = {}

    # Initialize Q0
    for sa in product(states, actions):
        Q[sa] = 0

    converged = False
    while not converged:
        # Iterate
        for s, a in product(states, actions):
            next_state, action_result = s.next(a)

            action_reward = 0 if action_result == "end" else int(action_result)
            future_reward = gamma * max([Q[(next_state, next_action)] for next_action in actions])

            Q_1[(s, a)] = action_reward + future_reward

        # Check convergence
        converged = max([abs(Q[sa] - Q_1[sa]) for sa in product(states, actions)]) < epsilon

        Q = Q_1
        Q_1 = {}

    # Annotate states with their values
    for state in states:
        value = max([Q[sa] for sa in product([state], actions)])
        state.name = f'{state.name}/{value:.2f}'

        # Also update the action rewards
        for action in actions:
            next_state, output = state.edges[action]
            state.edges[action] = (next_state, f'{Q[(state, action)]:.2f}')

    dfa.render_graph(tempfile.mktemp('.gv'))




if __name__ == "__main__":
    import numpy as np

    map = np.array([
        [0, 0, 0, 0, 0, 0, 0],
        [0, 1, 1, 1, 1, 1, 0],
        [0, 1, 0, 0, 1, 0, 0],
        [0, 1, 1, 1, 1, 1, 0],
        [0, 1, 0, 0, 0, 1, 0],
        [0, 1, 1, 1, 1, 1, 0],
        [0, 1, 0, 0, 1, 0, 0],
        [0, 1, 1, 1, 1, 1, 0],
        [0, 0, 0, 0, 0, 0, 0]
    ])

    rewards = np.array([
        [0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 1, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0],
    ])

    world = World(map, rewards, endstates=[(1, 3)], initial_pos=(7, 3))

    world.show()

    # We are using the brute force equivalence checker
    eqc = BFEquivalenceChecker(world, max_depth=12)

    # Set up the teacher, with the system under learning and the equivalence checker
    teacher = Teacher(world, eqc)

    # Set up the learner who only talks to the teacher
    learner = MealyLearner(teacher)

    # Get the learners hypothesis
    hyp = learner.run(show_intermediate=True)

    hyp.render_graph(tempfile.mktemp('.gv'))

    value_iterate(hyp, 0.9)

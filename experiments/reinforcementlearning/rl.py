import tempfile
from collections import Iterable

from equivalencecheckers.bruteforce import BFEquivalenceChecker
from learners.mealylearner import MealyLearner
from suls.sul import SUL

from enum import Enum

from teachers.teacher import Teacher


class World(SUL):
    def __init__(self, map, rewards, initial_pos=(0, 0)):
        self.initial_pos = initial_pos
        self.pos = initial_pos

        self.map = map
        self.rewards = rewards

    class Directions(Enum):
        up = 0
        down = 1
        right = 2
        left = 3

    def _step(self, direction):
        newpos = self._getnextpos(direction)

        if self._isvalid(newpos):
            self.pos = newpos
            return self.rewards[newpos]
        else:
            return "invalid"

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
            if output == "invalid":
                return output

        return output

    def reset(self):
        self.pos = self.initial_pos

    def get_alphabet(self):
        return [d.name for d in self.Directions]


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

    world = World(map, rewards, initial_pos=(7, 3))

    # We are using the brute force equivalence checker
    eqc = BFEquivalenceChecker(world, max_depth=12)

    # Set up the teacher, with the system under learning and the equivalence checker
    teacher = Teacher(world, eqc)

    # Set up the learner who only talks to the teacher
    learner = MealyLearner(teacher)



    # Get the learners hypothesis
    hyp = learner.run(show_intermediate=True)

    hyp.render_graph(tempfile.mktemp('.gv'))

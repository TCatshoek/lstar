import tempfile

from equivalencecheckers.StackedChecker import StackedChecker
from equivalencecheckers.bruteforce import BFEquivalenceChecker
from equivalencecheckers.genetic import GeneticEquivalenceChecker
from equivalencecheckers.wmethod import WmethodEquivalenceChecker, SmartWmethodEquivalenceChecker
from learners.TTTmealylearner import TTTMealyLearner
from learners.mealylearner import MealyLearner
from suls.sul import SUL
from teachers.teacher import Teacher
from util.instrumentation import CounterexampleTracker


class ArithmeticTest(SUL):
    def __init__(self):
        self.counter = 0
        self.last_action = None
        self.actions = {
            'add': self._add,
            'sub': self._noop,
            'show': self._show,
            'a': self._noop,
            'b': self._noop,
            'c': self._noop,
            'd': self._noop,
            'e': self._noop,
        }

    def _add(self):
        self.last_action = 'add'
        self.counter += 1
        self.counter = min(self.counter, 18)
        return 'ok'

    def _sub(self):
        self.last_action = 'sub'
        self.counter -= 1
        self.counter = max(0, self.counter)
        return 'ok'

    def _show(self):
        self.last_action = 'show'
        if self.counter % 3 == 0:
            if self.counter >= 18:
                return 'YAY!'
            else:
                return str(self.counter)
        else:
            return 'nope'

    def _noop(self):
        return 'invalid'

    def process_input(self, inputs):

        #print('inputs', inputs)
        outputs = [self.actions[inp]() for inp in inputs]
        #print('outputs', outputs)

        self.reset()

        if len(outputs) == 0:
            return None
        else:
            return outputs[-1]

    def reset(self):
        self.counter = 0
        self.last_action = None

    def get_alphabet(self):
        return tuple(self.actions.keys())

if __name__ == "__main__":
    sul = ArithmeticTest()

    #sul.process_input(['add', 'exec', 'show'])

    ct = CounterexampleTracker()

    eqc = SmartWmethodEquivalenceChecker(sul, horizon=3)

    eqc = StackedChecker(
        GeneticEquivalenceChecker(sul, ct, pop_n=100000),
        SmartWmethodEquivalenceChecker(sul, horizon=4, order_type='ce count')
    )

    eqc.onCounterexample(lambda ce: ct.add(ce))

    teacher = Teacher(sul, eqc)

    # We are learning a mealy machine
    #learner = MealyLearner(teacher)
    learner = TTTMealyLearner(teacher)

    def print_stats(hyp=None):
        print("Member queries:", teacher.member_query_counter)
        print("Equivalence queries:", teacher.equivalence_query_counter)
        print("Test queries:", teacher.test_query_counter)

    hyp = learner.run(
        show_intermediate=False,
        on_hypothesis=print_stats
    )

    hyp.render_graph()


    #learner.DTree.render_graph()

    hyp.render_graph(tempfile.mktemp('.gv'))

    for ce in ct.storage:
        print(ce)

    print_stats()
import tempfile
from typing import Tuple, Optional, Iterable

from equivalencecheckers.bruteforce import BFEquivalenceChecker
from equivalencecheckers.equivalencechecker import EquivalenceChecker
from learners.TTTdfalearner import TTTDFALearner
from learners.dfalearner import DFALearner
from suls.re_machine import RegexMachine
from suls.dfa import State, DFA
from suls.sul import SUL
from teachers.teacher import Teacher

# Set up a simple state machine (S1) =a> (S2) =b> ((S3))

s1 = State('s1')
s2 = State('s2')
s3 = State('s3')

s1.add_edge('a', s2)
s2.add_edge('b', s3)

sm = DFA(s1, [s3])

# Since we are learning a DFA, we need edges for the whole alphabet in every state
s1.add_edge('b', s1)
s2.add_edge('a', s2)
s3.add_edge('a', s3)
s3.add_edge('b', s3)

# Or use a regex to define the state machine
#sm = RegexMachine('b*a+b.*')

class FakeEQChecker(EquivalenceChecker):

    def __init__(self, sul):
        super().__init__(sul)
        self.count = 0

    def test_equivalence(self, test_sul: SUL) -> Tuple[bool, Optional[Iterable]]:
        if self.count == 0:
            self.count += 1
            return False, ('a', 'b', 'b')
        else:
            return True, None

# We are using the brute force equivalence checker
eqc = FakeEQChecker(sm)

# Set up the teacher, with the system under learning and the equivalence checker
teacher = Teacher(sm, eqc)

# Set up the learner who only talks to the teacher
learner = TTTDFALearner(teacher)

# Get the learners hypothesis
hyp = learner.run()

hyp.render_graph('ttt_dfa_example', format='png')
learner.DTree.render_graph('dtree_example', format='png')

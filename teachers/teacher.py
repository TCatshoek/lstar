from suls.sul import SUL
from equivalencecheckers.equivalencechecker import EquivalenceChecker
import util.statstracker as stats

# Simple wrapper class around the system under learning and equivalencechecker
class Teacher:
    def __init__(self, sul: SUL, eqc: EquivalenceChecker):
        self.sul = sul
        self.eqc = eqc
        self.eqc.set_teacher(self)

        self.member_query_counter = 0
        self.equivalence_query_counter = 0
        self.test_query_counter = 0

    def member_query(self, inputs):
        self.member_query_counter += 1

        stats.increment('membership_query')

        self.sul.reset()
        return self.sul.process_input(inputs)

    def equivalence_query(self, hypothesis: SUL):
        self.equivalence_query_counter += 1

        stats.increment('equivalence_query')

        return self.eqc.test_equivalence(hypothesis)

    def get_alphabet(self):
        return self.sul.get_alphabet()

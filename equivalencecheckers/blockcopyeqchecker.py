from typing import Tuple, Iterable

from numpy.random.mtrand import choice

from equivalencecheckers.StackedChecker import StackedChecker
from equivalencecheckers.equivalencechecker import EquivalenceChecker
from suls.rerssoconnector import RERSSOConnector
from suls.sul import SUL
from util.minsepseq import get_distinguishing_set
from util.transitioncover import get_state_cover_set


class BlockCopyEquivalenceChecker(EquivalenceChecker):
    def __init__(self, sul: SUL, max_block_size=5):
        super().__init__(sul)
        self.max_block_size = max_block_size

    def test_equivalence(self, test_sul: SUL) -> Tuple[bool, Iterable]:
        P = get_state_cover_set(test_sul)
        W = get_distinguishing_set(test_sul, check=False)

        equivalent = True
        counterexample = None

        for acc_seq in P:
            equivalent, counterexample = self.blockcopy(acc_seq, test_sul, W)
            if not equivalent:
                return equivalent, counterexample

        return equivalent, counterexample

    # Do a block copy up to the given length for the given acc seq
    def blockcopy(self, acc_seq, test_sul, W):
        acc_seq = tuple(acc_seq)

        equivalent = True
        counterexample = None

        for block_size in range(1, self.max_block_size + 1):

            for block_start_idx in range(len(acc_seq)):
                cur_block = acc_seq[block_start_idx: block_start_idx + block_size]

                for insert_idx in range(len(acc_seq)):
                    cur_test_seq = acc_seq[0:insert_idx] + cur_block + acc_seq[insert_idx:]

                    for w in W:
                        equivalent, counterexample = self._are_equivalent(test_sul, cur_test_seq + w)
                        if not equivalent:
                            return equivalent, counterexample

        return equivalent, counterexample

if __name__ == "__main__":

    from equivalencecheckers.wmethod import SmartWmethodEquivalenceCheckerV2
    from learners.TTTmealylearner import TTTMealyLearner
    from suls.caches.rerstriecache import RersTrieCache
    from suls.rersconnectorv4 import RERSConnectorV4
    from teachers.teacher import Teacher
    from rers.check_result import check_result

    problem = "Problem12"
    problemset = "TrainingSeqReachRers2019"

    sul = RERSSOConnector(f"../rers/{problemset}/{problem}/{problem}.so")
    #sul = RERSConnectorV4(f'../rers/TrainingSeqReachRers2019/{problem}/{problem}')

    eqc = StackedChecker(
        BlockCopyEquivalenceChecker(sul, 3),
        SmartWmethodEquivalenceCheckerV2(sul,
                                         horizon=8,
                                         stop_on={'invalid_input'},
                                         stop_on_startswith={'error'})
    )

    teacher = Teacher(sul, eqc)
    learner = TTTMealyLearner(teacher)

    # Get the learners hypothesis
    hyp = learner.run(
        show_intermediate=True,
        render_options={'ignore_self_edges': ['error', 'invalid']},
        on_hypothesis=lambda x: check_result(x,
                                             f'../rers/TrainingSeqReachRers2019/{problem}/reachability-solution-{problem}.csv')
    )

    hyp.render_graph(render_options={'ignore_self_edges': ['error', 'invalid']})


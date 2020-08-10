from subprocess import Popen
import subprocess

from typing import Tuple, Iterable

from afl.utils import AFLUtils
from equivalencecheckers.StackedChecker import StackedChecker
from equivalencecheckers.wmethod import SmartWmethodEquivalenceCheckerV2
from learners.TTTmealylearner import TTTMealyLearner
from learners.mealylearner import MealyLearner
from rers.check_result import check_result
from suls.caches.rerstriecache import RersTrieCache
from suls.caches.triecache import TrieCache
from suls.rersconnectorv4 import RERSConnectorV4
from suls.rerssoconnector import RERSSOConnector
from teachers.teacher import Teacher
from util.minsepseq import get_distinguishing_set
from util.transitioncover import get_state_cover_set
from equivalencecheckers.equivalencechecker import EquivalenceChecker
from suls.dfa import DFA
from suls.mealymachine import MealyMachine, MealyState
from suls.sul import SUL
from typing import Union
from itertools import product, chain
from pathlib import Path
from shutil import rmtree
from afl.util import decode_afl_file, strip_invalid, trim
import pickle
from util.minsepseq import get_distinguishing_set

from enum import Enum, auto
from itertools import product


class EQCheckType(Enum):
    ERRORS = auto()
    QUEUE = auto()
    BOTH = auto()

class AFLEquivalenceCheckerV2(EquivalenceChecker):
    def __init__(self, sul: SUL,
                 corpus_path,
                 eqchecktype=EQCheckType.ERRORS,
                 enable_dtraces=False):

        super().__init__(sul)

        self.sul_alphabet = [str(x) for x in sul.get_alphabet()]

        self.corpus_path = Path(corpus_path)

        assert self.corpus_path.exists(), f"corpus dir does not exist - {self.corpus_path}"

        self.eqchecktype = eqchecktype
        self.enable_dtraces = enable_dtraces


    def test_equivalence(self, fsm: Union[DFA, MealyMachine]) -> Tuple[bool, Iterable]:

        equivalent = True
        counterexample = None

        if self.eqchecktype == EQCheckType.ERRORS or self.eqchecktype == EQCheckType.BOTH:
            equivalent, counterexample = self._test_equivalence_helper(fsm, self.aflutils.get_crashset())
            if not equivalent:
                return equivalent, tuple(counterexample)

        if self.eqchecktype == EQCheckType.QUEUE or self.eqchecktype == EQCheckType.BOTH:
            if self.enable_dtraces:
                testset = self.aflutils.get_testset()
                dset = get_distinguishing_set(fsm)
                concatted = [tuple(a) + b for a, b in product(testset, dset)]
                equivalent, counterexample = self._test_equivalence_helper(fsm, concatted)
            else:
                equivalent, counterexample = self._test_equivalence_helper(fsm, self.aflutils.get_testset())
            if not equivalent:
                return equivalent, tuple(counterexample)

        return equivalent, counterexample

    def _test_equivalence_helper(self, fsm: Union[DFA, MealyMachine], testcases) -> Tuple[bool, Union[Iterable, None]]:
        for testcase in testcases:
            equivalent, counterexample = self._are_equivalent(fsm, [str(x) for x in testcase])
            if not equivalent:
                return equivalent, tuple(counterexample)

        return True, None



if __name__ == "__main__":
    problem = "Problem12"
    problemset = "TrainingSeqReachRers2019"

    path = f"/home/tom/projects/lstar/rers/{problemset}/{problem}/{problem}.so"

    sul = RERSSOConnector(path)

    afl_dir = f'/home/tom/projects/lstar/afl/{problemset}/{problem}'
    bin_path = f'/home/tom/projects/lstar/afl/{problemset}/{problem}/{problem}'

    eqc = StackedChecker(
        AFLEquivalenceCheckerV2(sul, afl_dir, bin_path, eqchecktype=EQCheckType.BOTH),
        SmartWmethodEquivalenceCheckerV2(sul,
                                         horizon=3,
                                         stop_on={'invalid_input'},
                                         stop_on_startswith={'error'})
    )

    teacher = Teacher(sul, eqc)

    learner = TTTMealyLearner(teacher)
    # learner.enable_checkpoints('checkpoints3')
    # learner.load_checkpoint('/home/tom/projects/lstar/experiments/counterexampletracker/checkpoints3/cZsmSu/2020-05-06_20:00:33:790987')
    # Get the learners hypothesis
    hyp = learner.run(
        show_intermediate=False,
        render_options={'ignore_self_edges': ['error', 'invalid']},
        on_hypothesis=lambda x: check_result(x,
                                             f'../rers/TrainingSeqReachRers2019/{problem}/reachability-solution-{problem}.csv')
    )

    print("SUCCES",
          check_result(hyp, f'../rers/TrainingSeqReachRers2019/{problem}/reachability-solution-{problem}.csv'))

    hyp.render_graph(render_options={'ignore_self_edges': ['error', 'invalid']})

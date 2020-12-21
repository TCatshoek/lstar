from subprocess import Popen
import subprocess

from typing import Tuple, Iterable

from afl.utils import AFLUtils
from equivalencecheckers.StackedChecker import StackedChecker
from equivalencecheckers.wmethod import SmartWmethodEquivalenceCheckerV2
from learners.TTTmealylearner import TTTMealyLearner
from learners.mealylearner import MealyLearner
from libfuzzer.utils import CorpusUtils
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

class LibFuzzerEquivalenceChecker(EquivalenceChecker):
    def __init__(self, sul: SUL,
                 corpus_path,
                 fuzzer_path,
                 eqchecktype=EQCheckType.ERRORS,
                 enable_dtraces=False,
                 minimize=True):

        super().__init__(sul)

        self.sul_alphabet = [str(x) for x in sul.get_alphabet()]

        self.corpus_path = Path(corpus_path)
        assert self.corpus_path.exists(), f"corpus dir does not exist - {self.corpus_path}"

        self.fuzzer_path = Path(fuzzer_path)
        assert self.fuzzer_path.exists() and self.fuzzer_path.is_file(), f"Fuzzer executable not found - {self.fuzzer_path}"

        self.cutil = CorpusUtils(corpus_path=self.corpus_path,
                                 fuzzer_path=self.fuzzer_path,
                                 sul=self.sul)

        self.eqchecktype = eqchecktype
        self.enable_dtraces = enable_dtraces

        self.minimize = minimize


    def test_equivalence(self, fsm: Union[DFA, MealyMachine]) -> Tuple[bool, Iterable]:

        equivalent = True
        counterexample = None

        # Ensure minimization was performed if necessary
        if self.minimize:
            self.cutil.minimize_corpus()

        # Gather testcases
        testcases = self.cutil.gather_testcases(minimized=self.minimize)

        if self.enable_dtraces:
            dset = get_distinguishing_set(fsm)
            for testcase in testcases:
                for dtrace in dset:
                    cur_testcase = tuple(testcase) + tuple(dtrace)
                    equivalent, counterexample = self._are_equivalent(fsm, [str(x) for x in cur_testcase])
                    if not equivalent:
                        return equivalent, tuple(counterexample)

        else:
            for testcase in testcases:
                equivalent, counterexample = self._are_equivalent(fsm, [str(x) for x in testcase])
                if not equivalent:
                    return equivalent, tuple(counterexample)

        return equivalent, None




if __name__ == "__main__":
    problem = "Problem9"
    problemset = "SeqLtlRers2019"
    path = Path(f'/home/tom/projects/lstar/libfuzzer/{problemset}/{problem}')
    #path = Path(f'/home/tom/afl/libfuzz/{problemset}/{problem}')
    assert path.exists()

    sul = RERSSOConnector(f'/home/tom/projects/lstar/rers/{problemset}/{problem}/{problem}.so')
    #sul = RERSSOConnector(f'/home/tom/projects/lstar/rers/TrainingSeqReachRers2019/{problem}/{problem}.so')


    eqc = StackedChecker(
        LibFuzzerEquivalenceChecker(sul,
                                    corpus_path=path.joinpath("corpus"),
                                    fuzzer_path=path.joinpath(f'{problem}_fuzz')),
        SmartWmethodEquivalenceCheckerV2(sul,
                                         horizon=1,
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
    )

    hyp.render_graph(render_options={'ignore_self_edges': ['error', 'invalid']})

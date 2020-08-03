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


class AFLEquivalenceCheckerV2(EquivalenceChecker):
    def __init__(self, sul: SUL, afl_dir, bin_path, name="learner01"):

        super().__init__(sul)

        self.sul_alphabet = [str(x) for x in sul.get_alphabet()]

        self.afl_dir = Path(afl_dir)
        self.bin_path = Path(bin_path)
        assert self.afl_dir.exists()
        assert self.bin_path.exists()

        self.aflutils = AFLUtils(afl_dir, bin_path, self.sul_alphabet, sul)

        # Keep track of file names for access sequences [maps state names to id for file names]
        self.state_id = {}

        self.name = name



    def _update_afl_queue(self, fsm: Union[DFA, MealyMachine]):
        # Make sure we have a folder to put our stuff in
        queuepath = self.afl_dir.joinpath(f'output/{self.name}/queue')
        queuepath.mkdir(exist_ok=True, parents=True)

        state_cover = get_state_cover_set(fsm)
        for acc_seq in state_cover:
            fsm.reset()
            fsm.process_input(acc_seq)

            if acc_seq in self.state_id:
                file_id = self.state_id[acc_seq]
            else:
                self.state_id[acc_seq] = len(self.state_id)
                file_id = self.state_id[acc_seq]

            filename = f'id:{str(file_id).rjust(6, "0")}'

            with open(queuepath.joinpath(filename), 'wb') as file:
                for a in acc_seq:
                    file.write(bytes([int(a)]))

    def test_equivalence(self, fsm: Union[DFA, MealyMachine]) -> Tuple[bool, Iterable]:
        self._update_afl_queue(fsm)

        # Minimization loses some crashes :(
        #crashing_testcases = self.aflutils.get_minimized_crashset()
        crashing_testcases = self.aflutils.get_crashset()

        equivalent = True
        counterexample = None

        for testcase in crashing_testcases:
            equivalent, counterexample = self._are_equivalent(fsm, [str(x) for x in testcase])
            if not equivalent:
                return equivalent, tuple(counterexample)

        return equivalent, counterexample


if __name__ == "__main__":
    problem = "Problem12"
    problemset = "TrainingSeqReachRers2019"

    path = f"/home/tom/projects/lstar/rers/{problemset}/{problem}/{problem}.so"

    sul = RERSSOConnector(path)

    afl_dir = f'/home/tom/projects/lstar/afl/{problemset}/{problem}'
    bin_path = f'/home/tom/projects/lstar/afl/{problemset}/{problem}/{problem}'

    eqc = StackedChecker(
        AFLEquivalenceCheckerV2(sul, afl_dir, bin_path),
        SmartWmethodEquivalenceCheckerV2(sul,
                                         horizon=12,
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

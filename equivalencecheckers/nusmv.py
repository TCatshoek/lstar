from subprocess import Popen
import subprocess

from typing import Tuple, Iterable

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
from util.nusmv import NuSMVUtils
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
import re


def parse_nusmv_counterexample(ce):
    result = re.match(r'\[(.*)\]\(\[(.*)\]\)', ce)
    assert result, f"Couldn't parse nusmv counterexample: f{ce}"

    prefix = result.group(1).split(';') if len(result.group(1)) > 0 else []
    loop = result.group(2).split(';') if len(result.group(2)) > 0 else []

    prefix_inputs = [prefix[i] for i in range(0, len(prefix), 2)]
    loop_inputs = [loop[i] for i in range((len(prefix) % 2), len(loop), 2)]

    return tuple(prefix_inputs), tuple(loop_inputs)


class NuSMVEquivalenceChecker(EquivalenceChecker):
    def __init__(self, sul: SUL, constraints_path, mapping_path, n_unrolls=100):
        super().__init__(sul)
        self.nusmv = NuSMVUtils(constraints_path, mapping_path)
        self.n_unrolls = n_unrolls

    def test_equivalence(self, fsm: Union[DFA, MealyMachine]) -> Tuple[bool, Iterable]:
        # Get the NuSMV results
        nusmv_results = self.nusmv.run_ltl_check(fsm)

        # Get the counterexamples for the failed constraints:
        nusmv_counterexamples = [y[2] for y in filter(lambda x: x[1] == 'false', nusmv_results)]

        for nusmv_counterexample in nusmv_counterexamples:
            prefix, loop = parse_nusmv_counterexample(nusmv_counterexample)
            for n in range(self.n_unrolls):
                cur_testcase = prefix + (loop * n)
                #print("NUSMV", cur_testcase)
                if len(cur_testcase) > 0:
                    equivalent, counterexample = self._are_equivalent(fsm, cur_testcase)
                    if not equivalent:
                        return equivalent, counterexample

        return True, None


if __name__ == "__main__":
    problem = 'Problem3'
    problemset = 'SeqLtlRers2020'
    problemset = 'TrainingSeqLtlRers2020'
    constrpath = f'/home/tom/projects/lstar/rers/{problemset}/{problem}/constraints-{problem}.txt'
    mappingpath = f'/home/tom/projects/lstar/rers/{problemset}/{problem}/{problem}_alphabet_mapping_C_version.txt'


    path = f"../rers/{problemset}/{problem}/{problem}.so"
    sul = RERSSOConnector(path)

    horizon = 2

    eqc = StackedChecker(
        #NuSMVEquivalenceChecker(sul, constrpath, mappingpath),
        SmartWmethodEquivalenceCheckerV2(sul,
                                         horizon=horizon,
                                         stop_on={'invalid_input'},
                                         stop_on_startswith={'error'})
    )

    # Set up the teacher, with the system under learning and the equivalence checker
    teacher = Teacher(sul, eqc)

    # Set up the learner who only talks to the teacher
    learner = TTTMealyLearner(teacher)

    # Get the learners hypothesis
    hyp = learner.run(
        show_intermediate=False,
    )


    nusmv = NuSMVUtils(constrpath, mappingpath)

    nusmv.run_ltl_check(hyp)

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
from itertools import product

# def parse_nusmv_counterexample(ce):
#     result = re.match(r'\[(.*)\]\(\[(.*)\]\)', ce)
#     assert result, f"Couldn't parse nusmv counterexample: f{ce}"
#
#     prefix = result.group(1).split(';') if len(result.group(1)) > 0 else []
#     loop = result.group(2).split(';') if len(result.group(2)) > 0 else []
#
#     prefix_inputs = [prefix[i] for i in range(0, len(prefix), 2)]
#     loop_inputs = [loop[i] for i in range((len(prefix) % 2), len(loop), 2)]
#
#     return tuple(prefix_inputs), tuple(loop_inputs)

def parse_nusmv_counterexample(ce):
    loop_match = re.findall(r'\(\[([0-9;]*)\]\)\*', ce)
    assert len(loop_match) > 0, f"Couldn't parse nusmv counterexample loops: {ce}"

    prefix_match = re.match(r'\[([0-9;]*)\]\(', ce)
    assert prefix_match, f"Couldn't parse nusmv counterexample prefix: {ce}"

    prefix = prefix_match.group(1).split(';') if len(prefix_match.group(1)) > 0 else []
    prefix_inputs = [prefix[i] for i in range(0, len(prefix), 2)]

    prev = prefix
    loops_inputs = []
    for loop_str in loop_match:
        loop = loop_str.split(';')
        loop_inputs = [loop[i] for i in range((len(prev) % 2), len(loop), 2)]
        loops_inputs.append(tuple(loop_inputs))
        prev = loop

    return tuple(prefix_inputs), loops_inputs


class NuSMVEquivalenceChecker(EquivalenceChecker):
    def __init__(self, sul: SUL, constraints_path, mapping_path, n_unrolls=10, enable_dtraces=True):
        super().__init__(sul)
        self.nusmv = NuSMVUtils(constraints_path, mapping_path)
        self.n_unrolls = n_unrolls
        self.enable_dset = enable_dtraces

    def test_equivalence(self, fsm: Union[DFA, MealyMachine]) -> Tuple[bool, Iterable]:
        # Get the NuSMV results
        nusmv_results = self.nusmv.run_ltl_check(fsm)

        # Get the counterexamples for the failed constraints:
        nusmv_counterexamples = [y[2] for y in filter(lambda x: x[1] == 'false', nusmv_results)]

        # Get distinguishing set
        dset = get_distinguishing_set(fsm)

        for nusmv_counterexample in nusmv_counterexamples:
            prefix, loops = parse_nusmv_counterexample(nusmv_counterexample)

            # Figure out the unroll counts for the loops
            n_repeats = product(range(self.n_unrolls), repeat=len(loops))
            for repeats in n_repeats:

                # build testcase
                cur_testcase = prefix
                for idx, repeat in enumerate(repeats):
                    cur_testcase += (loops[idx] * repeat)

                if self.enable_dset:
                    for dtrace in dset:
                        cur_testcase_w_dtrace = cur_testcase + tuple(dtrace)
                        if len(cur_testcase_w_dtrace) > 0 and cur_testcase_w_dtrace[0] != '':
                            equivalent, counterexample = self._are_equivalent(fsm, cur_testcase_w_dtrace)
                            if not equivalent:
                                return equivalent, counterexample
                else:
                    if len(cur_testcase) > 0 and cur_testcase[0] != '':
                        equivalent, counterexample = self._are_equivalent(fsm, cur_testcase)
                        if not equivalent:
                            return equivalent, counterexample

        return True, None


if __name__ == "__main__":
    from rers.check_ltl_result import check_result

    problem = 'Problem3'
    problemset = 'SeqLtlRers2020'
    problemset = 'TrainingSeqLtlRers2020'
    constrpath = f'/home/tom/projects/lstar/rers/{problemset}/{problem}/constraints-{problem}.txt'
    mappingpath = f'/home/tom/projects/lstar/rers/{problemset}/{problem}/{problem}_alphabet_mapping_C_version.txt'

    if '2020' in problemset:
        solutionspath = f'/home/tom/projects/lstar/rers/{problemset}/{problem}/constraints-solution-{problem}.txt'
    else:
        solutionspath = f'/home/tom/projects/lstar/rers/{problemset}/{problem}/constraints-solution.csv'

    path = f"../rers/{problemset}/{problem}/{problem}.so"
    sul = RERSSOConnector(path)

    horizon = 2

    eqc = StackedChecker(
        SmartWmethodEquivalenceCheckerV2(sul,
                                         horizon=horizon,
                                         stop_on={'invalid_input'},
                                         stop_on_startswith={'error'}),
        NuSMVEquivalenceChecker(sul, constrpath, mappingpath, n_unrolls=10),
        # SmartWmethodEquivalenceCheckerV2(sul,
        #                                  horizon=horizon,
        #                                  stop_on={'invalid_input'},
        #                                  stop_on_startswith={'error'})
    )

    # Set up the teacher, with the system under learning and the equivalence checker
    teacher = Teacher(sul, eqc)

    # Set up the learner who only talks to the teacher
    learner = TTTMealyLearner(teacher)

    # Get the learners hypothesis
    hyp = learner.run(
        show_intermediate=False,
    )

    #hyp.render_graph()

    nusmv = NuSMVUtils(constrpath, mappingpath)

    ltl_answers = nusmv.run_ltl_check(hyp)

    if 'Training' in problemset:
        check_result(ltl_answers, solutionspath)

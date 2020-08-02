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


class AFLEquivalenceChecker(EquivalenceChecker):
    def __init__(self, sul: SUL, exec_path,
                 afl_out_dir="/tmp/afl/output",
                 parse_bin_path="../afl/parse"):

        super().__init__(sul)
        self.afl_out_dir = afl_out_dir
        self.sul_alphabet = [str(x) for x in sul.get_alphabet()]
        self.parse_bin_path = parse_bin_path
        self.exec_path = exec_path
        self.try_minimizing = set()
        self.testcase_cache = {}

        # Keep track of file names for access sequences [maps state names to id for file names]
        self.state_id = {}


    def _get_testcases(self, type="queue"):
        #h4x
        #if Path('tmpstorage').exists():
        #   self.testcase_cache = pickle.load(open('tmpstorage', 'rb'))

        testcases = []
        paths = [x for x in Path(self.afl_out_dir).glob('**/id:*') if x.match(f'**/{type}/**') and not x.match('**/leaner*/**')]
        for path in paths:
            if path in self.testcase_cache:
                testcases.append((path, self.testcase_cache[path]))
            else:
                if path in self.try_minimizing:
                    testcase = decode_afl_file(path.absolute(), self.parse_bin_path, self.exec_path, minimize=True)
                else:
                    testcase = decode_afl_file(path.absolute(), self.parse_bin_path, self.exec_path)

                if len(testcase) > 0:
                    stripped = strip_invalid(testcase, self.sul_alphabet)
                    trimmed = trim(stripped, self.sul)
                    testcases.append((path, trimmed))
                    self.testcase_cache[path] = trimmed

        #pickle.dump(self.testcase_cache, open('tmpstorage', 'wb'))

        return testcases

    def _update_afl_queue(self, fsm: Union[DFA, MealyMachine]):
        # Make sure we have a folder to put our stuff in
        queuepath = Path(self.afl_out_dir).joinpath('learner01/queue')
        queuepath.mkdir(exist_ok=True, parents=True)

        state_cover = get_state_cover_set(fsm)
        for acc_seq in state_cover:
            fsm.reset()
            fsm.process_input(acc_seq)
            statename = fsm.state.name

            if statename in self.state_id:
                filename = self.state_id[statename]
            else:
                filename = f'id:{statename.rjust(6, "0")}'
                self.state_id[statename] = filename

            with open(queuepath.joinpath(filename), 'w') as file:
                for a in acc_seq:
                    file.write(f'{a} ')
                file.write('0 \n')


    def test_equivalence(self, fsm: Union[DFA, MealyMachine]) -> Tuple[bool, Iterable]:
        self._update_afl_queue(fsm)

        crashes = self._get_testcases('crashes')
        # queries = self._get_testcases('queue')

        def test_queries(queries):
            for path, query in queries:
                #print("testing", query)
                if self.sul.process_input(query) == "invalid_input":
                    print("NO CRASH:", path)
                    self.try_minimizing.add(path)
                equivalent, counterexample = self._are_equivalent(fsm, query)
                if not equivalent:
                    return equivalent, counterexample
            return True, None

        print("[Info] testing crashing afl queries")

        equivalent, counterexample = test_queries(crashes)
        if not equivalent:
            return equivalent, tuple(counterexample)
        #
        # print("[Info] testing normal afl queries")
        # equivalent, counterexample = test_queries(queries)
        # if not equivalent:
        #     return equivalent, tuple(counterexample)

        return True, None


if __name__ == "__main__":
    problem = "Problem12"

    sul = RersTrieCache(
        RERSConnectorV4(f'../rers/TrainingSeqReachRers2019/{problem}/{problem}'),
        storagepath="cache"
    )

    exec_path = f'../afl/TrainingSeqReachRers2019/{problem}/{problem}'
    #afl_path = '/home/tom/projects/lstar/afl/output'
    afl_path = '/tmp/afl/output'

    eqc = StackedChecker(
        AFLEquivalenceChecker(sul, exec_path, afl_out_dir=afl_path),
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

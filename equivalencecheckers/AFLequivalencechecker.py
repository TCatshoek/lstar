from subprocess import Popen
import subprocess

from typing import Tuple, Iterable

from equivalencecheckers.StackedChecker import StackedChecker
from equivalencecheckers.wmethod import SmartWmethodEquivalenceCheckerV2
from learners.mealylearner import MealyLearner
from rers.check_result import check_result
from suls.caches.triecache import TrieCache
from suls.rersconnectorv4 import RERSConnectorV4
from teachers.teacher import Teacher
from util.distinguishingset import get_distinguishing_set
from util.transitioncover import get_state_cover_set
from equivalencecheckers.equivalencechecker import EquivalenceChecker
from suls.dfa import DFA
from suls.mealymachine import MealyMachine, MealyState
from suls.sul import SUL
from typing import Union
from itertools import product, chain
from pathlib import Path
from shutil import rmtree


class AFLEquivalenceChecker(EquivalenceChecker):
    def __init__(self, sul: SUL, exec_path, workdir="/tmp/afl"):
        super().__init__(sul)
        self.workdir = Path(workdir)
        # if self.workdir.exists():
        #     rmtree(self.workdir)
        self.workdir.mkdir(exist_ok=True)
        self.aflproc = None
        self.exec_path = Path(exec_path)

        self.sul_alphabet = self.sul.get_alphabet()

        self._generate_dictionary()
        self._generate_initial_input()

        self._start_afl()

    def _generate_dictionary(self):
        dict_content = ' '.join([str(x) for x in self.sul_alphabet]) + ' 0'
        dict_content = dict_content.split(' ')
        dict_content = [f"\"{x} \"\n" for x in dict_content]
        with open(self.workdir.joinpath("dictionary.dict"), 'w') as file:
            file.writelines(dict_content)

    def _generate_initial_input(self):
        self.workdir.joinpath("input").mkdir(exist_ok=True)
        subprocess.run(f"echo {' '.join([str(x) for x in self.sul_alphabet]) + ' 0'} > input/1.txt", shell=True, cwd=self.workdir)

    def _start_afl(self):
        if self.aflproc is None and not self.workdir.joinpath("output").exists():
            self.aflproc = Popen(["afl-fuzz",
                                  "-i", "input",
                                  "-o", "output",
                                  "-x", "dictionary.dict",
                                  self.exec_path.absolute()
                                  ], cwd=self.workdir)
        else:
            self.aflproc = Popen(["afl-fuzz",
                                  "-i-",
                                  "-o", "output",
                                  "-x", "dictionary.dict",
                                  self.exec_path.absolute()
                                  ], cwd=self.workdir)

    def _stop_afl(self):
        assert self.aflproc is not None
        if self.aflproc is not None:
            self.aflproc.terminate()

    def _get_testcases(self, path="queue"):
        testcases = []
        for testcase in [x for x in self.workdir.joinpath(f"output/{path}").iterdir() if not x.is_dir()]:
            with open(testcase, 'rb') as file:
                test = self._parse_testcase(file.read())
                if len(test) > 0:
                    testcases.append(test)
        return testcases

    def _parse_testcase(self, input):
        input = input.decode(errors='ignore')
        # get rid of duplicate whitespace and split
        inputs = " ".join(input.split()).strip().split(' ')
        inputs = [x for x in inputs if x in self.sul_alphabet]
        return(inputs)

    def _update_afl_queue(self, fsm: Union[DFA, MealyMachine]):
        state_cover = get_state_cover_set(fsm)

        for access_seq in state_cover:



    def test_equivalence(self, fsm: Union[DFA, MealyMachine]) -> Tuple[bool, Iterable]:
        self._stop_afl()
        self._update_afl_queue()

        crashes = self._get_testcases('crashes')
        queries = self._get_testcases('queue')

        equivalent = True
        counterexample = None

        def test_queries(queries):
            for query in queries:
                print("testing", query)
                equivalent, counterexample = self._are_equivalent(fsm, query)
                if not equivalent:
                    return

        print("[Info] testing crashing afl queries")
        test_queries(crashes)

        if not equivalent:
            return equivalent, counterexample

        print("[Info] testing normal afl queries")
        test_queries(queries)

        return equivalent, counterexample


if __name__ == "__main__":
    problem = "Problem12"

    sul = TrieCache(
        RERSConnectorV4(f'../rers/TrainingSeqReachRers2019/{problem}/{problem}'),
        storagepath="cache"
    )

    exec_path = f'../afl/TrainingSeqReachRers2019/{problem}/{problem}'

    eqc = StackedChecker(
        AFLEquivalenceChecker(sul, exec_path),
        SmartWmethodEquivalenceCheckerV2(sul,
                                         horizon=9,
                                         stop_on={'invalid_input'},
                                         stop_on_startswith={'error'})
    )

    teacher = Teacher(sul, eqc)

    learner = MealyLearner(teacher)
    # learner.enable_checkpoints('checkpoints3')
    # learner.load_checkpoint('/home/tom/projects/lstar/experiments/counterexampletracker/checkpoints3/cZsmSu/2020-05-06_20:00:33:790987')
    # Get the learners hypothesis
    hyp = learner.run(
        show_intermediate=True,
        render_options={'ignore_self_edges': ['error', 'invalid']},
        on_hypothesis=lambda x: check_result(x,
                                             f'../rers/TrainingSeqReachRers2019/{problem}/reachability-solution-{problem}.csv')
    )

    print("SUCCES",
          check_result(hyp, f'../rers/TrainingSeqReachRers2019/{problem}/reachability-solution-{problem}.csv'))

    hyp.render_graph(render_options={'ignore_self_edges': ['error', 'invalid']})

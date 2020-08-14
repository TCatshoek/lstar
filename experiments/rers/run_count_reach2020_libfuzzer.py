import sys
from pathlib import Path

from libfuzzer.utils import CorpusUtils
from rers.check_result import parse_csv

sys.path.extend(['/home/tom/projects/lstar'])
import os
os.chdir('/home/tom/projects/lstar/experiments/rers')

from suls.rerssoconnector import RERSSOConnector
import re


def check_reached(problem, problemset, rers_basepath, fuzzer_basepath):
    rers_path = f"{rers_basepath}/{problemset}/{problem}/{problem}.so"
    fuzzer_dir = Path(f'{fuzzer_basepath}/{problemset}/{problem}')

    assert fuzzer_dir.exists(), fuzzer_dir

    sul = RERSSOConnector(rers_path)

    cutils = CorpusUtils(
        corpus_path=fuzzer_dir.joinpath('corpus'),
        fuzzer_path=fuzzer_dir.joinpath(f'{problem}_fuzz'),
        sul=sul
    )

    testcases = cutils.gather_testcases()

    errors = filter(lambda x: x.startswith('error'),
                    [tmp for testcase in testcases if
                      (tmp:= cutils.extract_error(testcase)) is not None])

    return set([int(re.sub('error_', '', x)) for x in errors])


problems = [f'Problem{x}' for x in range(12, 20)]
problemset = "SeqReachabilityRers2020"

rers_basepath = "/home/tom/projects/lstar/rers"
fuzzer_basepath = "/home/tom/afl/libfuzz"

for problem in problems:

    print(problem)
    errors = check_reached(problem, problemset, rers_basepath, fuzzer_basepath)
    print(f"Reached {len(errors)}")

    result_dir = Path(f'results/{problemset}_libfuzz')
    result_dir.mkdir(exist_ok=True, parents=True)

    problem_number = problem.replace('Problem', '')

    with result_dir.joinpath(f'{problem}_tcatshoek.csv').open('w') as f:
        for error in sorted(errors, key=lambda x: int(x)):
            f.write(f'{problem_number}, {error}, true\n')
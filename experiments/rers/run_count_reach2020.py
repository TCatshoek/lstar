import sys
from pathlib import Path

sys.path.extend(['/home/tom/projects/lstar'])
import os
os.chdir('/home/tom/projects/lstar/experiments/rers')

from afl.utils import AFLUtils
from suls.rerssoconnector import RERSSOConnector
import re


def check_reached(problem, problemset, rers_basepath, afl_basepath):
    rers_path = f"{rers_basepath}/{problemset}/{problem}/{problem}.so"
    afl_dir = f'{afl_basepath}/{problemset}/{problem}'
    bin_path = f'{afl_basepath}/{problemset}/{problem}/{problem}'

    sul = RERSSOConnector(rers_path)

    aflutils = AFLUtils(afl_dir,
                        bin_path,
                        [str(x) for x in sul.get_alphabet()],
                        sul)

    errors = aflutils.gather_reached_errors()
    return set([re.sub('error_', '', x) for x in errors])


problems = [f'Problem{x}' for x in range(11, 20)]
problemset = "SeqReachabilityRers2020"
rers_basepath = "/home/tom/projects/lstar/rers"
afl_basepath =   "/home/tom/afl/apta_backup_old/tmpfs/2020_plusplus"
afl_basepath_2 = "/home/tom/afl/apta_backup_old/tmpfs/2020_fast"


for problem in problems:
    print(problem)
    errors = check_reached(problem, problemset, rers_basepath, afl_basepath)
    print(len(errors))
    errors_2 = check_reached(problem, problemset, rers_basepath, afl_basepath_2)
    print(len(errors_2))
    print('total:', len(errors.union(errors_2)))
    print()

    errors = errors.union(errors_2)

    result_dir = Path(f'results/{problemset}_combined')
    result_dir.mkdir(exist_ok=True, parents=True)

    problem_number = problem.replace('Problem', '')

    with result_dir.joinpath(f'{problem}_tcatshoek.csv').open('w') as f:
        for error in sorted(errors, key=lambda x: int(x)):
            f.write(f'{problem_number}, {error}, true\n')
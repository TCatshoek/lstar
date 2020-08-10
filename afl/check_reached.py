from pathlib import Path

from afl.utils import AFLUtils
from rers.check_result import parse_csv
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

    reached = [int(re.sub('error_', '', x)) for x in aflutils.gather_reached_errors()]

    reachable, unreachable = parse_csv(Path(rers_path).parent.joinpath(f'reachability-solution-{problem}.csv'))

    print("Reached:", set(reached))
    print("Not reached:", set(reached).symmetric_difference(set(reachable)))
    print(f'{len(set(reached))}/{len(set(reachable))}')

training_problems = ["Problem11", "Problem12", "Problem13"]
problemset = "TrainingSeqReachRers2019"
rers_basepath = "/home/tom/projects/lstar/rers"
#afl_basepath = "/home/tom/projects/lstar/afl"
afl_basepath = "/tmp/afl/trainingreach2019"

for problem in training_problems:
    print(problem)
    check_reached(problem, problemset, rers_basepath, afl_basepath)
    print()
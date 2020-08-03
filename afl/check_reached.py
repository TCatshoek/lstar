from pathlib import Path

from afl.utils import AFLUtils
from rers.check_result import parse_csv
from suls.rerssoconnector import RERSSOConnector
import re

problem = "Problem11"
problemset = "TrainingSeqReachRers2019"

path = f"/home/tom/projects/lstar/rers/{problemset}/{problem}/{problem}.so"

sul = RERSSOConnector(path)

afl_dir = f'/home/tom/projects/lstar/afl/{problemset}/{problem}'
bin_path = f'/home/tom/projects/lstar/afl/{problemset}/{problem}/{problem}'

aflutils = AFLUtils(afl_dir,
                    bin_path,
                    [str(x) for x in sul.get_alphabet()],
                    sul)

reached = [int(re.sub('error_', '', x)) for x in aflutils.gather_reached_errors()]

reachable, unreachable = parse_csv(Path(path).parent.joinpath(f'reachability-solution-{problem}.csv'))

print("Reached:", set(reached))
print("Not reached:", set(reached).symmetric_difference(set(reachable)))

print(f'{len(set(reached))}/{len(set(reachable))}')
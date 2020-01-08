import angr
import re
from tqdm import tqdm
import claripy

proj = angr.Project('../rers/TrainingSeqReachRers2019/Problem11/Problem11')

# Restrict input
input_chars

state = proj.factory.entry_state()
simgr = proj.factory.simgr(state)

for i in tqdm(range(100)):

    simgr.explore(
        find=lambda s: b"error" in s.posix.dumps(2),
        avoid=lambda s: b"Invalid" in s.posix.dumps(2),
    )

    print("ACTIVE")
    for a in simgr.active:
        print(a.posix.dumps(0), a.posix.dumps(1), a.posix.dumps(2))

    print("FOUND")
    for a in simgr.found:
        print(a.posix.dumps(0), a.posix.dumps(1), a.posix.dumps(2))

    # print(["AVOID"])
    # for a in simgr.avoid:
    #     print(a.posix.dumps(0), a.posix.dumps(1), a.posix.dumps(2))

result = set([a.posix.dumps(2).decode() for a in simgr.found])
reached = set([int(re.search('[0-9]+', r).group(0)) for r in result])

from rers.check_result import parse_csv
reachable, unreachable = parse_csv('rers/TrainingSeqReachRers2019/Problem12/reachability-solution-Problem12.csv')
if len(reachable.difference(reached)) > 0:
    print("Not reached", reachable - reached)
    print("Falsely reached", reached - reachable)
else:
    print("Success")
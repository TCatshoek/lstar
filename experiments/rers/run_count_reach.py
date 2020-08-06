import sys
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

    # errors = aflutils.gather_reached_errors(return_traces=True)
    #
    # # Gather traces leading to error states, per error state
    # traces_by_state = {}
    # for error, trace in errors:
    #     if error in traces_by_state:
    #         traces_by_state[error].append(trace)
    #     else:
    #         traces_by_state[error] = [trace]
    #
    # shortest_to_error = {}
    # for error, traces in traces_by_state.items():
    #     shortest_trace = sorted(traces, key=len)[0]
    #     shortest_to_error[error] = shortest_trace
    #
    # for error, trace in sorted(shortest_to_error.items(), key=lambda x: len(x[1])):
    #     print(error, [int(x) for x in trace])
    #
    # return shortest_to_error

problems = [f'Problem{x}' for x in range(11, 20)]
problemset = "SeqReachabilityRers2020"
rers_basepath = "/home/tom/projects/lstar/rers"
afl_basepath = "/home/tom/afl/2020_fast"

for problem in problems:
    print(problem)
    errors = check_reached(problem, problemset, rers_basepath, afl_basepath)
    print(errors)
    print()
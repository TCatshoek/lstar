from pathlib import Path

from afl.utils import AFLUtils
from rers.check_result import parse_csv
from suls.rerssoconnector import RERSSOConnector
import re

import matplotlib.pyplot as plt

problem = "Problem13"
problemset = "TrainingSeqReachRers2019"
#problemset = "SeqReachabilityRers2020"

basepath = "/home/tom/projects/lstar/rers"
path = f"{basepath}/{problemset}/{problem}/{problem}.so"

sul = RERSSOConnector(path)

afl_basepath = "/home/tom/projects/lstar/afl"
#afl_basepath = "/home/tom/afl/2020_fast"
afl_dir = f'{afl_basepath}/{problemset}/{problem}'
bin_path = f'{afl_basepath}/{problemset}/{problem}/{problem}'

aflutils = AFLUtils(afl_dir,
                    bin_path,
                    [str(x) for x in sul.get_alphabet()],
                    sul)

reached = aflutils.gather_reached_errors(return_time_date=True)

# Filter reached so only the earliest of each error counts
time_error_reached = {}
for (error, time_cur_reached) in reached:
    if error in time_error_reached:
        if time_error_reached[error] > time_cur_reached:
            time_error_reached[error] = time_cur_reached
    else:
        time_error_reached[error] = time_cur_reached

# Sort by time reached
sorted_time_reached = sorted(time_error_reached.items(), key=lambda x: x[1])

# Accumulate which errors were found by which time
acc_err_reached = {}
acc_errs = set()
for err, time in sorted_time_reached:
    acc_errs.add(err)
    acc_err_reached[time] = acc_errs.copy()

sorted_acc_reached = sorted(acc_err_reached.items(), key=lambda x: x[0])
sorted_acc_reached_count = [(time, len(errs)) for (time, errs) in sorted_acc_reached]
times, counts = list(zip(*sorted_acc_reached_count))

# Get some time info from the AFL directory
start_time = aflutils.get_start_date_time()
last_time = aflutils.get_last_date_time()

# Calculate some time stuff for plotting
min_time = min(list(times))
rel_times = [time - min_time for time in times]
rel_start_time = start_time - min_time
rel_last_time = last_time - min_time

plt.step([rel_start_time] + rel_times + [rel_last_time],
         [0] + list(counts) + [max(counts)])
plt.title(f'Error states found in {problemset} - {problem}')
plt.xlabel('time(s)')
plt.ylabel('reached error states')
plt.show()


#
# reachable, unreachable = parse_csv(Path(path).parent.joinpath(f'reachability-solution-{problem}.csv'))
#
# print("Reached:", set(reached))
# print("Not reached:", set(reached).symmetric_difference(set(reachable)))
#

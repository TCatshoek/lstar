from pathlib import Path

from afl.utils import AFLUtils
from rers.check_result import parse_csv
from suls.rerssoconnector import RERSSOConnector
import re

import matplotlib.pyplot as plt

def gather_plot_data(problem, problemset, rers_basepath, afl_basepath):
    rers_path = f"{rers_basepath}/{problemset}/{problem}/{problem}.so"
    afl_dir = f'{afl_basepath}/{problemset}/{problem}'
    bin_path = f'{afl_basepath}/{problemset}/{problem}/{problem}'

    sul = RERSSOConnector(rers_path)

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

    all_times = [rel_start_time] + rel_times + [rel_last_time]
    all_counts = [0] + list(counts) + [max(counts)]

    return all_times, all_counts



#problemset = "TrainingSeqReachRers2019"
problemset = "SeqReachabilityRers2020"
rers_basepath = "/home/tom/projects/lstar/rers"
#afl_basepath = "/home/tom/projects/lstar/afl"
afl_basepath = "/home/tom/afl/2020_fast"

plain_problems = ['Problem11', 'Problem14', 'Problem17']
arith_problems = ['Problem12', 'Problem15', 'Problem18']
datastruct_problems = ['Problem13', 'Problem16', 'Problem19']

seqreach2020problems = {
    'Plain': plain_problems,
    'Arithmetic': arith_problems,
    'Datastructures': datastruct_problems
}

for title, problems in seqreach2020problems.items():
    for problem in problems:
        times, counts = gather_plot_data(problem, problemset, rers_basepath, afl_basepath)
        plt.step(times, counts, label=problem)

    plt.title(f'Error states found in {problemset} - {title}')
    plt.xlabel('time(s)')
    plt.ylabel('reached error states')
    plt.legend()

    plt.show()

afl_basepath = "/home/tom/projects/lstar/afl"
problemset = "TrainingSeqReachRers2019"

seqreach2019trainingproblems = ['Problem11', 'Problem12', 'Problem13']

for problem in seqreach2019trainingproblems:
    times, counts = gather_plot_data(problem, problemset, rers_basepath, afl_basepath)
    print(problem, max(counts))
    plt.step(times, counts, label=problem)

plt.title(f'Error states found in {problemset} - Training')
plt.xlabel('time(s)')
plt.ylabel('reached error states')
plt.legend()

plt.show()
#
# reachable, unreachable = parse_csv(Path(path).parent.joinpath(f'reachability-solution-{problem}.csv'))
#
# print("Reached:", set(reached))
# print("Not reached:", set(reached).symmetric_difference(set(reachable)))
#

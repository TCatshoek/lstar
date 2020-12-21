from afl.utils import AFLUtils
from libfuzzer.utils import CorpusUtils
from suls.rerssoconnector import RERSSOConnector
from pathlib import Path
import re
import matplotlib.pyplot as plt

def check_reached_afl(problem, problemset, rers_basepath, afl_basepath):
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
    # min_time = min(list(times))
    min_time = start_time
    rel_start_time = start_time - min_time
    rel_times = [time - min_time for time in times]
    rel_last_time = last_time - min_time

    all_times = [rel_start_time] + rel_times + [rel_last_time]
    all_counts = [0] + list(counts) + [max(counts)]

    return all_counts, all_times


def check_reached_libfuzzer(problem, problemset, rers_basepath, fuzzer_basepath):
    rers_path = f"{rers_basepath}/{problemset}/{problem}/{problem}.so"
    fuzzer_dir = Path(f'{fuzzer_basepath}/{problemset}/{problem}')

    assert fuzzer_dir.exists(), fuzzer_dir

    sul = RERSSOConnector(rers_path)

    cutils = CorpusUtils(
        corpus_path=fuzzer_dir.joinpath('corpus_errors'),
        fuzzer_path=fuzzer_dir.joinpath(f'{problem}_fuzz'),
        sul=sul
    )

    return cutils.get_plot_data()

problem = "Problem11"
problemset = "TrainingSeqReachRers2019"
libfuzzer_basepath = "/home/tom/afl/thesis_benchmark_2/libFuzzer"
afl_basepath = "afl"
rers_basepath = "../../rers"

libfuzzer_reached = check_reached_libfuzzer(problem, problemset, rers_basepath, libfuzzer_basepath)
afl_reached = check_reached_afl(problem, problemset, rers_basepath, afl_basepath)

if max(libfuzzer_reached[1]) > max(afl_reached[1]):
    afl_reached[0].append(afl_reached[0][-1])
    afl_reached[1].append(libfuzzer_reached[1][-1])
elif max(libfuzzer_reached[1]) < max(afl_reached[1]):
    libfuzzer_reached[0].append(libfuzzer_reached[0][-1])
    libfuzzer_reached[1].append(afl_reached[1][-1])

print(libfuzzer_reached)
print(afl_reached)

plt.step(libfuzzer_reached[1], libfuzzer_reached[0], label="libFuzzer")
plt.step(afl_reached[1], afl_reached[0], label="AFL")
plt.legend()
plt.xlabel("time(s)")
plt.ylabel("Errors reached")
plt.title(f"Fuzzer comparison - {problem}")
plt.show()

# problem = "Problem13"
# problemset = "TrainingSeqReachRers2019"
# libfuzzer_basepath = "/home/tom/afl/thesis_benchmark_2/libFuzzer"
# #afl_basepath = "afl"
# rers_basepath = "../../rers"
#
# libfuzzer_reached = check_reached_libfuzzer(problem, problemset, rers_basepath, libfuzzer_basepath)
# #afl_reached = check_reached_afl(problem, problemset, rers_basepath, afl_basepath)
#
# print(libfuzzer_reached)
# #print(afl_reached)
#
# plt.step(libfuzzer_reached[1], libfuzzer_reached[0], label="libFuzzer")
# #plt.plot(afl_reached[1], afl_reached[0], label="AFL")
# plt.legend()
# plt.title(f"Fuzzer comparison - {problem}")
# plt.show()


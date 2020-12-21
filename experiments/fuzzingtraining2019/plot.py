from afl.utils import AFLUtils
from libfuzzer.utils import CorpusUtils
from suls.rerssoconnector import RERSSOConnector
from pathlib import Path
import re
import matplotlib.pyplot as plt
import tempfile
import pandas as pd

def read_log(path):
    edited_lines = []
    with open(path, 'r') as file:
        lines = file.readlines()

        for line in lines:
            # Extract set if necessary
            result = re.search(r'{(.*)}', line)
            if result:
                edited_lines.append(re.sub(r'{(.*)}',
                                           result.group(1).replace('\'', '').replace(',', ''),
                                           line))
            else:
                edited_lines.append(line)

    tmpfile = tempfile.mktemp('.csv')
    with open(tmpfile, 'w') as file:
        file.writelines(edited_lines)

    return pd.read_csv(tmpfile)

def get_plot_data(log_path, header):
    data = read_log(log_path)
    times = data['# timestamp']
    times = times - min(times)
    counts = data[header]
    return list(times), list(counts)

fuzz_log_paths = [
    'logs/Problem11/Problem11_2020-10-27_15:47:52.log',
    'logs/Problem12/Problem12_2020-10-27_15:49:47.log',
    'logs/Problem13/Problem13_2020-10-27_15:51:58.log'
]

wmethod_log_paths = [
    'logs/Problem11_wmethod/Problem11_2020-10-27_16:38:44.log',
    'logs/Problem12_wmethod/Problem12_2020-10-27_16:39:00.log',
    'logs/Problem13_wmethod/Problem13_2020-10-27_16:49:35.log'
]

figpath = Path('/home/tom/projects/lstar/experiments/figures').joinpath("fuzzlearning")
figpath.mkdir(exist_ok=True)

for n, problem in [(n, f"Problem{n}") for n in range(11, 14)]:
    fuzz_log_path = fuzz_log_paths[n - 11]
    wmethod_log_path = wmethod_log_paths[n - 11]

    fuzz_times, fuzz_states = get_plot_data(fuzz_log_path, ' state_count')
    wmethod_times, wmethod_states = get_plot_data(wmethod_log_path, ' state_count')
    _, fuzz_errors = get_plot_data(fuzz_log_path, ' error_count')
    _, wmethod_errors = get_plot_data(wmethod_log_path, ' error_count')

    fuzz_times.append(max(wmethod_times))
    fuzz_errors.append(fuzz_errors[-1])
    fuzz_states.append(fuzz_states[-1])


    plt.plot(fuzz_times, fuzz_states, label='fuzzer')
    plt.plot(wmethod_times, wmethod_states, label='w-method')

    #plt.xlim(-30, min(max(fuzz_times, wmethod_times), 20 * 60) )

    plt.xlabel("Time(s)")
    plt.ylabel("States")

    plt.legend()

    plt.title(f'Problem {n}')
    # plt.plot(fuzz_times, fuzz_errors)
    # plt.plot(wmethod_times, wmethod_errors)

    plt.savefig(figpath.joinpath(f"{problem}.png"))

    plt.show()
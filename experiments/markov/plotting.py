import pandas as pd
import re
import tempfile
import matplotlib.pyplot as plt

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

def get_error_plot_data(log_path):
    data = read_log(log_path)
    times = data['# timestamp']
    times = times - min(times)
    counts = data[' error_count']
    return times, counts

if __name__ == '__main__':
    pn = 13

    exts = [
        ('_markov.log', 'Markov + W-method 11'),
        ('_standard_3.log', 'W-method 3'),
        ('_standard_9.log', 'W-method 9'),
        ('_standard_11.log', 'W-method 11'),
        #('_normal_12.log', 'W-method 12')
    ]

    base = f'Problem{pn}'

    alpha = 0.8

    max_times = []

    for ext, title in exts:
        cur_path = base + ext
        log = read_log(cur_path)

        times = log['# timestamp']
        times = times - min(times)
        times = list(times)
        max_times.append(max(times))

        states = list(log[' state_count'])
        if max(times) < 3600:
            states.append(max(states))
            times.append(3600)

        plt.step(times, states, label=title, alpha=alpha)

    plt.legend(loc='lower right')
    plt.title(f"Problem {pn}")
    plt.xlabel('time(s)')
    plt.ylabel('reached states')

    if pn == 11:
        plt.xlim(left=-1, right=10)
    else:
    #     plt.xlim(left=plt.xlim()[0], right=min(max_times))
        plt.xlim(left=-100, right = 3600)

    plt.savefig(f'problem{pn}_markov')
    plt.show()

    #
    #
    # path = f'Problem{pn}_markov.log'
    # times, counts = get_error_plot_data(path)
    #
    # path2 = f'Problem{pn}_markov_baseline.log'
    # times2, counts2 = get_error_plot_data(path)
    #
    # log1 = read_log(path)
    # log2 = read_log(path2)
    #
    # times1 = log1['# timestamp']
    # times1 = times1 - min(times1)
    # times1 = times1 #/ 3600
    # times2 = log2['# timestamp']
    # times2 = times2 - min(times2)
    # times2 = times2 #/ 3600
    #
    # states1 = log1[' state_count']
    # states2 = log2[' state_count']
    #
    # alpha = 0.8
    # plt.step(times1, states1, label='Markov + W-method', alpha=alpha)
    # plt.step(times2, states2, label='W-Method', alpha=alpha)
    #
    # plt.legend()
    #
    # plt.title(f"Problem {pn}")
    #
    # plt.xlabel('time(s)')
    # plt.ylabel('reached states')
    #
    # if pn == 11:
    #     plt.xlim(left=-1, right=10)
    # else:
    #     plt.xlim(left=plt.xlim()[0], right=min(max(times2), max(times1)))
    #
    # plt.savefig(f'problem{pn}_markov')
    # plt.show()


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

    path = f'mutatingproblem{pn}/Problem{pn}_normal.log'
    times, counts = get_error_plot_data(path)

    path2 = f'mutatingproblem{pn}/Problem{pn}_mutating.log'
    times2, counts2 = get_error_plot_data(path)

    log1 = read_log(path)
    log2 = read_log(path2)

    times1 = log1['# timestamp']
    times1 = times1 - min(times1)
    times1 = times1 #/ 3600
    times2 = log2['# timestamp']
    times2 = times2 - min(times2)
    times2 = times2 #/ 3600

    states1 = log1[' state_count']
    states2 = log2[' state_count']

    plt.step(times1, states1, label='W-method')
    plt.step(times2, states2, label='Mutating + W-method')

    plt.legend()

    plt.title(f"Problem {pn}")

    plt.xlabel('time(s)')
    plt.ylabel('reached states')

    plt.xlim(left=0, right=min(max(times2), max(times1)))

    plt.show()


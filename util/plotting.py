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
    path = '/home/tom/projects/lstar/experiments/learningfuzzing/Problem13_2020-08-01_16:59:43.log'

    times, counts = get_error_plot_data(path)
    plt.step(times, counts)


    plt.xlabel('time(s)')
    plt.ylabel('reached error states')

    #plt.xlim(left=0, right=30000)

    plt.show()


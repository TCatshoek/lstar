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

def get_plot_data(log_path, header):
    data = read_log(log_path)
    times = data['# timestamp']
    times = times - min(times)
    counts = data[header]
    return times, counts

if __name__ == '__main__':
    pn = 13

    path = f'Problem{pn}_mutation_cluster.log'
    times, counts = get_plot_data(path, ' state_count')

    path2 = f'Problem{pn}_mutation_nocluster.log'
    times2, counts2 = get_plot_data(path, ' state_count')

    log1 = read_log(path)
    log2 = read_log(path2)

    times1 = log1['# timestamp']
    times1 = times1 - min(times1)
    times1 = times1 #/ 60
    times2 = log2['# timestamp']
    times2 = times2 - min(times2)
    times2 = times2 #/ 60

    states1 = log1[' state_count']
    states2 = log2[' state_count']

    alpha = 0.8
    plt.step(times1, states1, label='With clustering', alpha=alpha)
    plt.step(times2, states2, label='Without clustering', alpha=alpha)

    plt.legend()

    plt.title(f"Problem {pn}")

    if pn == 11:
        #plt.xlim(left=-0.5, right=min(max(times2), max(times1)))
        print('lol')
    else:
        plt.xlim(left=plt.ylim()[0], right=min(max(times2), max(times1)))

    plt.xlabel('time(s)')
    plt.ylabel('reached states')

    plt.savefig(f'problem_{pn}_mutatingcomparison')
    plt.show()


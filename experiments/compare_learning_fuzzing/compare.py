from afl.generate_reached_errors_plot import gather_plot_data
from util.plotting import get_error_plot_data
import matplotlib.pyplot as plt

p11log = '/home/tom/projects/lstar/experiments/learningfuzzing/Problem11_2020-08-01_16:54:59.log'
p12log = '/home/tom/projects/lstar/experiments/learningfuzzing/Problem12_2020-08-01_16:54:02.log'
p13log = '/home/tom/projects/lstar/experiments/learningfuzzing/Problem13_2020-08-01_16:59:43.log'

logs = [p11log, p12log, p13log]

afl_basepath = "/home/tom/projects/lstar/afl"
problemset = "TrainingSeqReachRers2019"
rers_basepath = "/home/tom/projects/lstar/rers"
figpath = '/home/tom/projects/lstar/experiments/figures/rers_afl_plots'

seqreach2019trainingproblems = ['Problem11', 'Problem12', 'Problem13']

for idx, problem in enumerate(seqreach2019trainingproblems):
    afl_times, afl_counts = gather_plot_data(problem, problemset, rers_basepath, afl_basepath)
    ttt_times, ttt_counts = get_error_plot_data(logs[idx])

    plt.step(afl_times, afl_counts, label='afl')
    plt.step(ttt_times, ttt_counts, label='ttt')

    plt.title(f'Method comparison - {problemset} - {problem}')
    plt.xlabel('time(s)')
    plt.ylabel('reached error states')
    plt.legend()

    plt.savefig(f"{figpath}/{problem}_comparison.png")
    plt.show()

    # ------------------ Zoomed

    plt.step(afl_times, afl_counts, label='afl')
    plt.step(ttt_times, ttt_counts, label='ttt')

    plt.xlim(left=0, right=min(max(afl_times), max(ttt_times)))

    plt.title(f'Method comparison - {problemset} - {problem}')
    plt.xlabel('time(s)')
    plt.ylabel('reached error states')
    plt.legend()

    # plt.savefig(f"{figpath}/{problem}_comparison_zoomed.svg")
    plt.show()
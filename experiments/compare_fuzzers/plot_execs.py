from afl.utils import AFLUtils
from libfuzzer.utils import CorpusUtils
from suls.rerssoconnector import RERSSOConnector
from pathlib import Path
import re
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from scipy.integrate import simps, trapz

problem = "Problem13"
problemset = "TrainingSeqReachRers2019"
libfuzzer_basepath = "/home/tom/afl/thesis_benchmark_3/libFuzzer"
afl_basepath = "afl"
rers_basepath = "../../rers"


def getAFLFuzzerPlotData(problem):
    plotdatapath = Path(afl_basepath).joinpath(problemset).joinpath(problem).joinpath("output/plot_data")

    plotdata = pd.read_csv(plotdatapath)

    return plotdata["# unix_time"] - min(plotdata['# unix_time']), plotdata[' execs_per_sec']


def getAFLFuzzerPlotDataCumulative(problem):
    plotdatapath = Path(afl_basepath).joinpath(problemset).joinpath(problem).joinpath("output/plot_data")

    plotdata = pd.read_csv(plotdatapath)

    return plotdata["# unix_time"] - min(plotdata['# unix_time']), plotdata[' execs_per_sec']


def getLibFuzzerPlotData(problem):
    plotdatapath = Path(libfuzzer_basepath) \
        .joinpath(problemset) \
        .joinpath(problem) \
        .joinpath(f"log_{problem}.txt")

    plotdata = pd.read_csv(plotdatapath, error_bad_lines=False, header=None, dtype=object)
    times = plotdata.iloc[:, 0]
    lines = plotdata.iloc[:, 1]
    lineswithtimes = zip(times, lines)
    execspswithtimes = [(time, match.group(1)) for time, match in
                        [(time, re.search("exec\/s: (\d+)", line)) for time, line in lineswithtimes]
                        if match is not None]

    times, execsps = zip(*execspswithtimes)
    times = [float(a[0:-2] + "." + b) for [a, b] in [x.split(".") for x in times]]
    times = np.array(times) - np.min(times)
    execsps = [int(x) for x in execsps]

    return times, execsps


def getLibFuzzerPlotDataCumulative(problem):
    plotdatapath = Path(libfuzzer_basepath) \
        .joinpath(problemset) \
        .joinpath(problem) \
        .joinpath(f"log_{problem}.txt")

    plotdata = pd.read_csv(plotdatapath, error_bad_lines=False, header=None, dtype=object)
    times = plotdata.iloc[:, 0]
    lines = plotdata.iloc[:, 1]
    lineswithtimes = zip(times, lines)
    execspswithtimes = [(time, match.group(1)) for time, match in
                        [(time, re.search("#(\d+)", line)) for time, line in lineswithtimes]
                        if match is not None]

    times, execsps = zip(*execspswithtimes)
    times = [float(a[0:-2] + "." + b) for [a, b] in [x.split(".") for x in times]]
    times = np.array(times) - np.min(times)
    execsps = [int(x) for x in execsps]

    return times, execsps


def integrate(x, y):
    return [(trapz(x[0:i], y[0:i]), y[i]) for i in range(1, len(x))]


Path('figures').mkdir(exist_ok=True)

for problem, n in [(f"Problem{n}", n) for n in range(11, 14)]:
    lfuzztimes, lfuzzexecs = getLibFuzzerPlotData(problem)
    afltimes, aflexecs = getAFLFuzzerPlotData(problem)

    plt.plot(lfuzztimes, lfuzzexecs, label="libFuzzer")
    plt.plot(afltimes, aflexecs, label="AFL")

    plt.title(f"Execs/s comparison - problem {n}")
    plt.ylabel("Execs/s")
    plt.xlabel("Time(s)")
    plt.xlim(plt.xlim()[0], min(max(lfuzztimes), max(afltimes)))
    plt.legend()
    plt.savefig(f"figures/problem{n}persec.png")
    plt.show()

    lfuzztotalexecs, lfuzztotaltimes = zip(*integrate(lfuzzexecs, lfuzztimes))
    afltotalexecs, afltotaltimes = zip(*integrate(list(aflexecs), list(afltimes)))

    plt.plot(lfuzztotaltimes, lfuzztotalexecs, label="libFuzzer")
    plt.plot(afltotaltimes, afltotalexecs, label="AFL")
    plt.ylabel("Execs/s")
    plt.xlabel("Time(s)")
    plt.xlim(plt.xlim()[0], min(max(lfuzztotaltimes), max(afltotaltimes)))
    plt.title(f"Total execs over time - problem {n}")
    plt.legend()
    plt.savefig(f"figures/problem{n}total.png")
    plt.show()

from rers.check_ltl_result import compare_results
from util.plotting import read_log
from pathlib import Path
import pandas as pd

problems = [f'Problem{n}' for n in range(1, 10)]
problemsets = ['SeqLtlRers2019', 'SeqLtlRers2020']

def get_data(problem, problemset):
    return read_log(Path('logs').joinpath(problemset).joinpath(f'{problem}.log'))

def get_score(problem, problemset):
    solutionspath = f'/home/tom/projects/lstar/rers/{problemset}/{problem}/constraints-solution-{problem}.txt'
    resultspath = Path('results').joinpath(problemset).joinpath(f'{problem}.csv')
    correct, total = compare_results(resultspath, solutionspath)
    return correct, total

def process(data):
    # Get time passed
    timestamps = data["# timestamp"]
    dtime = timestamps.max() - timestamps.min()

    # Get n states found
    n_states = data[' state_count'].max()

    return [dtime, n_states]

if __name__ == "__main__":
    data = {}
    problemset = problemsets[0]

    for idx, problem in enumerate(problems):
        correct, total = get_score(problem, problemset)
        data[f'Problem {idx + 1}'] = process(get_data(problem, problemset)) + [f'{correct}/{total}']

    df = pd.DataFrame(data=data).T
    df.columns = ['Time(m:s)', 'States', 'Score']
    df['Time(m:s)'] = pd.to_datetime(df['Time(m:s)'], unit='s').apply(lambda x: x.strftime('%M:%S'))
    print(df.to_latex())

    data = {}
    problemset = problemsets[1]

    for idx, problem in enumerate(problems):
        data[f'Problem {idx + 1}'] = process(get_data(problem, problemset)) + ['?/10']

    df = pd.DataFrame(data=data).T
    df.columns = ['Time(m:s)', 'States', 'Score']
    df['Time(m:s)'] = pd.to_datetime(df['Time(m:s)'], unit='s').apply(lambda x: x.strftime('%M:%S'))
    print(df.to_latex())
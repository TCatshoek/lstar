import argparse
from pathlib import Path

parser = argparse.ArgumentParser(description='generates solution files for the individual problems from a big results file')
parser.add_argument('file', type=str)
parser.add_argument('problems_dir', type=str)

args = parser.parse_args()

solutions = {}
# Read solutions file
with Path(args.file).open('r') as f:
    for line in f.readlines():

        problem, property_no, answer = line.split(',')

        if problem not in solutions:
            solutions[problem] = {}

        solutions[problem][property_no] = 'true' if answer.strip() == 'yes' else 'false'

for problem_dir in Path(args.problems_dir).glob('Problem*'):
    problem_no = problem_dir.stem.replace('Problem', '')

    with problem_dir.joinpath(f'constraints-solution-{problem_dir.stem}.txt').open('w') as f:
        for property_no, answer in sorted(solutions[problem_no].items(), key=lambda x: int(x[0])):
            f.write(f'{property_no}, {answer}\n')
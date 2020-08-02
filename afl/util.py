from pathlib import Path
import subprocess
from subprocess import Popen, PIPE
import re
from functools import lru_cache
from math import ceil
# def decode_afl_file(path, parse_bin_path):
#     path = Path(path).resolve().absolute()
#     # Parse the input file like the RERS program would, appending a 0 to make sure it terminates
#     try:
#         result = subprocess.run(f"cat {path} | sed 's/$/ 0/' | {parse_bin_path}", shell=True, capture_output=True, timeout=1)
#         stdout = result.stdout.decode()
#         return [x.strip() for x in stdout.split('\n')]
#     except subprocess.TimeoutExpired:
#         print("Could not parse", path)
#         return []

@lru_cache
def decode_afl_file(path, parse_bin_path, afl_target_bin_path, minimize=False):
    path = Path(path).resolve().absolute()

    if(minimize):
        minimized_path = Path('/tmp/minimized')
        minimized_path.mkdir(exist_ok=True)

        # Get all already minimized files
        already_minimized = [x.stem for x in minimized_path.glob('**/id:*')]

        # Minimize if necessary
        if path.stem not in already_minimized:
            result = subprocess.run(['afl-tmin',
                             '-i', path,
                             '-o', minimized_path.joinpath(path.stem),
                             '--', afl_target_bin_path],
                           capture_output=True)
            print("Minimized", path.stem)
            assert result.returncode == 0

        # Redirect to minimized testcase
        path = minimized_path.joinpath(path.stem)

    # Parse the input file like the RERS program would
    # The parse program needs an upper bound on how many characters to read,
    # so we take the amount of bytes in the input file
    try:
        n = len(path.open('rb').read()) + 2
        result = subprocess.run(f"cat {path} | sed '$a 0' | {parse_bin_path} {n}", shell=True, capture_output=True,
                                timeout=1)
        stdout = result.stdout.decode()
        return [x.strip() for x in stdout.split('\n')]
    except subprocess.TimeoutExpired:
        print("Couldn't parse", path.stem)
        return []

def strip_invalid(input, alphabet):
    return [x for x in input if x in alphabet]

# # Trims the end of the given testcase such that it is the shortest possible while keeping the same output
# def trim(testcase, sul):
#     og_output = sul.process_input(testcase)
#     og_len = len(testcase)
#
#     lower = 0
#     upper = og_len
#
#     cur_idx = upper
#
#     while lower != upper and abs(lower - upper) > 1:
#         cur_output = sul.process_input(testcase[0:cur_idx])
#
#         if cur_output == og_output:
#             upper = cur_idx
#         else:
#             lower = cur_idx
#
#         cur_idx = (lower + upper) // 2
#
#     return testcase[0:upper + 1]

def trim(testcase, sul):
    og_output = sul.process_input(testcase)
    og_len = len(testcase)

    left = 0
    right = og_len - 1

    while left != right:
        cur_idx = ceil((left + right) / 2)
        cur_output = sul.process_input(testcase[0:cur_idx])

        if cur_output == og_output:
            right = cur_idx - 1
        else:
            left = cur_idx

    return testcase[0:cur_idx + 1]

def _generate_dictionary(alphabet, workdir):
    dict_content = ' '.join([str(x) for x in sul.get_alphabet()]) + ' 0'
    dict_content = dict_content.split(' ')
    dict_content = [f"\"{x} \"\n" for x in dict_content]
    with open(workdir.joinpath("dictionary.dict"), 'w') as file:
        file.writelines(dict_content)

def _generate_initial_input(workdir):
    workdir.joinpath("input").mkdir(exist_ok=True)
    subprocess.run(f"echo '0' > input/1.txt", shell=True, cwd=self.workdir)

def collect_errors(afl_target_bin_path, output_folder):
    paths = [x for x in Path('../afl/output').glob('**/id:*') if
             x.match(f'**/crashes/**') and not x.match('**/leaner*/**')]

    errors = set()

    for path in paths:
        result = subprocess.run(f"cat {path} | {afl_target_bin_path}", shell=True, capture_output=True)
        match = re.search('error_[0-9]+', result.stderr.decode()).group()
        assert match is not None
        errors.add(match)

    return errors


if __name__ == "__main__":
    # errors = collect_errors('/home/tom/projects/lstar/afl/TrainingSeqReachRers2019/Problem12/Problem12',
    #                '/home/tom/projects/lstar/afl/output')
    path = "output/fuzzer02/crashes/id:000006,sig:06,src:000027+000055,op:splice,rep:4"
    print(decode_afl_file(path, './parse', 'TrainingSeqReachRers2019/Problem12/Problem12'))

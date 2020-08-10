from pathlib import Path
import subprocess
import shutil
from multiprocessing import Pool, cpu_count

from rers.check_result import parse_csv
from suls.rerssoconnector import RERSSOConnector

import re

def parse_file(path):
    if Path(path).exists():
        with Path(path).open('rb') as file:
            return [int(x) for x in file.read()]
    else:
        print(f"{path} eaten by running afl instance?")

def get_name(testcase, prefix_offset=-3):
    return f'{testcase.parts[prefix_offset]}/{testcase.name}'

def run_minimize(testcase, outdir, binary_path):
    outdir = outdir.joinpath(testcase.parts[-3])
    outdir.mkdir(exist_ok=True)
    subprocess.run(['afl-tmin',
                    '-i', testcase,
                    '-o', outdir.joinpath(testcase.name),
                    '--', binary_path],
                   stderr=subprocess.DEVNULL)

def strip_invalid(testcase, alphabet):
    alphabet = [int(x) for x in alphabet]
    return [str(x) for x in testcase if x in alphabet]

def ensure_crash(testcase, sul):
    # testbytes = str(bytes(testcase)).strip('"b').strip('\'')
    # result = subprocess.run(f'echo -n -e \"{testbytes}\" | {binary}'
    #                         , shell=True
    #                         , capture_output=True)
    # return 'error' in result.stderr.decode()
    testcase = [str(x) for x in testcase]
    output = sul.process_input(testcase)
    return 'error' in output

class AFLUtils:
    # The root directory is the directory with afl's input and output folder
    # Binary path is the binary fuzzed by afl
    def __init__(self, root_dir, binary_path, alphabet, sul=None):
        self.root_dir = Path(root_dir)
        assert self.root_dir.exists(), f'{root_dir} does not exists'

        self.binary_path = Path(binary_path)
        assert self.binary_path.exists(), f'{binary_path} does not exists'

        self.alphabet = alphabet

        # Cache minimized testcases so we don't have to minimize them again
        self.error_cache = {}
        self.queue_cache = {}

        self.sul = sul

    def get_minimized_testset(self):
        # First, gather all queue files
        collection_dir = self.root_dir.joinpath("collected")
        collection_dir.mkdir(exist_ok=True)

        queue_files = [x for x in self.root_dir.joinpath("output").glob('**/id:*') if
             x.match(f'**/queue/**') and not x.match('**/learner*/**')]

        for idx, queue_file in enumerate(queue_files):
            shutil.copy(str(queue_file), str(collection_dir.joinpath(f'{queue_file.name}_{idx}')))

        # Then, we run afl-cmin to minimize the test set while keeping the same coverage
        minimized_dir = self.root_dir.joinpath("minimized")
        minimized_dir.mkdir(exist_ok=True)

        subprocess.run(['afl-cmin',
                        '-i', collection_dir,
                        '-o', minimized_dir,
                        '--', self.binary_path], check=True)

        # Next, we use afl-tmin to trim all test cases to the smallest possible size
        minimized_and_trimmed_dir = self.root_dir.joinpath("minimized_trimmed")
        minimized_and_trimmed_dir.mkdir(exist_ok=True)

        args = [(x, minimized_and_trimmed_dir, self.binary_path)
                for x in minimized_dir.glob('id:*')]

        with Pool(cpu_count()) as pool:
            pool.starmap(run_minimize, args)

        # We gather all the minimized, trimmed testcases and load them
        testcases = [parse_file(path) for path in minimized_and_trimmed_dir.glob("id:*")]

        # Remove characters not in alphabet and convert to strings
        testcases = [str(strip_invalid(testcase, self.alphabet)) for testcase in testcases]

        print(f'Imported {len(testcases)} queue test cases!')

        # And lastly clean up our temporary directories
        shutil.rmtree(minimized_dir)
        shutil.rmtree(minimized_and_trimmed_dir)

        return testcases

    def get_testset(self):
        queue_files = [x for x in self.root_dir.joinpath("output").glob('**/id:*') if
                       x.match(f'**/queue/**') and not x.match('**/learner*/**')
                       and get_name(x) not in self.queue_cache]

        for queue_file in queue_files:
            name = get_name(queue_file)
            self.queue_cache[name] = parse_file(queue_file)

        testcases = self.queue_cache.values()

        # Remove characters not in alphabet and convert to strings
        testcases = [strip_invalid(testcase, self.alphabet) for testcase in testcases]

        # Remove zero length testcases
        testcases = [x for x in testcases if len(x) > 0]

        print(f"Imported {len(testcases)} queue test cases!")

        return testcases


    def get_minimized_crashset(self):
        trimmed_dir = self.root_dir.joinpath("trimmed")
        trimmed_dir.mkdir(exist_ok=True)

        # Gather crashes in output directory
        crashes = [x for x in self.root_dir.joinpath("output").glob('**/id:*') if
                   x.match(f'**/crashes/**') and not x.match('**/learner*/**')
                   and get_name(x) not in self.error_cache]

        # Minimize the crashing inputs
        args = [(x, trimmed_dir, self.binary_path)
                for x in crashes]

        with Pool(cpu_count()) as pool:
            pool.starmap(run_minimize, args)

        # Add trimmed testcases to cache
        for path in trimmed_dir.glob("**/id:*"):
            testcase = parse_file(path)
            name = get_name(path, prefix_offset=-2)

            assert name not in self.error_cache

            self.error_cache[name] = testcase

        # Load the trimmed testcases
        testcases = self.error_cache.values()

        # Remove characters not in alphabet and convert to strings
        testcases = [strip_invalid(testcase, self.alphabet) for testcase in testcases]

        # Remove zero length testcases
        testcases = [x for x in testcases if len(x) > 0]

        # Sanity check if crashing test cases do actually crash
        if self.sul:
            for testcase in testcases:
                self.sul.reset()
                assert ensure_crash(testcase, self.sul)

        # And lastly clean up our temporary directories
        shutil.rmtree(trimmed_dir)

        print(f'Imported {len(testcases)} crashing test cases!')

        return testcases

    def get_crashset(self, return_time_date=False):
        crashset = []
        time_dates = []

        # Gather crashes in output directory
        crashes = [x for x in self.root_dir.joinpath("output").glob('**/id:*') if
                   (x.match(f'**/crashes/**') or 'crashes' in str(x)) and not x.match('**/learner*/**') and get_name(x) not in self.error_cache]

        for crash in crashes:
            if return_time_date:
                time_dates.append(crash.stat().st_mtime)
            crashset.append(parse_file(crash))

        # Remove characters not in alphabet and convert to strings
        crashset = [strip_invalid(testcase, self.alphabet) for testcase in crashset]
        crashset = [[str(y) for y in x] for x in crashset]

        # Remove zero length testcases
        crashset = [x for x in crashset if len(x) > 0]

        # Check what errors are reached
        reached_errors = set()
        for crashing_input in crashset:
            crashing_input = [str(x) for x in crashing_input]
            self.sul.reset()
            output = self.sul.process_input(crashing_input)
            if 'error' in output:
                reached_errors.add(output)

        print(f'Imported {len(crashset)} crashing test cases!',
              f'{len(reached_errors)} Unique crashes')

        if return_time_date:
            return crashset, time_dates
        else:
            return crashset

    def gather_reached_errors(self, return_time_date=False, return_traces=False):
        errors = []

        for (crashing_input, last_modified) in list(zip(*self.get_crashset(return_time_date=True))):
            crashing_input = [str(x) for x in crashing_input]
            self.sul.reset()
            output = self.sul.process_input(crashing_input)

            to_append = tuple()

            if "error" in output:
                to_append += (output,)

                if return_traces:
                    to_append += (crashing_input,)

                if return_time_date:
                    to_append += (last_modified,)

                if len(to_append) == 1:
                    to_append = to_append[0]

                errors.append(to_append)
            else:
                print("No error for ", crashing_input, ':(')


        return errors

    # Attempts to guess the time afl started
    # by looking at when the original file was copied
    # to the output dir
    def get_start_date_time(self):
        origs = [x for x in self.root_dir.joinpath("output").glob('**/id:000000*orig*') if
                   x.match(f'**/queue/**') and not x.match('**/learner*/**')]

        times = [x.stat().st_mtime for x in origs]
        return min(times)

    def get_last_date_time(self):
        all = [x for x in self.root_dir.joinpath("output").glob('**/id:*') if not re.search('/learner\d+/', str(x))]

        # divide per parent folder
        per_parent = {}
        for file in all:
            if file.parent in per_parent:
                per_parent[file.parent].append(file)
            else:
                per_parent[file.parent] = [file]

        # Do some preparation to prevent having to check *ALL* the files
        max_ids = []
        for paths in per_parent.values():
            sorted_paths = sorted(paths, key=lambda x: int(re.search('id:(\d+)', str(x)).group(1)))
            max_ids.append(sorted_paths[-1])

        times = [x.stat().st_mtime for x in max_ids]

        return max(times)

    def minimize_error_trace(self, trace):
        trace = list(trace)
        trimmed_trace = trace.copy()
        deletion_shift = 0
        inv_idxes = []
        # Remove "invalid output"s
        for i in range(1, len(trace) + 1):
            self.sul.reset()
            output = self.sul.process_input(trace[0:i])
            if output == "invalid_input":
                inv_idxes.append(i - 1)
        for inv_idx in inv_idxes:
            del trimmed_trace[inv_idx - deletion_shift]
            deletion_shift += 1

        self.sul.reset()
        og_output = self.sul.process_input(trace)
        self.sul.reset()
        new_output = self.sul.process_input(trimmed_trace)

        assert og_output == new_output
        assert 'error' in og_output

        return trimmed_trace



if __name__ == "__main__":
    problem = "Problem12"
    problemset = "TrainingSeqReachRers2019"

    path = f"/home/tom/projects/lstar/rers/{problemset}/{problem}/{problem}.so"

    sul = RERSSOConnector(path)

    afl_dir = f'/home/tom/projects/lstar/afl/{problemset}/{problem}'
    bin_path = f'/home/tom/projects/lstar/afl/{problemset}/{problem}/{problem}'

    aflutils = AFLUtils(afl_dir,
                        bin_path,
                        [str(x) for x in sul.get_alphabet()],
                        sul)

    reached = [int(re.sub('error_', '', x)) for x in aflutils.gather_reached_errors()]

    reachable, unreachable = parse_csv(Path(path).parent.joinpath(f'reachability-solution-{problem}.csv'))

    print("Reached:", set(reached))
    print("Not reached:", set(reached).symmetric_difference(set(reachable)))


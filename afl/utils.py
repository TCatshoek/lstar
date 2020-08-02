from pathlib import Path
import subprocess
import shutil
from multiprocessing import Pool, cpu_count


def parse_file(path):
    with Path(path).open('rb') as file:
        return [int(x) for x in file.read()]


def run_minimize(testcase, outdir, binary_path):
    subprocess.run(['afl-tmin',
                    '-i', testcase,
                    '-o', outdir.joinpath(testcase.name),
                    '--', binary_path],
                   stderr=subprocess.DEVNULL)

def strip_invalid(testcase, alphabet):
    return [x for x in testcase if x in alphabet]

def ensure_crash(binary, testcase):
    testbytes = str(bytes(testcase)).strip('"b').strip('\'')
    result = subprocess.run(f'echo -n -e \"{testbytes}\" | {binary}'
                            , shell=True
                            , capture_output=True)
    return 'error' in result.stderr.decode()

class AFLUtils:
    # The root directory is the directory with afl's input and output folder
    # Binary path is the binary fuzzed by afl
    def __init__(self, root_dir, binary_path, alphabet):
        self.root_dir = Path(root_dir)
        assert self.root_dir.exists()

        self.binary_path = Path(binary_path)
        assert self.binary_path.exists()

        self.alphabet = alphabet

    def get_minimized_testset(self):
        # First, we run afl-cmin to minimize the test set while keeping the same coverage
        minimized_dir = self.root_dir.joinpath("minimized")
        minimized_dir.mkdir(exist_ok=True)

        subprocess.run(['afl-cmin',
                        '-i', self.root_dir.joinpath("output"),
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

    def get_minimized_crashset(self):
        trimmed_dir = self.root_dir.joinpath("trimmed")
        trimmed_dir.mkdir(exist_ok=True)

        # Gather crashes in output directory
        crashes = [x for x in self.root_dir.joinpath("output").glob('**/id:*') if
                   x.match(f'**/crashes/**') and not x.match('**/leaner*/**')]

        # Minimize the crashing inputs
        args = [(x, trimmed_dir, self.binary_path)
                for x in crashes]

        with Pool(cpu_count()) as pool:
            pool.starmap(run_minimize, args)

        # Load the trimmed testcases
        testcases = [parse_file(path) for path in trimmed_dir.glob("id:*")]

        # Remove characters not in alphabet and convert to strings
        testcases = [strip_invalid(testcase, self.alphabet) for testcase in testcases]

        # Remove zero length testcases
        testcases = [x for x in testcases if len(x) > 0]

        # Sanity check if crashing test cases do actually crash
        # Disabled because they spam core dumps
        # for testcase in testcases:
        #     assert ensure_crash(self.binary_path, testcase)

        print(f'Imported {len(testcases)} crashing test cases!')

        return testcases


if __name__ == "__main__":
    path = "/tmp/afltest/12test/output/crashes/id:000069,sig:06,src:000250+000362,op:splice,rep:4"
    path = "/home/tom/afl/cminned/12test/"

    aflutils = AFLUtils(path,
                        path + "Problem12afl",
                        [1,2,3,4,5,6,7,8,9,10])

    #testset = aflutils.get_minimized_testset()
    crashset = aflutils.get_minimized_crashset()

    print(crashset)

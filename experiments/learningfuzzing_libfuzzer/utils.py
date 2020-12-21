from pathlib import Path

from rers.check_result import parse_csv
from suls.rerssoconnector import RERSSOConnector
import subprocess


def parse_file(path):
    if Path(path).exists():
        with Path(path).open('rb') as file:
            tmp = [int(x) for x in file.read()]
            return tmp
    else:
        #print(f"{path} does not exist")
        return []


def strip_invalid(testcase, alphabet):
    alphabet = [int(x) for x in alphabet]
    return [str(x) for x in testcase if x in alphabet]


class CorpusUtils:
    def __init__(self, corpus_path, fuzzer_path, sul):
        self.corpus_path = Path(corpus_path)
        self.fuzzer_path = Path(fuzzer_path)
        self.minimized_corpus_path = None
        self.sul = sul
        self.alphabet = sul.get_alphabet()

    def minimize_corpus(self, minimized_dir=None, overwrite=False):
        if minimized_dir is None:
            minimized_dir = self.corpus_path.parent.joinpath('minimized')
        else:
            minimized_dir = Path(minimized_dir)

        if minimized_dir.exists() and not overwrite:
            print("Minimized corpus already exists, skipping minimization")
            self.minimized_corpus_path = minimized_dir
            return

        minimized_dir.mkdir()

        min_result = subprocess.run([self.fuzzer_path, '-merge=1', minimized_dir, self.corpus_path])
        assert min_result.returncode == 0, f"Corpus minimization failed: {min_result.stderr.decode()}"

        self.minimized_corpus_path = minimized_dir

        return minimized_dir

    def gather_testcases(self, return_time_date=False, minimized=False):
        if minimized:
            corpus_path = self.minimized_corpus_path
        else:
            corpus_path = self.corpus_path

        #testcases = []
        print(len(list(corpus_path.glob('*'))), "testcases in corpus directory")

        def testcases():
            for testcase_file in corpus_path.glob('*'):
                testcase = strip_invalid(parse_file(testcase_file), self.alphabet)

                if len(testcase) > 0:
                    if return_time_date:
                        time_date = testcase_file.stat().st_mtime
                        #testcases.append((testcase, time_date))
                        yield (testcase, time_date)
                    else:
                        #testcases.append(testcase)
                        yield testcase

        return testcases()

    def get_plot_data(self):
        print(f"Gathering plot data from {self.corpus_path}")
        # Gather testcases from corpus
        testcases_w_time = self.gather_testcases(return_time_date=True)

        # Get the start and end times
        start_time, end_time = None, None
        for _, time in testcases_w_time:
            if start_time is None or time < start_time:
                start_time = time
            if end_time is None or time > end_time:
                end_time = time

        # Filter on crashing testcases
        crashing_w_time = [(testcase, time, output) for testcase, time in testcases_w_time
                           if (output := self.extract_error(testcase)) is not None]

        # Group by error
        by_error = {}
        for testcase, time, output in crashing_w_time:
            if output not in by_error:
                by_error[output] = []
            by_error[output].append((testcase, time))

        # Sort so we can find the earliest time an error was reached
        by_error_earliest = {}
        for error, testcases_w_time_by_error in by_error.items():
            by_error_earliest[error] = list(sorted(testcases_w_time_by_error, key=lambda x: x[1]))[0]

        # Accumulate errors over time
        n_errors_reached = [0]
        times_errors_reached = [0]
        error_counter = 0
        for error, (testcase, time) in by_error_earliest.items():
            error_counter += 1
            n_errors_reached.append(error_counter)
            times_errors_reached.append(time - start_time)

        n_errors_reached.append(max(n_errors_reached))
        times_errors_reached.append(end_time - start_time)

        return n_errors_reached, sorted(times_errors_reached)

    def extract_error(self, testcase):
        self.sul.reset()
        output = self.sul.process_input(testcase)
        if 'error' in output:
            return output
        else:
            return None

    def extract_errors(self, crashes):
        cs = set()
        for c in crashes:
            if c is not None:
                # print(c)
                self.sul.reset()
                output = self.sul.process_input(c)
                # print(output)
                if 'error' in output:
                    cs.add(output)
        return cs


if __name__ == "__main__":
    import matplotlib.pyplot as plt

    problem = "Problem17"
    path = Path(f'/home/tom/afl/libfuzz/SeqReachabilityRers2020/{problem}')
    # path = Path(f'/home/tom/projects/lstar/libfuzzer/TrainingSeqReachRers2019/{problem}')
    assert path.exists()
    sul = RERSSOConnector(f'/home/tom/projects/lstar/rers/SeqReachabilityRers2020/{problem}/{problem}.so')
    # sul = RERSSOConnector(f'/home/tom/projects/lstar/rers/TrainingSeqReachRers2019/{problem}/{problem}.so')

    cutils = CorpusUtils(
        corpus_path=path.joinpath('corpus'),
        fuzzer_path=path.joinpath(f'{problem}_fuzz'),
        sul=sul
    )

    # minimized_dir = cutils.minimize_corpus()
    n_reached, times_reached = cutils.get_plot_data()
    plt.step([x / 3600 for x in times_reached], n_reached)
    plt.show()
    #
    # crashing_inputs = cutils.gather_crashes()
    #
    # reached_errs = [x.replace('error_', '') for x in cutils.extract_errors(crashing_inputs)]
    #
    # reachable, unreachable = parse_csv('/home/tom/projects/lstar/rers/TrainingSeqReachRers2019/Problem12/reachability-solution-Problem12.csv')
    #
    # print(len(reached_errs), '/', len(reachable))

from pathlib import Path

from rers.check_result import parse_csv
from suls.rerssoconnector import RERSSOConnector


def parse_file(path):
    if Path(path).exists():
        with Path(path).open('rb') as file:
            return [int(x) for x in file.read()]
    else:
        print(f"{path} does not exist")

class CorpusUtils:
    def __init__(self, corpus_path, artifact_path, fuzzer_path, sul):
        self.corpus_path = Path(corpus_path)
        self.fuzzer_path = Path(fuzzer_path)
        self.artifact_path = Path(artifact_path)
        self.sul = sul

    def gather_crashes(self):
        crash_testcases = []
        for crash_file in self.artifact_path.glob('*'):
            crash_testcase = parse_file(crash_file)
            crash_testcases.append(crash_testcase)

        return crash_testcases

    def extract_errors(self, crashes):
        cs = set()
        for c in crashes:
            if c is not None:
                self.sul.reset()
                output = self.sul.process_input(c)
                if 'error' in output:
                    cs.add(output)
        return cs

if __name__ == "__main__":
    path = Path('/home/tom/projects/lstar/libfuzzer/SeqReachabilityRers2020/Problem19')

    sul = RERSSOConnector('/home/tom/projects/lstar/rers/SeqReachabilityRers2020/Problem19/Problem19.so')

    cutils = CorpusUtils(
        corpus_path=path.joinpath('corpus'),
        artifact_path=path.joinpath('corpus'),
        fuzzer_path=path.joinpath('Problem19_fuzz'),
        sul=sul
    )

    crashing_inputs = cutils.gather_crashes()

    reached_errs = [x.replace('error_', '') for x in cutils.extract_errors(crashing_inputs)]

    reachable, unreachable = parse_csv('/home/tom/projects/lstar/rers/TrainingSeqReachRers2019/Problem12/reachability-solution-Problem12.csv')

    print(len(reached_errs), '/', len(reachable))

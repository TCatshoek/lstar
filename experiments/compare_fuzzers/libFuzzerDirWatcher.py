# This bad boy watches a libfuzzer corpus directory and copies out
# any new cases before they can be deleted, preserving
# their creation date for later plotting

import time
from watchdog.observers import Observer
from watchdog.events import PatternMatchingEventHandler
from shutil import copy2
from pathlib import Path

from libfuzzer.utils import CorpusUtils, parse_file
from suls.rerssoconnector import RERSSOConnector


class FSWatchingCopier:
    def __init__(self, src_dir, dest_dir):
        # Setup event handler
        self.event_handler = PatternMatchingEventHandler("*", "", False, False)
        self.event_handler.on_created = self._on_created

        # Create observer
        self.observer = Observer(timeout=10)
        self.observer.schedule(self.event_handler, src_dir, recursive=False)
        self.observer.event_queue.maxsize = 100000

        # Folder to put stuff
        self.dest_dir = dest_dir
        self.src_dir = src_dir

        # Ensure that dest folder exists
        Path(self.dest_dir).mkdir(exist_ok=True)

    def start(self):
        self.observer.start()

    def _on_created(self, event):
        src_path = Path(event.src_path)
        dst_path = Path(self.dest_dir).joinpath(src_path.name)
        try:
            copy2(src_path, dst_path)
        except:
            #print(f"Failed to copy {src_path.name}")
            pass

    def stop(self):
        self.observer.stop()
        self.observer.join()


# Yeets files that are not erroring test cases
class FSWatchingFileYeeter:
    def __init__(self, watch_dir, problem, problemset, rers_basepath, fuzzer_basepath):
        # Setup event handler
        self.event_handler = PatternMatchingEventHandler("*", "", False, False)
        self.event_handler.on_created = self._on_created

        # Create observer
        self.observer = Observer(timeout=10)
        self.observer.schedule(self.event_handler, watch_dir, recursive=False)
        self.observer.event_queue.maxsize = 100000

        self.watch_dir = watch_dir

        rers_path = f"{rers_basepath}/{problemset}/{problem}/{problem}.so"
        fuzzer_dir = Path(f'{fuzzer_basepath}/{problemset}/{problem}')

        sul = RERSSOConnector(rers_path)

        self.cutils = CorpusUtils(
            corpus_path=fuzzer_dir.joinpath('corpus'),
            fuzzer_path=fuzzer_dir.joinpath(f'{problem}_fuzz'),
            sul=sul
        )

        self.errors_seen = set()
        self.last_n_errors_seen = 0

    def start(self):
        self.observer.start()

    def _on_created(self, event):
        src_path = Path(event.src_path)
        testcase = parse_file(src_path)

        error = self.cutils.extract_error(testcase)

        # Remove if no error is reached by this testcase
        if error is None or error in self.errors_seen:
            src_path.unlink()
        else:
            self.errors_seen.add(error)
            print(f'{len(self.errors_seen)} errors found.')

    def stop(self):
        print(self.errors_seen)
        print(len(self.errors_seen), " Errors seen!")
        self.observer.stop()
        self.observer.join()


problem = "Problem11"
#problemset = "TrainingSeqReachRers2019"
problemset = "SeqReachabilityRers2019"
#libfuzzer_basepath = "/home/tom/afl/thesis_benchmark_2/libFuzzer"
libfuzzer_basepath = "/home/tom/afl/thesis_benchmark_4/"
rers_basepath = "../../rers"

copier = FSWatchingCopier(Path(libfuzzer_basepath)
                          .joinpath(problemset)
                          .joinpath(problem)
                          .joinpath('corpus'),
                          Path(libfuzzer_basepath)
                          .joinpath(problemset)
                          .joinpath(problem)
                          .joinpath('corpus_errors'))

yeeter = FSWatchingFileYeeter(Path(libfuzzer_basepath)
                              .joinpath(problemset)
                              .joinpath(problem)
                              .joinpath('corpus_errors'),
                              problem,
                              problemset,
                              rers_basepath,
                              libfuzzer_basepath)

yeeter.start()
copier.start()

try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    copier.stop()
    yeeter.stop()

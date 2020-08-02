from pathlib import Path
import time
import functools

class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            if len(args) == 0:
                return NoopTracker()
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]

class NoopTracker():
    def __getattr__(self, item):
        return lambda *args, **kwargs: None

class StatsTracker(metaclass=Singleton):
    def __init__(self, stats, log_path, write_on_change=None, log_interval=60):
        self.stats = stats
        # where to write the log file to
        self.log_path = log_path
        # log interval in seconds
        self.log_interval = log_interval
        # if any of these values get changed, write to the log file
        self.write_on_change = write_on_change

        self.last_write_time = 0

        if not Path(self.log_path).exists():
            self.log_file = open(self.log_path, 'w+')
            self.log_file.write('# timestamp, ')
            self.log_file.write(', '.join([str(x) for x in self.stats.keys()]))
            self.log_file.write('\n')
            self.log_file.flush()
        else:
            self.log_file = open(self.log_path, 'a+')

        self.write_log()

    def set(self, key, value):
        if self.write_on_change is not None and key in self.write_on_change:
            old_value = self.stats[key]
            self.stats[key] = value
            if value != old_value:
                self.write_log()
        else:
            self.stats[key] = value
        self.write_if_time()

    def increment(self, key):
        self.stats[key] = self.stats[key] + 1
        if self.write_on_change is not None and key in self.write_on_change:
            self.write_log()
        self.write_if_time()

    def add(self, key, value):
        self.stats[key].add(value)
        if self.write_on_change is not None and key in self.write_on_change:
            self.write_log()
        self.write_if_time()

    def write_if_time(self):
        now = time.time()
        delta = now - self.last_write_time
        if delta > self.log_interval:
            self.write_log()

    def write_log(self):
        self.last_write_time = time.time()
        unixtime = time.time()
        self.log_file.write(f'{unixtime}, ')
        self.log_file.write(', '.join([str(x) for x in self.stats.values()]))
        self.log_file.write('\n')
        self.log_file.flush()


# Convenience methods so you don't need to manually check if
# stats tracking is enabled
def increment(key):
    statstracker = StatsTracker()
    if statstracker:
        statstracker.increment(key)

def set(key, value):
    statstracker = StatsTracker()
    if statstracker:
        statstracker.set(key, value)

def add(key, value):
    statstracker = StatsTracker()
    if statstracker:
        statstracker.add(key, value)

# Convenience method to count states, errors, and determine reached error states in a given hypothesis
def count_hypothesis_stats(hyp):
    statstracker = StatsTracker()

    states = hyp.get_states()

    # {*()} creates an empty set without having to use set(), since
    # i did a dumb and shadow it in this file >_>
    error_states = {*()}

    for state in states:
        for _, (_, output) in state.edges.items():
            if "error" in output:
                error_states.add(output)

    statstracker.set('state_count', len(states))
    statstracker.set('error_count', len(error_states))
    statstracker.set('errors', error_states)

# Save when the program quits
import atexit

def __save_on_quit():
    statstracker = StatsTracker()
    statstracker.write_log()
atexit.register(__save_on_quit)

if __name__ == '__main__':
    statstracker = StatsTracker()

    statstracker = StatsTracker({
            'membership_query': 0,
            'equivalence_query': 0,
            'test_query': 0,
            'state_count': 0,
            'error_count': 0,
            'errors': {*()}
        },
        log_path= 'test.log',
        write_on_change={'error_count'})

    statstracker = StatsTracker()

    statstracker.increment('membership_query')

    statstracker.increment('error_count')
    time.sleep(3)
    statstracker.increment('error_count')
    time.sleep(3)
    statstracker.increment('error_count')

    print(statstracker.stats)


from equivalencecheckers.equivalencechecker import EquivalenceChecker
from suls.sul import SUL
from typing import Tuple, Iterable, Callable
import random

from util.instrumentation import CounterexampleTracker


class Population:
    def __init__(self, initial_pop, pop_count, p_cross=0.9, p_mutate=0.05):
        self.pop = set(initial_pop)
        self.pop_count = pop_count

        # Disable crossover if we only have a pop size of 1
        self.p_cross = p_cross if len(self.pop) > 1 else -1
        self.p_mutate = p_mutate

        self.max_tries = pop_count * 10

    def __iter__(self):
        return self.pop.__iter__()

    # Generates a new individual
    def gen_new(self):
        # Are we going to do crossover?
        if random.random() <= self.p_cross:
            # Choose two parents
            p1, p2 = random.sample(self.pop, 2)
            tmp = self.crossover(p1, p2)
        # If we don't do crossover, pick a random parent
        else:
            tmp = random.sample(self.pop, 1)[0]
        return self.mutate(tmp)

    # A mutation is a random duplication or deletion in the sequence
    def mutate(self, individual):
        new = []
        for gene in individual:
            if random.random() <= self.p_mutate:
                # Bias to making longer sequences
                if random.random() <= 0.6:
                    new.append(gene)
                    new.append(gene)
            else:
                new.append(gene)

        tmp = tuple(new)
        return tmp

    def crossover(self, p1, p2):
        # Pick crossover points
        cpt1 = random.randint(0, len(p1))
        cpt2 = random.randint(0, len(p2))

        tmp = p1[0:cpt1] + p2[cpt2:]

        return tmp

    # Generates a new population from the previous population
    # Total tries prevents getting stuck
    def run_round(self):

        total_tries = 0
        newpop = set()
        lastlen = len(newpop)
        rounds_same = 0

        while len(newpop) < self.pop_count and rounds_same < 100:

            curlen = len(newpop)
            if curlen == lastlen:
                rounds_same += 1
            else:
                rounds_same = 0
                lastlen = curlen

            #print('rounds same', rounds_same)

            newpop.add(self.gen_new())

        self.pop = newpop
        return newpop


class GeneticEquivalenceChecker(EquivalenceChecker):
    def __init__(self, sul, counterexampletracker: CounterexampleTracker,
                 pop_n=1000):
        super().__init__(sul)
        self.ct = counterexampletracker
        self.pop_n = pop_n

    def test_equivalence(self, test_sul: SUL) -> Tuple[bool, Iterable]:
        # We need to have enough counterexamples to base our new attempts on
        if len(self.ct.storage) < 2:
            return True, None

        #total_counterexamples = []

        # Loop until we find no more new counterexamples
        #while True:

        # Keep track of all counterexamples we find this round
        new_counterexamples = []

        # We cluster the counterexamples, and mutate and cross them
        for cluster in [self.ct.storage]:#self.ct.get_clusters():
            # Skip clusters with just 1 trace
            # if len(cluster) < 2:
            #     continue

            # Grow the population to the desired size
            pop = Population(cluster, self.pop_n)
            pop.run_round()

            # Run all the potential counterexample traces
            for trace in pop.pop:
                equivalent, input = self._are_equivalent(test_sul, trace)
                if not equivalent:
                    return False, self.minimize(input, test_sul)
                    #total_counterexamples.append(input)

            # if len(new_counterexamples) < 1:
            #     break

        if len(new_counterexamples) < 1:
            return True, None
        else:
            return False, sorted(new_counterexamples, key=len)[0]

    def _reset_and_query(self, query, test_sul):
        self.sul.reset()
        test_sul.reset()
        og_out_1 = self.sul.process_input(query)
        og_out_2 = test_sul.process_input(query)
        return og_out_1, og_out_2

    def minimize(self, counterexample, test_sul):

        og_out_1, og_out_2 = self._reset_and_query(counterexample, test_sul)

        def trim():
            # leave one out and check if the output changes
            for i in range(1, len(counterexample)):
                test = counterexample[0:i - 1] + counterexample[i:]

                new_out_1, new_out_2 = self._reset_and_query(test, test_sul)

                if og_out_1 == new_out_1 and og_out_2 == new_out_2:
                    return test

            return counterexample

        previous = counterexample
        while previous != (counterexample := trim()):
            previous = counterexample

        print(["SHRANK DOWN TO"], counterexample)
        return counterexample




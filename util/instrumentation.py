import pickle
import numpy as np
from util.editdistance import lcsdistance
from scipy.cluster.hierarchy import linkage, dendrogram
from scipy.spatial.distance import squareform
import matplotlib.pyplot as plt
from scipy.cluster.hierarchy import fcluster
import random

# Borg pattern for EZ singletons https://python-3-patterns-idioms-test.readthedocs.io/en/latest/Singleton.html

class Borg:
    _shared_state = {}
    def __init__(self):
        self.__dict__ = self._shared_state

class CounterexampleTracker(Borg):
    def __init__(self):
        Borg.__init__(self)

        if 'storage' not in self.__dict__.keys():
            self.storage = []

    def add(self, counterexample):
        self.storage.append(counterexample)

    def save(self, filename):
        with open(filename, 'wb') as file:
            pickle.dump(self.storage, file)

    def load(self, filename):
        with open(filename, 'rb') as file:
            self.storage = pickle.load(file)

    def distance_matrix(self, penalty=0):
        n = len(self.storage)
        m = np.zeros((n, n))

        for row in range(n):
            for col in range(n):
                m[row, col] = lcsdistance(self.storage[row], self.storage[col], penalty=penalty)

        return m

    def get_clusters(self,
                     penalty=0,
                     t=1,
                     linkage_method='single'):

        if len(self.storage) < 2:
            return self.storage

        dists = self.distance_matrix(penalty)
        linkages = linkage(squareform(dists), method=linkage_method)
        cluster_assignments = fcluster(linkages, t=t)
        cluster_labels = np.unique(cluster_assignments)

        counterexamples = np.array(self.storage)
        clusters = []
        for label in cluster_labels:
            clusters.append(counterexamples[cluster_assignments == label])

        return clusters


class GeneticMethod:
    def __init__(self, initial_pop, pop_count, p_cross=0.9, p_mutate=0.05):
        self.pop = set(initial_pop)
        self.pop_count = pop_count

        self.p_cross = p_cross
        self.p_mutate = p_mutate

    # Generates a new individual
    def gen_new(self):
        # Are we going to do crossover?
        if random.random() <= self.p_cross:
            # Choose two parents
            p1, p2 = random.sample(self.pop, 2)
            tmp = self.crossover(p1, p2)
        # If we don't do crossover, pick a random parent
        else:
            tmp = random.sample(self.pop, 1)
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
        return tuple(new)

    def crossover(self, p1, p2):
        # Pick crossover points
        cpt1 = random.randint(0, len(p1) - 1)
        cpt2 = random.randint(0, len(p2) - 1)

        return p1[0:cpt1] + p2[cpt2:]

    # Generates a new population from the previous population
    def run_round(self):
        newpop = set()
        while len(newpop) < self.pop_count:
            print(len(newpop))
            newpop.add(self.gen_new())

        return newpop


if __name__ == "__main__":
    c = CounterexampleTracker()
    c.load("/home/tom/projects/lstar/experiments/counterexampletracker/problem12counterexamples")

    clusters = c.get_clusters(penalty=2)

    print(clusters)

    cluster = clusters[0]

    gm = GeneticMethod(cluster, 1000)
    totry = gm.run_round()




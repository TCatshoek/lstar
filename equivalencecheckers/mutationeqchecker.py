from typing import Tuple, Optional, Iterable

from hdbscan import HDBSCAN
import umap
from equivalencecheckers.equivalencechecker import EquivalenceChecker
from suls.sul import SUL
from util.editdistance import lcsdistance
import numpy as np
import random

class MutationEquivalenceChecker(EquivalenceChecker):
    def __init__(self, sul, counterexampletracker, p_cross=0.9, p_mutate=0.05, penalty=1, min_cluster_size=20,
                 min_samples=3, target_pop_size=10000, max_retries=100, cluster=True):
        super().__init__(sul)
        self.p_cross = p_cross
        self.p_mutate = p_mutate
        self.penalty = penalty
        self.ct = counterexampletracker
        self.min_cluster_size = min_cluster_size
        self.min_samples = min_samples
        self.target_pop_size = target_pop_size
        self.max_retries = max_retries
        self.cluster = cluster

    def test_equivalence(self, test_sul: SUL) -> Tuple[bool, Optional[Iterable]]:
        # Get the currently known counterexamples
        counterexamples = self.ct.storage
        # We can't do anything unless we have more than two counterexamples already
        if len(counterexamples) <= 4:
            return True, None

        # Perform clustering
        if self.cluster:
            clusters = self._preprocess(counterexamples)
        else:
            clusters = {0: counterexamples}

        # Generate new populations and use them for EQ checks
        for new_population in self._generate_new_populations(clusters):
            for individual in new_population:
                equivalent, input = self._are_equivalent(test_sul, individual)
                if not equivalent:
                    return False, self._minimize(input, test_sul)

        return True, None

    def _generate_new_populations(self, clusters):
        # For each cluster, build a population by mutation and crossover
        for cluster in clusters.values():
            # Again, we can't do anything useful if we don't have more than two individuals
            if len(cluster) <= 4:
                continue
            # Build new individuals
            new_population = set()
            retries = 0
            while len(new_population) < self.target_pop_size and retries < self.max_retries:
                # Crossover
                if random.random() < self.p_cross:
                    p1 = random.choice(cluster)
                    p2 = random.choice(cluster)
                    new_individual = self._crossover(p1, p2)
                else:
                    new_individual = random.choice(cluster)

                # Mutation
                if random.random() < self.p_mutate:
                    new_individual = self._mutate(new_individual)

                # Add to new population
                if new_individual not in new_population and len(new_individual) > 0:
                    new_population.add(new_individual)
                    retries = 0
                else:
                    retries += 1
            yield new_population

    # simple crossover
    def _crossover(self, p1, p2):
        # Pick crossover points
        cpt1 = random.randint(0, len(p1))
        cpt2 = random.randint(0, len(p2))

        tmp = p1[0:cpt1] + p2[cpt2:]

        return tmp

    # random duplication or deletion
    def _mutate(self, individual):
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

    def _preprocess(self, counterexamples):
        # First project and cluster the counterexamples
        distances = self._distance_matrix(counterexamples)
        # Normalize
        distances = distances / np.max(distances)
        # Project
        reducer = umap.UMAP(
            metric="precomputed",
            n_neighbors=len(counterexamples) - 1,
            min_dist=0.3,
        )
        projected = reducer.fit(distances)
        # Cluster
        cluster_labels = HDBSCAN(metric='euclidean',
                                 min_cluster_size=self.min_cluster_size,
                                 min_samples=self.min_samples
                                 ).fit_predict(projected.embedding_)
        clusters = {}
        for (counterexample, label) in zip(counterexamples, cluster_labels):
            if label not in clusters:
                clusters[label] = []
            clusters[label].append(counterexample)
        return clusters

    def _distance_matrix(self, counterexamples):
        n = len(counterexamples)
        m = np.zeros((n, n))

        for row in range(n):
            for col in range(n):
                m[row, col] = lcsdistance(counterexamples[row], counterexamples[col], penalty=self.penalty)

        return m

    def _reset_and_query(self, query, test_sul):
        self.sul.reset()
        test_sul.reset()
        og_out_1 = self.sul.process_input(query)
        og_out_2 = test_sul.process_input(query)
        return og_out_1, og_out_2

    def _minimize(self, counterexample, test_sul):

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

        #print(["SHRANK DOWN TO"], counterexample)
        return counterexample

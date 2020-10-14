import time
from numpy.random.mtrand import choice
import numpy as np
import sys

from suls.caches.dictcache import DictCache
from suls.caches.rerstriecache import RersTrieCache
from suls.caches.triecache import TrieCache
from suls.rersconnectorv4 import RERSConnectorV4
from suls.rerssoconnector import RERSSOConnector

import pickle

problem = "Problem12"
cache = 'cache'


n = 1000
w = 100

fill = []
retrieve = []
uncached = []
mem_usage = []

for run in range(10):

    # cached_sul = TrieCache(
    #     RERSConnectorV4(f'../rers/TrainingSeqReachRers2019/{problem}/{problem}'),
    #     storagepath=cache
    # )
    cached_sul = DictCache(
        RERSConnectorV4(f'../rers/TrainingSeqReachRers2019/{problem}/{problem}'),
        storagepath=cache
    )

    # sul = RERSSOConnector(f'../rers/TrainingSeqReachRers2019/{problem}/{problem}.so')

    sul = RERSConnectorV4(f'../rers/TrainingSeqReachRers2019/{problem}/{problem}')

    print("generating testcases")

    # Generate a bunch of random keys
    alphabet = sul.get_alphabet()
    quers = choice(alphabet, (n, w))
    queries = []
    for i in range(n):
        queries.append(tuple(quers[i]))
    print("done generating")

    # Time empty cache
    start = time.perf_counter()
    for query in queries:
        cached_sul.reset()
        a = cached_sul.process_input(query)
    end = time.perf_counter() - start
    fill.append(end)
    mem_usage.append(len(pickle.dumps(cached_sul.cache)))
    print()
    print(f"filling cache took {end:0.5f} s")

    # Retrieve cached
    start = time.perf_counter()
    for query in queries:
        cached_sul.reset()
        a = cached_sul.process_input(query)
    end = time.perf_counter() - start
    retrieve.append(end)
    print()
    print(f"retrieving cache took {end:0.5f} s")

    # Uncached
    start = time.perf_counter()
    for query in queries:
        sul.reset()
        a = sul.process_input(query)
    end = time.perf_counter() - start
    uncached.append(end)
    print()
    print(f"uncached took {end:0.5f} s")

print("AVG:")
print(f"fill: {np.mean(fill):0.5f}")
print(f"retrieve: {np.mean(retrieve):0.5f}")
print(f"uncached: {np.mean(uncached):0.5f}")
print(f"mem: {np.mean(mem_usage):0.5f}")
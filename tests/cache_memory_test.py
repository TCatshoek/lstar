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
import pickle

problem = "Problem12"
cache = 'cache'
path = f'../rers/TrainingSeqReachRers2019/{problem}/{problem}'
n = 100000
w = 100

trie_cached_sul = TrieCache(
    RERSSOConnector(f'{path}.so'),
    storagepath=cache
)
dict_cached_sul = DictCache(
    RERSSOConnector(f'{path}.so'),
    storagepath=cache
)

# Generate a bunch of random keys
alphabet = trie_cached_sul.get_alphabet()
quers = choice(alphabet, (n, w))
queries = []
for i in range(n):
    queries.append(tuple(quers[i]))
print("done generating")
queries = iter(queries)

trie_mem = []
dict_mem = []

count = 0
ns = [10, 100, 1000, 10000]
ns = range(0, 100000, 10000)
for run in ns:
    while count < run:
        query = next(queries)
        count += 1

        trie_cached_sul.reset()
        dict_cached_sul.reset()

        trie_cached_sul.process_input(query)
        dict_cached_sul.process_input(query)

    trie_mem.append(len(pickle.dumps(trie_cached_sul.cache)))
    dict_mem.append(len(pickle.dumps(dict_cached_sul.cache)))

import matplotlib.pyplot as plt
plt.plot(ns, trie_mem, label='trie')
plt.plot(ns, dict_mem, label='dict')
plt.legend()
plt.show()

plt.plot(ns, trie_mem, label='trie')
plt.show()

plt.plot(ns, dict_mem, label='dict')
plt.show()
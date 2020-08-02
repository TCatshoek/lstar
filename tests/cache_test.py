import time
from numpy.random.mtrand import choice

from suls.caches.dictcache import DictCache
from suls.caches.rerstriecache import RersTrieCache
from suls.rersconnectorv4 import RERSConnectorV4
from suls.rerssoconnector import RERSSOConnector

problem = "Problem12"
cache = 'cache'
# cached_sul = RersTrieCache(
#     RERSConnectorV4(f'../rers/TrainingSeqReachRers2019/{problem}/{problem}'),
#     storagepath=cache
# )
cached_sul = DictCache(
    RERSConnectorV4(f'../rers/TrainingSeqReachRers2019/{problem}/{problem}'),
    storagepath=cache
)
sul = RERSSOConnector(f'../rers/TrainingSeqReachRers2019/{problem}/{problem}.so')

n = 1000
w = 100

print("generating testcases")

# Generate a bunch of random keys
queries = []
for i in range(n):
    queries.append(tuple(choice(sul.get_alphabet(), w)))

print("done generating")
# Time empty cache
start = time.perf_counter()
for query in queries:
    cached_sul.reset()
    a = cached_sul.process_input(query)
end = time.perf_counter() - start
print()
print(f"filling cache took {end:0.5f} s")

# Retrieve cached
start = time.perf_counter()
for query in queries:
    cached_sul.reset()
    a = cached_sul.process_input(query)
end = time.perf_counter() - start
print()
print(f"retrieving cache took {end:0.5f} s")

# Uncached
start = time.perf_counter()
for query in queries:
    sul.reset()
    a = sul.process_input(query)
end = time.perf_counter() - start
print()
print(f"uncached took {end:0.5f} s")
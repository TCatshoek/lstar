import time
from numpy.random.mtrand import choice
from suls.caches.rerstriecache import RersTrieCache
from suls.rersconnectorv4 import RERSConnectorV4

problem = "Problem12"
cache = 'cache'
cached_sul = RersTrieCache(
    RERSConnectorV4(f'../rers/TrainingSeqReachRers2019/{problem}/{problem}'),
    storagepath=cache
)

sul = RERSConnectorV4(f'../rers/TrainingSeqReachRers2019/{problem}/{problem}')

num_samples = 10000
depth = 100

# Generate queries
A = list(sul.get_alphabet())
queries = choice(A, size=(num_samples, depth))

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
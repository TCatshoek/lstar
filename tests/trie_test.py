from suls.rersconnectorv2 import RERSConnectorV2
from cppconnector.build.trie import Trie
from numpy.random import choice
import time
from pygtrie import StringTrie
import string
import datrie




alphabet = ['1', '2', '3']

print("generating testcases")
# Generate a bunch of random keys
keys = choice(alphabet, (100000, 20))
keys = [" ".join(key) for key in keys]
print("done generating")



datr = datrie.Trie(''.join(alphabet) + ' ')
start = time.perf_counter()
for key in keys:
    datr[key] = 'hai'
end = time.perf_counter() - start
print(f"datrie put took {end:0.5f} s")

start = time.perf_counter()
for key in keys:
    a = datr[key]
end = time.perf_counter() - start
print(f"datrie get took {end:0.5f} s")




t = Trie(alphabet, ' ')
start = time.perf_counter()
for key in keys:
    t.put(key, 'hai')
end = time.perf_counter() - start
print(f"trie put took {end:0.5f} s")

start = time.perf_counter()
for key in keys:
    a = t.get(key)
end = time.perf_counter() - start
print(f"trie get took {end:0.5f} s")




dict = dict()
start = time.perf_counter()
for key in keys:
    dict[key] = 'hai'
end = time.perf_counter() - start
print(f"dict put took {end:0.5f} s")

start = time.perf_counter()
for key in keys:
    a = dict[key]
end = time.perf_counter() - start
print(f"dict get took {end:0.5f} s")




t = StringTrie()
start = time.perf_counter()
for key in keys:
    t[key] = 'hai'
end = time.perf_counter() - start
print(f"pygtrie put took {end:0.5f} s")

start = time.perf_counter()
for key in keys:
    a = t[key]
end = time.perf_counter() - start
print(f"pygtrie get took {end:0.5f} s")
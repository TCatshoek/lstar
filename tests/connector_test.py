from suls.caches.triecache import TrieCache
from suls.rersconnectorv3 import RERSConnectorV3
from suls.rersconnectorv4 import RERSConnectorV4
from suls.rersconnectorv2 import RERSConnectorV2
from numpy.random import choice
import time
from pygtrie import StringTrie

from suls.rerssoconnector import RERSSOConnector

path = '../rers/TrainingSeqReachRers2019/Problem11/Problem11'
r1 = RERSConnectorV2(path, terminator='-1')
r2 = RERSConnectorV3(path)
r3 = RERSConnectorV4(path)
r4 = RERSSOConnector(f'{path}.so')
r5 = TrieCache(r3)
alphabet = r1.get_alphabet()

n = 1000
w = 1000

print("generating testcases")

# Generate a bunch of random keys
inputs = []
for i in range(n):
    inputs.append(list(choice(alphabet, w)))

print("done generating")

def test(connector, name):
    start = time.perf_counter()

    for input in inputs:
        connector.reset()
        result = connector.process_input(input)

    end = time.perf_counter() - start
    print(f"{name} took {end:0.5f} s")

test(r3, 'v4')
test(r4, 'so')
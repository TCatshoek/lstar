from suls.caches.triecache import TrieCache
from suls.rersconnectorv3 import RERSConnectorV3
from suls.rersconnectorv4 import RERSConnectorV4
from suls.rersconnectorv2 import RERSConnectorV2
from suls.rersconnector import StringRERSConnector as RERSConnectorV1
from numpy.random import choice
import time
from tqdm import tqdm
from pygtrie import StringTrie

from suls.rerssoconnector import RERSSOConnector

path = '../rers/TrainingSeqReachRers2019/Problem11/Problem11'
r0 = RERSConnectorV1(path)
r1 = RERSConnectorV2(path, terminator='-1')
r2 = RERSConnectorV3(path)
r3 = RERSConnectorV4(path)
r4 = RERSSOConnector(f'{path}.so')

alphabet = r1.get_alphabet()

n = 100
ws = [10, 100, 1000, 10000]

results = {
    'v1': [],
    'v2': [],
    'v3': [],
    'v4': [],
    'so': []
}

def test_connector(connector, name, inputs):
    start = time.perf_counter()

    for input in tqdm(inputs):
        connector.reset()
        result = connector.process_input(input)

    end = time.perf_counter() - start
    results[name].append(end)
    print(f"{name} took {end:0.5f} s")

def test(n, w):
    print("generating testcases")

    # Generate a bunch of random keys
    inputs = []
    for i in range(n):
        inputs.append(list(choice(alphabet, w)))

    print("done generating")

    test_connector(r0, 'v1', inputs)
    test_connector(r1, 'v2', inputs)
    test_connector(r2, 'v3', inputs)
    test_connector(r3, 'v4', inputs)
    test_connector(r4, 'so', inputs)
#
for w in ws:
    test(n, w)

import pickle
# pickle.dump(results, open('results2.p', 'wb'))

results = pickle.load(open('results2.p', 'rb'))

import numpy as np
import matplotlib.pyplot as plt
for name, result in results.items():
    ws = np.array(ws)
    result = np.array(result)

    plt.plot(ws, result / n, label=name)
plt.legend()
plt.yscale('log')
plt.ylabel('time (s)')
plt.xscale('log')
plt.xlabel('query length')
plt.title('Time per query vs. query length (log scale)')
plt.grid(True)
plt.show()
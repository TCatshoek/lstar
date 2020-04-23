from suls.rersconnectorv2 import RERSConnectorV2
from suls.rersconnectorv3 import RERSConnectorV3
from suls.rersconnectorv2 import RERSConnectorV2
from numpy.random import choice
import time
from pygtrie import StringTrie

path = '../rers/TrainingSeqReachRers2019/Problem11/Problem11'
r1 = RERSConnectorV2(path, terminator='-1')
r2 = RERSConnectorV3(path)

alphabet = r1.get_alphabet()

print("generating testcases")
# Generate a bunch of random keys
keys = choice(alphabet, (10000, 200))
keys = [" ".join(key) for key in keys]
print("done generating")

start = time.perf_counter()
for key in keys:
    a = r1._interact(key)
end = time.perf_counter() - start
print(f"v2 took {end:0.5f} s")

start = time.perf_counter()
for key in keys:
    a = r2._interact(key)
end = time.perf_counter() - start
print(f"v3 took {end:0.5f} s")
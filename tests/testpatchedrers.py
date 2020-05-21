from suls.rersconnectorv4 import RERSConnectorV4
from suls.rersconnectorv2 import RERSConnectorV2

n = 1000

# asyncio.run(main(n))

path1 = "../rers/rers_19_industrial_reachability_training/arithmetic/m34/m34_Reach_patched"
path2 = "../rers/rers_19_industrial_reachability_training/arithmetic/m34/m34_Reach"
r = RERSConnectorV4(path1)
r2 = RERSConnectorV2(path2)

alphabet = r.get_alphabet()
assert r2.get_alphabet() == alphabet

from numpy.random import choice
import time

inputs = []
for i in range(n):
    inputs.append(list(choice(alphabet, 100)))

start = time.perf_counter()

mismatches = []

for input in inputs:
    print("Sending 1", input)
    result1 = r.process_input(input)
    print("Sending 2", input)
    result2 = r2.process_input(input)
    if result1 != result2:
        print("MISMATCH:", result1, result2)
        mismatches.append(input)

end = time.perf_counter() - start
print(f'Took {end:0.5f} seconds')

if len(mismatches) > 0:
    print("Mismatch found", mismatches)
else:
    print("No mismatches found")

print("DONE")
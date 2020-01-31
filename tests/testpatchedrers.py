from suls.rersconnectorv3 import RERSConnectorV3
from suls.rersconnectorv2 import RERSConnectorV2

n = 1000

# asyncio.run(main(n))

path1 = "../rers/TrainingSeqReachRers2019/Problem11/Problem11_patched"
path2 = "../rers/TrainingSeqReachRers2019/Problem11/Problem11"
r = RERSConnectorV3(path1)
r2 = RERSConnectorV2(path2)

alphabet = r.get_alphabet()

from numpy.random import choice
import time

inputs = []
for i in range(n):
    inputs.append(list(choice(alphabet, 10)))

start = time.perf_counter()

mismatches = []

for input in inputs:
    print("Sending", input)
    result1 = r.process_input(input)
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
from suls.rersconnectorv2 import RERSConnectorV2

sm = RERSConnectorV2('../rers/TrainingSeqReachRers2019/Problem11/Problem11')

testcase = ('1','2','3','4','5','6','7','8','9', '10')

import time

start = time.time_ns() // 1000000

for i in range(10000):
    sm._interact(testcase)

end = time.time_ns() // 1000000

print((end - start) / 10000)
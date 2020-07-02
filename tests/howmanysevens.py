from suls.rersconnectorv4 import RERSConnectorV4

problem = "Problem12"

rers = RERSConnectorV4(f'../rers/TrainingSeqReachRers2019/{problem}/{problem}')

seen_outputs = set()
for i in range(10000):
    output = rers.process_input(['7'] * i)
    if output not in seen_outputs:
        print(output)
        seen_outputs.add(output)
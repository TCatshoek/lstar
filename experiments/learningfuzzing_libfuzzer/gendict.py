import argparse
import re
from pathlib import Path

parser = argparse.ArgumentParser(description='Patches the rers code for libfuzzer')
parser.add_argument('file', type=str)

args = parser.parse_args()

path = args.file

alphabet = None
with open(path, 'r') as f:
    lines = f.readlines()
    for line in lines:
        match = re.match(r'\s*int inputs\[\] = {(.*)};', line)

        if match:
            alphabet = [int(x) for x in match.group(1).split(',')]
            print(len(alphabet))
newpath = Path(path).parent.joinpath('dict')

with open(newpath, 'w') as newfile:
    for a in alphabet:
        newfile.write("\"\\x%0.2X\"\n" % a)





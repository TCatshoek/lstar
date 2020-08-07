import re
import argparse

parser = argparse.ArgumentParser(description='Generates an alphabet mapping for the LTL problems that are missing one')
parser.add_argument('constraints_path', type=str)
parser.add_argument('output_path', type=str)

args = parser.parse_args()

mapping_path = args.output_path
constraints_path = args.constraints_path

def extract_inputs(path):
    with open(path, 'r') as file:
        for line in file.readlines():
            res = re.match(r'#inputs \[(.*)\]', line)
            if res:
                return [x.strip() for x in res.group(1).split(',')]

def extract_outputs(path):
    with open(path, 'r') as file:
        for line in file.readlines():
            res = re.match(r'#outputs \[(.*)\]', line)
            if res:
                return [x.strip() for x in res.group(1).split(',')]

def patch_input_output_lines(path):
    inputs = [f'i{x}' for x in extract_inputs(path)]
    outputs = [f'o{x}' for x in extract_outputs(path)]

    with open(path, 'r') as file:
        lines = file.readlines()

    lines[0] = f'#inputs [{", ".join(inputs)}]\n'
    lines[1] = f'#outputs [{", ".join(outputs)}]\n'

    with open(path, 'w') as file:
        file.writelines(lines)


with open(mapping_path, 'w') as file:
    for letter in extract_inputs(constraints_path):
        file.write(f'i{letter} {ord(letter.lower()) - 96}\n')

    for letter in extract_outputs(constraints_path):
        file.write(f'o{letter} {ord(letter.lower()) - 96}\n')

patch_input_output_lines(constraints_path)

import argparse
import re
from pathlib import Path

parser = argparse.ArgumentParser(description='Patches the rers code make it into a shared object')
parser.add_argument('file', type=str)

args = parser.parse_args()

path = args.file

def find_closing_bracket(lines, startpattern):
    counting = False
    count = 0
    for idx, line in enumerate(lines):
        if startpattern in line:
            counting = True

        if counting:
            count += line.count('{')
            count -= line.count('}')

        if count == 0 and counting is True:
            return idx


def patch(path):
    with open(path) as file:
        lines = file.readlines()

        patched = []

        for idx, line in enumerate(lines):
            # Rename simple stuff
            patched_line = line.replace("void errorCheck", "int errorCheck")
            patched_line = patched_line.replace("void calculate", "int calculate")
            patched_line = patched_line.replace("__VERIFIER_error", "return __VERIFIER_error")
            patched_line = patched_line.replace("extern void return __VERIFIER_error", "extern int __VERIFIER_error")

            if "extern int __VERIFIER_error(int);" in patched_line:
                patched_line = ""

            result = re.search(r'^(\s*)int inputs\[\] = ', patched_line)
            if result:
                patched_line += f"\n{result.group(1)}int output;\n"

            # Replace prints to set output
            result = re.search(r'^(\s*}*)printf\(\"\%d\\n\", (\d+)\);.*$', patched_line)
            if result:
                # patched_line = f'{patched_line}{result.group(1)}return {result.group(2)};\n'
                patched_line = f'{result.group(1)}output = {result.group(2)};\n'

            # # Make calculate output calls return
            # result = re.search(r'(\s*)(calculate_outputm\d+\(\w+\);)', patched_line)
            # if result:
            #     if not re.search(r'calculate_outputm\d+\(int\);', patched_line):
            #         patched_line = f'{result.group(1)}return {result.group(2)};\n'

            # Patch errorcheck call
            result = re.search(r'^(\s*)errorCheck\(\);', patched_line)
            if result:
                indent = result.group(1)
                patched_line =  f'{indent}int err = errorCheck();\n'
                patched_line += f'{indent}if (err != 0) ' + "{\n"
                patched_line += f'{indent}\treturn err;\n'
                patched_line += f'{indent}' + '}\n'

            # Patch invalid input return
            patched_line = patched_line.replace('fprintf(stderr, "Invalid input: %d\\n", input); ', 'return -1;')

            # Patch verifier error to just return an int, it returns the original error int, but negative and -2 to make
            # room for -1 being the int returned on invalid input
            result = re.search(r'^(\s*)return __VERIFIER_error\((\d+)\);', patched_line)
            if result:
                return_int = (int(result.group(2)) * -1) - 2
                patched_line = f'{result.group(1)}return {return_int};\n'

            patched.append(patched_line)

        # Fix return fallthrough of error checking
        errorCheck_end_line = find_closing_bracket(patched, 'int errorCheck() {')
        if errorCheck_end_line:
            patched.insert(errorCheck_end_line, '\t\treturn 0;\n')

        # Add output return
        calculate_output_end_line = find_closing_bracket(patched, 'int calculate_output(int input) {')
        if calculate_output_end_line:
            patched.insert(calculate_output_end_line, '\n\treturn output;\n')

        newpath = Path(path).parent.joinpath(Path(path).stem).as_posix() + "_lib.c"
        with open(newpath, 'w') as newfile:
            newfile.writelines(patched)

        return patched

# path = "/home/tom/projects/lstar/rers/TrainingSeqReachRers2019/Problem11/Problem11_patched.c"

patch(path)

#
# if __name__ == "__main__":
#     path = "/home/tom/projects/lstar/rers/TrainingSeqReachRers2019/Problem11/Problem11_patched.c"
#     patched = patch(path)
#
#     print(find_closing_bracket(patched, 'int errorCheck() {'))

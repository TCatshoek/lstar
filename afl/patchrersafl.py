import argparse
import re
from pathlib import Path

parser = argparse.ArgumentParser(description='Patches the rers code to add a reset function')
parser.add_argument('file', type=str)

args = parser.parse_args()

path = args.file

def patch(path):
    with open(path) as file:
        lines = file.readlines()

        # Line numbers to keep track of
        vardeclines = []
        declarations = []
        assignments = []
        initialresetpos = None
        manualresetpos = None

        for idx, line in enumerate(lines):
            # Find var declarations
            # (I'm so sorry for this regular expression stuff,
            # I really wanted to use a legit c parser but couldn't get it to work)
            if (result := re.search("(int \*?[a-z0-9]+\[?\]?)\s+=\s+(-?\{?[a-z]?([0-9]+,?)+\}?;)", line)) is not None:
                # Ignore the inputs line
                if re.search("inputs\[\]", line) is not None:
                    continue

                vardeclines.append(idx)

                decl = result.string.strip()

                lh = result.group(1)
                rh = result.group(2)

                # Handle array decl
                if arr := re.search("(int ([a-z0-9]+))\[\]", lh):
                    # Count amount of  elements
                    n_el = rh.count(',') + 1
                    var = f'{arr.group(1)}[{n_el}];'
                    #assignment = f'static {arr.group(1)}[{n_el}] = {rh}'
                    # We can't assign an array literal after declaration, so need to use memcpy
                    varname = arr.group(1).strip('int').strip()
                    assignment = f'memcpy({varname}, (int[]){rh.strip(";")}, sizeof({varname}));'
                else:
                    var = re.search('int \*?[a-z0-9]+(\[\])?', decl).group(0).strip() + ";"
                    assignment = re.search("[a-z0-9]+(\[\])?\s+=\s+-?\{?[a-z]?([0-9]+,?)+\}?;", decl).group(0).strip()

                declarations.append(var)
                assignments.append(assignment)

                #print("Var:", var, "Ass:", assignment)

            # Find where to insert resets
            if (result := re.search("while\(1\)", line)) is not None:
                #print(result.string.strip(), idx)
                initialresetpos = idx

            if (result := re.search("if\(\(input != [0-9]+\)", line)) is not None:
                #print(result.string.strip(), idx)
                manualresetpos = idx

        # Assemble the new file
        patched = ["#include <string.h>\n"]
        patched += ['#include <unistd.h>\n']
        patched += lines[0:vardeclines[0] - 1] # Lines before vars
        patched += [d + "\n" for d in declarations]
        patched += ["void reset() {\n"]
        patched += ["\t" + s + "\n" for s in assignments]
        patched += ["}\n"]
        patched += lines[vardeclines[-1] + 1: initialresetpos - 1]
        patched += ["\treset();\n"]
        patched += lines[initialresetpos:manualresetpos]
        patched += ["\t\tif(input == 0) {\n\t\t\treset();\n\t\t\tfprintf(stderr, \"Reset\\n\", input);\n\t\t\tcontinue;\n\t\t}\n"]
        patched += ["\t\telse " + lines[manualresetpos].strip() + "\n"]
        patched += lines[manualresetpos + 1:]

        return patched

def replace_main(lines):
    main = '''int main()
{
    char buf[1024*1024];

    while(__AFL_LOOP(10000000))
    {
        reset();

        // Read from stdin (fd 0)
        size_t n = read(0, buf, 1024*1024);
        
        // operate eca engine
        for (size_t i = 0; i < n; i++) {
            int input = buf[i];

		    $checkline
                return -2;

            calculate_output(input);
        }
    }
}
'''
    main_startsat = lines.index("int main()\n")

    main_lines = main.splitlines()
    main_lines = [f'{line}\n' for line in main_lines]

    return lines[0:main_startsat] + main_lines

def get_allowed_inputs(lines):
    for line in lines:
        match = re.match(r'\s*int inputs\[\] = {(.*)};', line)
        if match:
            return [x.strip() for x in match.group(1).split(',')]

def generate_check_line(allowed_inputs):
    checks = [f'(input != {x})' for x in allowed_inputs]
    return f'\t\t\tif({" && ".join(checks)})\n'

# add reset function
lines = patch(path)

# replace main
lines = replace_main(lines)

# generate the input check
allowed_inputs = get_allowed_inputs(lines)
check_index = lines.index('		    $checkline\n')
lines[check_index] = generate_check_line(allowed_inputs)

newpath = Path(path).parent.joinpath(Path(path).stem).as_posix() + "_afl.c"

with open(newpath, 'w') as newfile:
    newfile.writelines(lines)





from suls.mealymachine import MealyMachine, MealyState
import re
from util.spot_ltl_translate import rewrite_weakuntil
from itertools import chain
#
#
# def mealy2nusmv(fsm: MealyMachine, path):
#
#     # Collect fsm info
#     states = fsm.get_states()
#
#     inputs = set()
#     outputs = set()
#     statenames = set()
#     initial_state_name = fsm.initial_state.name
#
#     for state in states:
#         statenames.add(state.name)
#         for input, (next_state, output) in state.edges.items():
#             inputs.add(input)
#             outputs.add(output)
#
#     outputs.add('none')
#
#     # Assemble smv file
#     smvlines = []
#     smvlines.append("MODULE main\n")
#     smvlines.append("VAR\n")
#     smvlines.append("\tinput : {" + ",".join(inputs) + "};\n")
#     smvlines.append("\tstate : {" + ",".join(statenames) + "};\n")
#     smvlines.append("\toutput: {" + ",".join(outputs) + "};\n")
#     smvlines.append("ASSIGN\n")
#     smvlines.append(f"\tinit(state) := {initial_state_name};\n")
#     smvlines.append("\tnext(state) := case\n")
#
#     for state in states:
#         for input, (next_state, output) in state.edges.items():
#             smvlines.append(f"\t\t\tstate = {state.name} & input = {input} : {next_state.name};\n")
#
#     smvlines.append("\t\t\tTRUE : {" + ",".join(statenames) + "};\n")
#     smvlines.append("\tesac;\n")
#
#     smvlines.append("\tinit(output) := none;\n")
#     smvlines.append("\tnext(output) := case\n")
#
#     for state in states:
#         for input, (next_state, output) in state.edges.items():
#             smvlines.append(f"\t\t\tstate = {state.name} & input = {input} : {output};\n")
#
#     smvlines.append("\t\t\tTRUE : {" + ",".join(outputs) + "};\n")
#     smvlines.append("\tesac;\n")
#
#     return smvlines

    # with open(path, 'w') as file:
    #     file.writelines(smvlines)
#
# def mealy2nusmv_withintermediate(fsm: MealyMachine, path):
#
#     # Collect fsm info
#     states = fsm.get_states()
#
#     alphabet = fsm.get_alphabet()
#
#     inputs = set()
#     outputs = set()
#     statenames = set()
#     initial_state_name = fsm.initial_state.name
#
#     for state in states:
#         statenames.add(state.name)
#         for input, (next_state, output) in state.edges.items():
#             inputs.add(input)
#             outputs.add(output)
#
#     # Get a comma separated list of the state names + extra intermediate output states
#     # The intermediate states are named *original state name*_o_*input*
#     statenames_with_intermediate = []
#     for statename in statenames:
#         statenames_with_intermediate.append(statename)
#         for a in alphabet:
#             statenames_with_intermediate.append(f'{statename}_o_{a}')
#
#     statenames_with_intermediate = ",".join(statenames_with_intermediate)
#
#
#     # Assemble smv file
#     smvlines = []
#     smvlines.append("MODULE main\n")
#     smvlines.append("VAR\n")
#     smvlines.append("\tinput : {" + ",".join(inputs) + "};\n")
#     smvlines.append("\tstate : {" + statenames_with_intermediate + "};\n")
#     smvlines.append("\toutput: {" + ",".join(outputs) + "," + ",".join(inputs) + "};\n")
#     smvlines.append("ASSIGN\n")
#     smvlines.append(f"\tinit(state) := {initial_state_name};\n")
#     smvlines.append("\tnext(state) := case\n")
#
#     for state in states:
#         for input, (next_state, output) in state.edges.items():
#             intermediate_name = f'{state.name}_o_{input}'
#             smvlines.append(f"\t\t\tstate = {state.name} & input = {input} : {intermediate_name};\n")
#             smvlines.append(f"\t\t\tstate = {intermediate_name} : {next_state.name};\n")
#
#     #smvlines.append("\t\t\tTRUE : {" + statenames_with_intermediate + "};\n")
#     smvlines.append("\tesac;\n")
#
#     smvlines.append("\tinit(output) := input;\n")
#     smvlines.append("\tnext(output) := case\n")
#
#     for state in states:
#         for input, (next_state, output) in state.edges.items():
#             intermediate_name = f'{state.name}_o_{input}'
#             smvlines.append(f"\t\t\tstate = {state.name} & input = {input} : {input};\n")
#             smvlines.append(f"\t\t\tstate = {intermediate_name} : {output};\n")
#
#     #smvlines.append("\t\t\tTRUE : {" + ",".join(outputs) + "," + ",".join(inputs) + "};\n")
#     smvlines.append("\tesac;\n")
#
#     return smvlines
#
#     # with open(path, 'w') as file:
#     #     file.writelines(smvlines)


def mealy2nusmv_withintermediate(fsm: MealyMachine):

    # Collect fsm info
    states = fsm.get_states()



    alphabet = fsm.get_alphabet()

    inputs = set()
    outputs = set()
    statenames = set()
    initial_state_name = fsm.initial_state.name

    for state in states:
        statenames.add(state.name)
        for input, (next_state, output) in state.edges.items():
            inputs.add(input)
            outputs.add(output)

    # Get a comma separated list of the state names + extra intermediate output states
    # The intermediate states are named *original state name*_o_*input*
    statenames_with_intermediate = []
    for statename in statenames:
        statenames_with_intermediate.append(statename)
        for a in alphabet:
            statenames_with_intermediate.append(f'{statename}_o_{a}')

    statenames_with_intermediate = ",".join(statenames_with_intermediate)

    first_valid_inputs = []
    for input, (next_state, output) in fsm.initial_state.edges.items():
        if output != "invalid_input":
            first_valid_inputs.append(input)

    # Assemble smv file
    smvlines = []
    smvlines.append("MODULE main\n")
    smvlines.append("VAR\n")
    smvlines.append("\tstate : {" + statenames_with_intermediate + "};\n")
    smvlines.append("\toutput: {" + ",".join(outputs) + "," + ",".join(inputs) + "};\n")
    smvlines.append("ASSIGN\n")
    smvlines.append(f"\tinit(state) := {initial_state_name};\n")
    smvlines.append("\tnext(state) := case\n")

    for state in states:
        for input, (next_state, output) in state.edges.items():
            if output != "invalid_input":
                intermediate_name = f'{state.name}_o_{input}'
                smvlines.append(f"\t\t\tstate = {state.name}  & output = {input}: {intermediate_name};\n")
                smvlines.append(f"\t\t\tstate = {intermediate_name} : {next_state.name};\n")

    smvlines.append("\t\t\tTRUE : state;\n")
    smvlines.append("\tesac;\n")

    # The initial inputs also can't be invalid input,
    # So we cannot just choose any alphabet character
    #smvlines.append("\tinit(output) := {" + ",".join(alphabet) + "};\n")
    smvlines.append("\tinit(output) := {" + ",".join(first_valid_inputs) + "};\n")
    smvlines.append("\tnext(output) := case\n")

    for state in states:
        for input, (next_state, output) in state.edges.items():
            if output != "invalid_input":
                intermediate_name = f'{state.name}_o_{input}'
                smvlines.append(f"\t\t\tstate = {state.name} & next(state) = {intermediate_name} : {output};\n")
                valid_next_inputs = [n_input for (n_input, (_, n_output)) in next_state.edges.items()
                                     if n_output != "invalid_input"]
                if len(valid_next_inputs) > 0:
                    smvlines.append(f"\t\t\tstate = {intermediate_name} : " + "{" + ",".join(valid_next_inputs) + "};\n")

    smvlines.append("\t\t\tTRUE : output;\n")

    smvlines.append("\tesac;\n")

    return smvlines

    # with open(path, 'w') as file:
    #     file.writelines(smvlines)
#
# def rersltl2smv(ltlpath, mappingpath):
#
#     name_to_c, c_to_name = constructmapping(mappingpath)
#
#     ltl_lines = []
#
#     inputs = []
#     outputs = []
#
#     with open(ltlpath, 'r') as file:
#         for line in file.readlines():
#             # Grab inputs
#             if line.startswith('#inputs'):
#                 match = re.search('\[(.*)\]', line)
#                 inputs = match.group(1).split(', ')
#
#             # Grab outputs
#             if line.startswith('#outputs'):
#                 match = re.search('\[(.*)\]', line)
#                 outputs = match.group(1).split(', ')
#
#             # Grab LTL rules
#             if not line.startswith('#') and len(line.strip()) > 0:
#
#                 # Ez replacements
#                 line = line\
#                     .replace('true', 'TRUE')\
#                     .replace('false', 'FALSE')\
#
#                 # Replace variables
#                 for invar in inputs:
#                     line = line.replace(invar, f'(input = {name_to_c[invar]})')
#                 for outvar in outputs:
#                     line = line.replace(outvar, f'(output = {name_to_c[outvar]})')
#
#                 # Rewrite formulae
#                 # NuSMV uses V for release, rers uses R
#                 line = re.sub(' R ', ' V ', line)
#
#                 # NuSMV does not have weak until (rers WU), so we rewrite it
#                 # from p WU q -> (p U q | G p)
#                 match = re.search('(\d+) W (\d+)', line)
#                 while match:
#                     p = match.group(1)
#                     q = match.group(2)
#                     line = re.sub('(\d+) W (\d+)', f'({p} U {q} | G {p})', line, count=1)
#                     match = re.search('(\d+) W (\d+)', line)
#
#                 ltl_lines.append(line)
#
#     return [f'LTLSPEC NAME rule{i} := {line}' for i, line in enumerate(ltl_lines)]

def rersltl2smv_withintermediate(ltlpath, mappingpath):

    name_to_c, c_to_name = constructmapping(mappingpath)

    ltl_lines = []

    inputs = []
    outputs = []

    with open(ltlpath, 'r') as file:
        for line in file.readlines():
            # Grab inputs
            if line.startswith('#inputs'):
                match = re.search('\[(.*)\]', line)
                inputs = match.group(1).split(', ')

            # Grab outputs
            if line.startswith('#outputs'):
                match = re.search('\[(.*)\]', line)
                outputs = match.group(1).split(', ')

            # Grab LTL rules
            if not line.startswith('#') and len(line.strip()) > 0:

                # Rers 2019 uses WU instead of W for weak until, replace it
                line = re.sub(' WU ', ' W ', line)

                # Use spot to rewrite weak until formula if present
                line = rewrite_weakuntil(line)

                # Ez replacements
                line = line\
                    .replace('true', 'TRUE')\
                    .replace('false', 'FALSE')\
                #
                # # NuSMV does not have weak until (rers WU), so we rewrite it
                # # from p WU q -> (p U q | G p)
                # # This regex is bad and fragile and if we did it the right way
                # # we would parse the rules into an AST and use rewrite rules
                # # but no time for that
                # w_regex = r'([a-zA-z!]+) W ([a-zA-z!]+)'
                # match = re.search(w_regex, line)
                # while match:
                #     p = match.group(1)
                #     q = match.group(2)
                #     line = re.sub(w_regex, f'({p} U {q} | G {p})', line, count=1)
                #     match = re.search(w_regex, line)

                # Replace variables
                for invar in inputs:
                    line = line.replace(invar, f'(output = {name_to_c[invar]})')
                for outvar in outputs:
                    # It is possible for an output to be missing from the mapping,
                    # since the mapping is auto generated based on the model,
                    # a missing output mapping can never happen and thus always
                    # evaluates to FALSE
                    if outvar in name_to_c:
                        line = line.replace(outvar, f'(output = {name_to_c[outvar]})')
                    else:
                        line = line.replace(outvar, f'FALSE')

                # Rewrite formulae
                # NuSMV uses V for release, rers uses R
                line = re.sub(' R ', ' V ', line)

                print('{:10}'.format("Written:"), line.strip())
                ltl_lines.append(line)

    return [f'LTLSPEC NAME rule{i} := {line}\n' for i, line in enumerate(ltl_lines)]

def constructmapping(mappingpath):
    name_to_c = {}
    c_to_name = {}

    with open(mappingpath, 'r') as file:
        for line in file:
            # remove double whitespace
            line = re.sub(' +', ' ', line)
            line = re.sub('\t', ' ', line).strip()
            a, b = line.split(' ')

            # Build mapping
            name_to_c[a] = b
            c_to_name[b] = a

    return name_to_c, c_to_name

if __name__ == "__main__":
    s1 = MealyState('s1')
    s2 = MealyState('s2')
    s3 = MealyState('s3')

    s1.add_edge('a', 'nice', s2)
    s1.add_edge('b', 'a', s1)
    s2.add_edge('a', 'nice', s3)
    s2.add_edge('b', 'back_lol', s1)
    s3.add_edge('a', 'b', s3)
    s3.add_edge('b', 'c', s1)

    mm = MealyMachine(s1)

    constrpath = '/home/tom/projects/lstar/rers/TrainingSeqLtlRers2020/Problem1/constraints-Problem1.txt'
    mappingpath= '/home/tom/projects/lstar/rers/TrainingSeqLtlRers2020/Problem1/Problem1_alphabet_mapping_C_version.txt'

    mealy_lines = mealy2nusmv_withintermediate(mm)
    ltl_lines = rersltl2smv_withintermediate(constrpath, mappingpath)

    with open('test.smv', 'w') as file:
        file.writelines(mealy_lines)
        file.writelines(ltl_lines)

    print('done')

import tempfile

from util.mealy2nusmv import mealy2nusmv_withintermediate, rersltl2smv_withintermediate
from pathlib import Path
import subprocess
import re


class NuSMVUtils:
    def __init__(self, constraints_path, mapping_path):
        self.constraints_path = constraints_path
        self.mapping_path = mapping_path

        self.name_to_c, self.c_to_name = self._constructmapping()

    # TODO: handle missing values
    def _constructmapping(self):
        name_to_c = {}
        c_to_name = {}

        with open(self.mapping_path, 'r') as file:
            for line in file:
                # remove double whitespace
                line = re.sub(' +', ' ', line)
                line = re.sub('\t', ' ', line).strip()
                a, b = line.split(' ')

                # Build mapping
                name_to_c[a] = b
                c_to_name[b] = a

        return name_to_c, c_to_name

    def run_ltl_check(self, fsm):
        # Build nusmv input file
        nusmv_file = self._assemble_nusmv_file(fsm)

        check_results = self._nusmv_interact(nusmv_file)

        return check_results

    def _nusmv_interact(self, nusmv_file):
        result = subprocess.run(['nusmv', nusmv_file], capture_output=True)
        assert result.returncode == 0, f"NuSMV failed to run: \n {result.stderr}"

        nusmv_output = result.stdout.decode()

        results = {}
        cur_rule = None
        counterexamples = {}
        # Parse the output
        for line in nusmv_output.splitlines():

            # Gather result per rule
            result = re.match(r'-- specification (.*) is (true|false)', line)
            if result:
                rule = result.group(1)
                answer = result.group(2)
                results[rule] = answer
                cur_rule = rule

            # Capture output lines after each disproven rule to construct a counterexample
            if cur_rule != None:
                output_result = re.match('\s*output = (\d+)', line)
                if output_result:
                    if cur_rule in counterexamples:
                        counterexamples[cur_rule].append(output_result.group(1))
                    else:
                        counterexamples[cur_rule] = [output_result.group(1)]
                if 'Loop starts here' in line:
                    if cur_rule in counterexamples:
                        counterexamples[cur_rule].append('-- Loop starts here')
                    else:
                        counterexamples[cur_rule] = ['-- Loop starts here']

        print("--- NuSMV Results ---")
        for idx, (rule, answer) in enumerate(results.items()):
            print(f'Rule #{idx}: {"{:6}".format(answer)}',
                  self._parse_counterexample(counterexamples[rule]) if rule in counterexamples else None)

        return [(rule, answer, self._parse_counterexample(counterexamples[rule]) if rule in counterexamples else None)
                for rule, answer in results.items()]

    # # TODO fix for cases with more than one loop
    # def _parse_counterexample(self, counterexample: list):
    #     if '-- Loop starts here' in counterexample:
    #         loop_begin = counterexample.index('-- Loop starts here') + 1
    #         loop = counterexample[loop_begin:-1]
    #         prefix = counterexample[0:loop_begin - 1]
    #     else:
    #         prefix = counterexample
    #         loop = None
    #
    #     ce_string_prefix = f'[{";".join(prefix)}]'
    #     if loop is not None:
    #         ce_string_loop = f'([{";".join(loop)}])*'
    #     else:
    #         ce_string_loop = ""
    #
    #     assert '-- Loop starts here' not in ce_string_prefix + ce_string_loop
    #
    #     return ce_string_prefix + ce_string_loop

    def _parse_counterexample(self, counterexample: list):
        # The prefix ends when the first loop begins
        prefix_end_idx = counterexample.index('-- Loop starts here')
        prefix = counterexample[0:prefix_end_idx]

        # Find all starts of loops (there can be multiple)
        loop_starts = [i for i, x in enumerate(counterexample) if x == '-- Loop starts here']

        # Extract the loop contents for all loops found
        loops = []
        for i, loop_start in enumerate(loop_starts):
            next_loop_start = None
            if i < len(loop_starts) - 1:
                next_loop_start = loop_starts[i + 1]

            this_loop = counterexample[loop_start + 1: next_loop_start - 1] if next_loop_start \
                else counterexample[loop_start + 1:-1]

            loops.append(this_loop)


        ce_string_prefix = f'[{";".join(prefix)}]'
        if len(loops) > 0:
            ce_string_loop = ''.join([f'([{";".join(loop)}])*' for loop in loops])
        else:
            ce_string_loop = ""

        assert '-- Loop starts here' not in ce_string_prefix + ce_string_loop

        return ce_string_prefix + ce_string_loop

    def _translate_counterexample(self, ce_string):
        prefix_str, loop_str = ce_string.split('(')

        prefix = re.match(r'\[(.*)\]', prefix_str).group(1).split(';')
        loop_result = re.match(r'\[(.*)\]', loop_str)
        if loop_result:
            loop = loop_result.group(1).split(';')
        else:
            loop = None

        ce_string_prefix = f'[{";".join([self.c_to_name[x] for x in prefix])}]'
        if loop is not None:
            ce_string_loop = f'([{";".join([self.c_to_name[x] for x in loop])}])*'
        else:
            ce_string_loop = ""
        return ce_string_prefix + ce_string_loop

    def _assemble_nusmv_file(self, fsm, target_path=None):
        if target_path is None:
            target_path = tempfile.mktemp('.smv')

        mealy_lines = mealy2nusmv_withintermediate(fsm)
        ltl_lines = rersltl2smv_withintermediate(self.constraints_path, self.mapping_path)

        with open(target_path, 'w') as file:
            file.writelines(mealy_lines)
            for line in ltl_lines:
                file.write(f'{line}\n')

        return target_path


if __name__ == '__main__':
    constrpath = '/home/tom/projects/lstar/rers/TrainingSeqLtlRers2020/Problem1/constraints-Problem1.txt'
    mappingpath = '/home/tom/projects/lstar/rers/TrainingSeqLtlRers2020/Problem1/Problem1_alphabet_mapping_C_version.txt'

    nusmv = NuSMVUtils(constrpath, mappingpath)

    path = '/home/tom/projects/lstar/experiments/rers/smv/TrainingSeqLtlRers2020/Problem1.smv'

    nusmv._nusmv_interact(path)

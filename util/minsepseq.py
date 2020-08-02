import subprocess
import tempfile

from graphviz import Digraph

from suls.mealymachine import MealyMachine
import re

from util.dotloader import load_mealy_dot

distsetpath = "/home/tom/projects/lstar/util/distset"

def _render(fsm: MealyMachine, filename):
    g = Digraph('G', filename=filename)
    g.attr(rankdir='LR')

    states = fsm.get_states()

    # Add states
    for state in states:
        g.node(state.name)

    # Add transitions:
    for state in states:
        for action, (other_state, output) in state.edges.items():
            g.edge(state.name, other_state.name, label=f'{action}/{output}')

    g.save()

def _check_distinguishing_set(fsm, dset):
    outputs = _get_dset_outputs(fsm, dset)

    if len(set(outputs.values())) < len(outputs):
        print("Not unique", outputs)
        return False
    else:
        print('succes!', len(outputs), 'states,', len(set(outputs)), 'unique outputs')
        return True

def _get_dset_outputs(fsm, dset):
    states = fsm.get_states()
    outputs = {}
    for state in states:
        mm = MealyMachine(state)
        out = []
        for dseq in dset:
            out.append(mm.process_input(dseq))
            mm.reset()
        outputs[state] = tuple(out.copy())
    return outputs

def get_distinguishing_set(fsm: MealyMachine, check=True):
    path = tempfile.mktemp(".gv")

    _render(fsm, path)

    dset = _run_distset(path)

    if check:
        _check_distinguishing_set(fsm, dset)

    return dset

def _run_distset(path_to_dot):

    cases = {
        "State": {},
        "Output": {},
        "Input": {}
    }

    suffixes = []

    result = subprocess.run([distsetpath, '-path', path_to_dot], capture_output=True)
    for line in result.stdout.decode().split('\n'):

        if re.match("State|Output|Input .*", line):
            case, original, id = line.split(' ')
            cases[case][id] = original

        if re.match("Suffix .*", line):
            suffix = []
            line = line.replace("Suffix ", "")
            for a in line.strip().split(" "):
                if len(a) > 0:
                    suffix.append(cases["Input"][a])

            suffixes.append(tuple(suffix))

    return suffixes

if __name__ == "__main__":
    path = "/home/tom/projects/lstar/rers/industrial/m132.dot"

    fsm = load_mealy_dot(path)

    get_distinguishing_set(fsm, check=True)

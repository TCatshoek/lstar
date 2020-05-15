from typing import Union, List, Dict
from suls.dfa import DFA
from suls.mealymachine import MealyMachine, MealyState
from collections import namedtuple
from graphviz import Digraph
import tempfile

from util.dotloader import load_mealy_dot
from itertools import product

PState = namedtuple('PState', 'original current')


class Partition:
    def __init__(self, states=None, path=None):
        if states is None:
            states = []
        if path is None:
            path = []

        self.states: List[PState] = states
        self.children = {}
        self.path = path

    def append(self, state: PState):
        self.states.append(state)

    def add_child(self, input, child):
        self.children[input] = child
        new_path = self.path.copy()
        new_path.append(input)
        child._set_path(new_path)

    def is_closed(self):
        return len(self.states) <= 1

    def __len__(self):
        return len(self.states)


class PartitionNode:
    def __init__(self, states, alphabet, path=tuple()):
        self.path = []
        self.states = states
        self.A = alphabet
        self.splitter = None
        self.children = []
        self.path = path

    def split(self):
        print('trying split')
        n_partitions = 0
        potential_children = {}
        splitter = None

        n_repeat = 1
        while n_partitions < 2:
            print(n_repeat)

            for a in product(self.A, repeat=n_repeat):
                cur_seen_outputs = set()
                potential_children.clear()

                for og_state, cur_state in self.states:
                    tmp_state = cur_state
                    tmp_out = None
                    for cur_a in a:
                        tmp_state, tmp_out = tmp_state.next(cur_a)
                    next_state, output = tmp_state, tmp_out

                    cur_seen_outputs.add(output)

                    if output in potential_children:
                        potential_children[output].append(PState(og_state, cur_state))
                    else:
                        potential_children[output] = [PState(og_state, cur_state)]

                n_partitions = len(cur_seen_outputs)
                if n_partitions > 1:
                    self.splitter = a
                    break

            n_repeat += 1

        print('found split', self.splitter, potential_children)
        for output, states in potential_children.items():
            self.children.append(PartitionNode(states, self.A, self.path + self.splitter))

        return self.splitter, self.children


class PartitionTree:
    def __init__(self, fsm: MealyMachine):
        self.fsm = fsm
        self.A = fsm.get_alphabet()

        self.states = self.fsm.get_states()
        self.root = PartitionNode([PState(state.name, state) for state in self.states], self.A)

        # Keep track of what layers partition nodes are in
        self.layers = [[self.root]]
        self.cur_layer = 0

        self.wanted = set([state.name for state in fsm.get_states()])
        self.closed = set()
        self.solution = set()

    def build(self):
        while not self.closed == self.wanted:
            print('Building layer', self.cur_layer)
            self.build_layer()

    def build_layer(self):
        cur_layer_nodes = self.layers[self.cur_layer]
        next_layer_nodes = []

        for cur_node in cur_layer_nodes:
            if len(cur_node.states) > 1:
                splitter, next_layer_tmp = cur_node.split()
                next_layer_nodes += next_layer_tmp
                self.solution.add(splitter)
            else:
                self.closed.add(cur_node.states[0].original)

        self.layers.append(next_layer_nodes)
        self.cur_layer += 1


def get_distinguishing_set(fsm: MealyMachine):
    ptree = PartitionTree(fsm)
    ptree.build()
    return ptree.solution


import pickle

if __name__ == '__main__':
    #hyp: MealyMachine = pickle.load(open('../hyp.p', 'rb'))

    path = "/home/tom/projects/lstar/rers/industrial/m95.dot"

    hyp = load_mealy_dot(path)

    dset = get_distinguishing_set(hyp)

    # dset = walkTree2(tree, mm.get_states())

    print(dset)

    #dset = set(list(dset)[0:5])

    states = hyp.get_states()
    outputs = {}
    for state in states:
        mm = MealyMachine(state)
        out = []
        for dseq in dset:
            out.append(mm.process_input(dseq))
            mm.reset()
        outputs[state] = tuple(out.copy())
        out = []

    if len(set(outputs.values())) < len(outputs):
        print("Not unique", outputs )
    else:
        print('succes!', len(outputs), 'states,', len(set(outputs)), 'unique outputs' )

    # drawTree(tree)

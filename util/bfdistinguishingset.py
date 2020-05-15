from typing import Union, List, Dict
from suls.dfa import DFA
from suls.mealymachine import MealyMachine, MealyState
from collections import namedtuple
from graphviz import Digraph
import tempfile

from util.dotloader import load_mealy_dot

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

    def append(self, state:PState):
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
    def __init__(self):
        self.partitions = {}
        self._path = []

    def add(self, response, state: PState):
        if response in self.partitions:
            self.partitions[response].append(state)
        else:
            self.partitions[response] = Partition([state])
        # Make sure the path is correctly set
        self.partitions[response].path = self._path.copy()

    def _set_path(self, path):
        self._path = path.copy()
        for partition in self.partitions.values():
            partition.path = path.copy()

    def find_closed(self):
        # Finds all partitions with one PState, and returns those PStates
        return [x.states[0] for x in filter(lambda x: x.is_closed(), self.partitions.values())]


class PartitionTree:
    def __init__(self, fsm: MealyMachine):
        self.root = PartitionNode()

        # Keep track of what layers partition nodes are in
        self.layers = [[self.root]]
        self.cur_layer = 0

        self.wanted = set([state.name for state in fsm.get_states()])
        self.closed = set()
        self.solutions = {}

        self.fsm = fsm
        self.A = fsm.get_alphabet()

    def build(self):
        states = self.fsm.get_states()

        for state in states:
            self.root.add(None, PState(state.name, state))

        while not self.closed == self.wanted:
            print('Building layer', self.cur_layer)
            self.build_layer()

    def build_layer(self):
        cur_layer_nodes = self.layers[self.cur_layer]
        next_layer_nodes = []

        for cur_node in cur_layer_nodes:
            for cur_partition in cur_node.partitions.values():

                # If this partition is closed, we don't need to continue traversing and can add the solution
                if cur_partition.is_closed():
                    closed_name = cur_partition.states[0].original
                    if closed_name not in self.closed:
                        print('closed', closed_name)
                        self.closed.add(closed_name)
                        self.solutions[closed_name] = tuple(cur_partition.path)

                # If not, continue building the subtree until we can close the partition
                else:
                    for a in self.A:

                        # Create new partition node
                        new_partition_node = PartitionNode()

                        # Assign next states to partition
                        for og_state, cur_state in cur_partition.states:
                            next_state, output = cur_state.next(a)
                            new_partition_node.add(output, PState(og_state, next_state))

                        # Hook up partition node as child of parent partition
                        cur_partition.add_child(a, new_partition_node)

                        # Don't forget to add it to the layer bookkeeping
                        next_layer_nodes.append(new_partition_node)

        self.layers.append(next_layer_nodes)
        self.cur_layer += 1

def get_distinguishing_set(fsm: MealyMachine):
    ptree = PartitionTree(fsm)
    ptree.build()
    return ptree.solutions


import pickle
if __name__ == '__main__':
    # hyp: MealyMachine = pickle.load(open('../hyp.p', 'rb'))
    path = "/home/tom/projects/lstar/rers/industrial/m54.dot"

    hyp = load_mealy_dot(path)

    dset = set(get_distinguishing_set(hyp).values())

    #dset = walkTree2(tree, mm.get_states())

    print(dset)

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

    if len(set(outputs)) < len(outputs):
        print(outputs, "Not unique")
    else:
        print('succes!')



    #drawTree(tree)

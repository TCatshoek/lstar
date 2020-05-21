from typing import Union, List, Dict
from suls.dfa import DFA
from suls.mealymachine import MealyMachine, MealyState
from collections import namedtuple
from graphviz import Digraph
import tempfile

from util.dotloader import load_mealy_dot
from itertools import product

PState = namedtuple('PState', 'original current')


# WARNING: This code is ultra jank but it works on all tested (HUGE) mealy machines as long as they are minimal
class PartitionNode:
    def __init__(self, states, alphabet, acceptable=False, stable=False):
        self.states = states
        self.A = alphabet
        self.splitter = None
        self.children = []

        self.acceptable = acceptable
        self.stable = stable
        self.isleaf = True

    def split_output(self):
        #print('trying split')
        n_partitions = 0
        potential_children = {}

        for a in self.A:
            cur_seen_outputs = set()
            potential_children.clear()

            for cur_state in self.states:

                next_state, output = cur_state.next(a)

                cur_seen_outputs.add(output)

                if output in potential_children:
                    potential_children[output].append(cur_state)
                else:
                    potential_children[output] = [cur_state]

            n_partitions = len(cur_seen_outputs)
            if n_partitions > 1:
                self.splitter = (a,)
                break

        if n_partitions < 2:
            #print('Made acceptable')
            self.acceptable = True
            return None, None

        #print('found split', self.splitter, potential_children)

        for output, states in potential_children.items():
            self.children.append(PartitionNode(states, self.A, self.acceptable, self.stable))

        self.isleaf = len(self.children) == 0

        return self.splitter, self.children

    def split_state(self, ptree):
        name = " ".join([state.name for state in self.states])
        #print("Split-stating ", " ".join([state.name for state in self.states]), "leaf:", self.isleaf, 'acceptable:', self.acceptable, 'stable:', self.stable)

        if len(self.states) == 1:
            self.stable = True
            self.acceptable = True
            return None, None

        # Find split using state after a
        seen_successor_states = set()
        seen_partitions = set()
        next_states_set = set()

        for a in self.A:
            seen_successor_states.clear()
            next_states_set.clear()
            seen_partitions.clear()

            for cur_state in self.states:
                next_state, output = cur_state.next(a)
                seen_successor_states.add(next_state.name)
                seen_partitions.add(ptree.get_partition(next_state))
                next_states_set.add(next_state)

            if len(seen_partitions) > 1:
                self.splitter = (a,)
                break

        if self.splitter is None:
            #print("no splitter :(")
            self.stable = False
            return None, None

        lca = ptree.get_lca(next_states_set)
        assert lca.splitter is not None

        self.splitter = self.splitter + lca.splitter

        # Now assign states to children according to their output given after the splitter
        children = {}
        for state in self.states:
            next_state = state
            next_out = None
            for a in self.splitter:
                next_state, next_out = next_state.next(a)

            if next_out in children:
                children[next_out].append(state)
            else:
                children[next_out] = [state]

        for output, states in children.items():
            self.children.append(PartitionNode(states, self.A, self.acceptable, self.stable))

        self.isleaf = False

        return self.splitter, self.children


class PartitionTree:
    def __init__(self, fsm: MealyMachine):
        self.fsm = fsm
        self.A = fsm.get_alphabet()

        self.states = self.fsm.get_states()
        self.root = PartitionNode(self.states, self.A)

        self.nodes = [self.root]

        self.wanted = set([state.name for state in fsm.get_states()])
        self.closed = set()
        self.solution = set()

    # The PTree is acceptable if all nodes are acceptable
    def is_acceptable(self):
        is_acc = True
        for node in self.nodes:
            if node.isleaf:
                is_acc &= node.acceptable
        return is_acc

    def is_stable(self):
        is_stab = True
        for node in self.nodes:
            if node.isleaf:
                is_stab &= node.stable
        return is_stab

    def get_leaves(self):
        return filter(lambda x: len(x.children) == 0, self.nodes)

    # Gets the leaf partition that holds the given state
    def get_partition(self, state):
        tmp = list(filter(lambda x: state in x.states, self.get_leaves()))
        assert len(tmp) == 1
        return tmp[0]

    # Can we just get the smallest partition node which contains all states?
    def get_lca(self, states):
        states = set(states)

        best_node = None
        best_len = len(self.states) + 1

        for node in self.nodes:
            node_states = set(node.states)

            if states.issubset(node_states):
                if len(node_states) < best_len:
                    best_len = len(node_states)
                    best_node = node

        return best_node


    def build(self):
        while not self.is_acceptable():
            cur_nodes = filter(lambda x: x.isleaf, self.nodes.copy())
            for node in cur_nodes:
                splitter, children = node.split_output()
                if splitter is not None:
                    self.solution.add(splitter)
                if children is not None:
                    for child in children:
                        self.nodes.append(child)

        #self.render_graph()

        while not self.is_stable():
            #print('attempting to stabilize')
            cur_nodes = filter(lambda x: x.isleaf and not x.stable, self.nodes.copy())
            for node in cur_nodes:
                splitter, children = node.split_state(self)
                if splitter is not None:
                    self.solution.add(splitter)
                if children is not None:
                    for child in children:
                        self.nodes.append(child)

        #self.render_graph()



    def render_graph(self, filename=None):
        if filename is None:
            filename = tempfile.mktemp('.gv')

        g = Digraph('G', filename=filename)

        for node in self.nodes:
            node_name = " ".join([state.name for state in node.states]) + f" / {node.splitter}"
            g.node(node_name)

            for child in node.children:
                child_name = " ".join([state.name for state in child.states]) + f" / {child.splitter}"
                g.edge(node_name, child_name)

        g.view()


def check_distinguishing_set(fsm, dset):
    states = fsm.get_states()
    outputs = {}
    for state in states:
        mm = MealyMachine(state)
        out = []
        for dseq in dset:
            out.append(mm.process_input(dseq))
            mm.reset()
        outputs[state] = tuple(out.copy())

    if len(set(outputs.values())) < len(outputs):
        print("Not unique", outputs)
        return False
    else:
        print('succes!', len(outputs), 'states,', len(set(outputs)), 'unique outputs')
        return True

# Uses partition refinement to find a distinguishing set for a given mealy machine
def get_distinguishing_set(fsm: MealyMachine):
    ptree = PartitionTree(fsm)
    ptree.build()

    dset = ptree.solution

    assert check_distinguishing_set(fsm, dset)

    if len(dset) == 0:
        dset.add(tuple())

    return dset


import time
if __name__ == '__main__':
    path = "/home/tom/projects/lstar/rers/industrial/m27.dot"

    fsm = load_mealy_dot(path)

    t0 = time.time()
    dset = get_distinguishing_set(fsm)
    t1 = time.time()

    print(t1 - t0)


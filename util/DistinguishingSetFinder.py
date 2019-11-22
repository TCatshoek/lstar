from typing import Union, List
from suls.dfa import DFA
from suls.mealymachine import MealyMachine
from collections import namedtuple


class Partition:
    def __init__(self, states=None, edges=None):
        if edges is None:
            edges = {}
        if states is None:
            states = []

        self.edges = edges
        self.states = states

    def __len__(self):
        return len(self.states)

class PTreeNode:
    def __init__(self, partitions: List[Partition] = None, prev_input=tuple()):
        if partitions is None:
            partitions = list()

        # Keep track of the path to end up in this node
        self.prev_input = prev_input

        # Keep track of the partitions this path splits the states in
        self.partitions: List[Partition] = partitions

    def _is_leaf(self):
        # Leaf nodes have one partition with one state
        return len(self.partitions) == 1 and len(self.partitions[0]) == 1




# Finds the optimal distinguishing set for a given state machine using
# based on https://ieeexplore.ieee.org/document/1672636
def getDistinguishingSet(fsm: MealyMachine):
    states = fsm.get_states()
    alphabet = fsm.get_alphabet()

    root = PTreeNode([Partition(states)])

    curnode = root

    for p in curnode.partitions:
        for a in alphabet:
            # Add outgoing edge from partition
            newNode = PTreeNode([])
            p.edges[a] = newNode

            # Assign states to nodes according to their responses
            for state in p.states:
                nextstate, response = state.next(a)







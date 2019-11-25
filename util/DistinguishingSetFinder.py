from typing import Union, List, Dict
from suls.dfa import DFA
from suls.mealymachine import MealyMachine, MealyState
from collections import namedtuple
from graphviz import Digraph
import tempfile

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

    def getStateNames(self):
        return set([state.name for state in self.states])

    def addState(self, state):
        # Only add a state if no state with the same name is present
        cur_names = [state.name for state in self.states]
        if state.name not in cur_names:
            self.states.append(state)

class PTreeNode:
    def __init__(self, partitions: Dict[str, Partition] = None, prev_input=tuple(), parent: Partition = None):
        if partitions is None:
            partitions = {}

        # Keep track of the path to end up in this node
        self.prev_input = prev_input

        # Keep track of the partitions this path splits the states in
        self.partitions: Dict[str, Partition] = partitions
        self.parent: Partition = parent

    def is_leaf(self):
        # Leaf nodes have one partition with one state
        return len(self.partitions.keys()) == 1 and len(list(self.partitions.values())[0]) == 1




# Finds the optimal distinguishing set for a given state machine using
# based on https://ieeexplore.ieee.org/document/1672636
def getDistinguishingSet(fsm: MealyMachine):
    # Setup state machine
    states = fsm.get_states()
    alphabet = fsm.get_alphabet()

    # Keep track of the partitions already seen, to prevent loops
    seen = []

    root = PTreeNode({'': Partition(states)})
    buildTree(root, alphabet, seen)

    return root

def buildTree(node: PTreeNode, alphabet, seen):
    if node.is_leaf():
        return

    for curpartition in node.partitions.values():
        # Prevent loops
        if curpartition.getStateNames() in seen:
            continue

        for a in alphabet:
            # Add outgoing edge from partition
            new_node = PTreeNode(prev_input=node.prev_input + (a,), parent=curpartition)
            curpartition.edges[a] = new_node

            # Assign states to nodes according to their responses
            for state in curpartition.states:
                nextstate, response = state.next(a)

                if a not in new_node.partitions.keys():
                    new_node.partitions[a] = Partition()

                new_node.partitions[a].addState(nextstate)

        #seen.append(curpartition.getStateNames())
        for new_node in curpartition.edges.values():
            buildTree(new_node, alphabet, seen)

def drawTree(node: PTreeNode):
    graph = Digraph()

    to_visit = [node]

    while len(to_visit) > 0:
        cur_node = to_visit.pop()

        if cur_node.is_leaf():
            c = Digraph()
            for partition in cur_node.partitions.values():
                c.node(name=str(partition.getStateNames()))
                graph.subgraph(c)

        else:
            c = Digraph(node_attr={'shape': 'box'})
            for partition in cur_node.partitions.values():
                c.node(name=str(partition.getStateNames()))
                graph.subgraph(c)

        for partition in cur_node.partitions.values():
            for other_node in partition.edges.values():
                to_visit.append(other_node)

    graph.view(tempfile.mktemp('.gv'))

def walkTree(root: PTreeNode):
    to_visit = [root]
    dset = set()

    while len(to_visit) > 0:
        cur_node = to_visit.pop()

        if cur_node.is_leaf():
            print(cur_node, cur_node.prev_input)
            dset.add(cur_node.prev_input)

        for partition in cur_node.partitions.values():
            for other_node in partition.edges.values():
                to_visit.append(other_node)

    return dset


if __name__ == '__main__':
    # Set up an example mealy machine
    s1 = MealyState('1')
    s2 = MealyState('2')
    s3 = MealyState('3')
    # s4 = MealyState('4')

    s1.add_edge('a', 'nice', s2)
    s1.add_edge('b', 'B', s1)
    s2.add_edge('a', 'nice', s3)
    s2.add_edge('b', 'back', s1)
    s3.add_edge('a', 'A', s3)
    s3.add_edge('b', 'back', s1)
    # s4.add_edge('a', 'loop', s4)
    # s4.add_edge('b', 'loop', s4)

    mm = MealyMachine(s1)

    # # Set up an example mealy machine
    # s1 = MealyState('1')
    # s2 = MealyState('2')
    # s3 = MealyState('3')
    # s4 = MealyState('4')
    #
    # s1.add_edge('a', 'nice', s2)
    # s1.add_edge('b', 'nic2', s3)
    #
    # s2.add_edge('a', 'nicea', s4)
    # s2.add_edge('b', 'back', s1)
    #
    # s3.add_edge('a', 'nice', s4)
    # s3.add_edge('b', 'back', s1)
    #
    # s4.add_edge('a', 'loop', s4)
    # s4.add_edge('b', 'loop', s4)
    #
    # mm = MealyMachine(s1)

    tree = getDistinguishingSet(mm)

    dset = walkTree(tree)

    states = [s1, s2, s3] #, s4]
    for state in states:
        mm = MealyMachine(state)
        print(state)
        for dseq in dset:
            print([mm.process_input(x) for x in dseq])
            mm.reset()

    drawTree(tree)

from typing import Union, List, Dict
from suls.dfa import DFA
from suls.mealymachine import MealyMachine, MealyState
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

    def addState(self, state):
        # Only add a state if no state with the same name is present
        cur_names = [state.name for state in self.states]
        if state.name not in cur_names:
            self.states.append(state)

class PTreeNode:
    def __init__(self, partitions: Dict[str, Partition] = None, prev_input=tuple()):
        if partitions is None:
            partitions = {}

        # Keep track of the path to end up in this node
        self.prev_input = prev_input

        # Keep track of the partitions this path splits the states in
        self.partitions: Dict[str, Partition] = partitions

    def is_leaf(self):
        # Leaf nodes have one partition with one state
        return len(self.partitions.keys()) == 1 and len(list(self.partitions.values())[0]) == 1




# Finds the optimal distinguishing set for a given state machine using
# based on https://ieeexplore.ieee.org/document/1672636
def getDistinguishingSet(fsm: MealyMachine):
    states = fsm.get_states()
    alphabet = fsm.get_alphabet()

    root = PTreeNode({'': Partition(states)})

    buildTree(root, alphabet)

    return root

def buildTree(node: PTreeNode, alphabet):
    if node.is_leaf():
        return

    for curpartition in node.partitions.values():
        for a in alphabet:
            # Add outgoing edge from partition
            newNode = PTreeNode(prev_input=node.prev_input + (a,))
            curpartition.edges[a] = newNode

            # Assign states to nodes according to their responses
            for state in curpartition.states:
                nextstate, response = state.next(a)

                if a not in newNode.partitions.keys():
                    newNode.partitions[a] = Partition()

                newNode.partitions[a].addState(nextstate)

        for newNode in curpartition.edges.values():
            buildTree(newNode, alphabet)

def walkTree(root: PTreeNode):
    to_visit = [root]

    while len(to_visit) > 0:
        cur_node = to_visit.pop()

        if cur_node.is_leaf():
            print(cur_node, cur_node.prev_input)

        for partition in cur_node.partitions.values():
            for other_node in partition.edges.values():
                to_visit.append(other_node)


if __name__ == '__main__':
    # Set up an example mealy machine
    s1 = MealyState('1')
    s2 = MealyState('2')
    s3 = MealyState('3')

    s1.add_edge('a', 'nice', s2)
    s1.add_edge('b', 'B', s1)
    s2.add_edge('a', 'nice', s3)
    s2.add_edge('b', 'back', s1)
    s3.add_edge('a', 'A', s3)
    s3.add_edge('b', 'back', s1)

    mm = MealyMachine(s1)

    tree = getDistinguishingSet(mm)

    walkTree(tree)






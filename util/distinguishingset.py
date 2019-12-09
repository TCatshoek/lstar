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

    def __str__(self):
        return str(sorted(list(self.getStateNames())))

    def getStateNames(self):
        return set([state.name for state in self.states])

    def addState(self, state):
        # Only add a state if no state with the same name is present
        cur_names = [state.name for state in self.states]
        if state.name not in cur_names:
            self.states.append(state)

    def is_leaf(self):
        return len(self) == 1

class PTreeNode:
    def __init__(self, partitions: Dict[str, Partition] = None, prev_input=tuple(), parent: Partition = None):
        if partitions is None:
            partitions = {}

        # Keep track of the path to end up in this node
        self.prev_input = prev_input

        # Keep track of the partitions this path splits the states in
        self.partitions: Dict[str, Partition] = partitions
        self.parent: Partition = parent

    def __str__(self):
        return f'[{[f"{k}:{v.getStateNames()}" for k, v in self.partitions.items()]}]'

    def is_leaf(self):
        leaf = True
        for partition in self.partitions.values():
            leaf &= len(partition) == 1
        return leaf




# Finds the optimal distinguishing set for a given state machine using
# based on https://ieeexplore.ieee.org/document/1672636
def get_distinguishing_set(fsm: MealyMachine):
    # Setup state machine
    states = fsm.get_states()
    alphabet = fsm.get_alphabet()

    root = PTreeNode({'': Partition(states)})
    buildTree(root, alphabet)

    return walkTree2(root, states)


# TODO: non-recursive implementation
def buildTree(node: PTreeNode, alphabet, seen=list()):
    if node.is_leaf():
        return

    for curpartition in node.partitions.values():
        # Prevent loops
        if curpartition.getStateNames() in seen:
            continue

        if curpartition.is_leaf():
            continue

        for a in alphabet:
            # Add outgoing edge from partition
            new_node = PTreeNode(prev_input=node.prev_input + (a,), parent=curpartition)
            curpartition.edges[a] = new_node

            # Assign states to nodes according to their responses
            for state in curpartition.states:
                nextstate, response = state.next(a)

                if response not in new_node.partitions.keys():
                    new_node.partitions[response] = Partition()

                new_node.partitions[response].addState(nextstate)

        seen_tmp = seen.copy()
        seen_tmp.append(curpartition.getStateNames())
        for new_node in curpartition.edges.values():
            buildTree(new_node, alphabet, seen_tmp)

def drawTree(node: PTreeNode):
    graph = Digraph(graph_attr={'compound': 'true'})

    to_visit = [node]

    while len(to_visit) > 0:
        cur_node = to_visit.pop()

        with graph.subgraph(name=f'cluster_{str(hex(id(cur_node)))}') as c:
            print('making cluster', f'cluster_{str(hex(id(cur_node)))}')

            if cur_node.is_leaf():
                c.attr(style='filled', color='darkgrey')
            else:
                c.attr(style='filled', color='lightgrey')

            for partition in cur_node.partitions.values():
                c.node(name=str(hex(id(partition))), label=str(partition))
                for input, othernode in partition.edges.items():

                    to_visit.append(othernode)

                    otherpart = list(othernode.partitions.values())[0]
                    graph.edge(
                        str(hex(id(partition))),
                        str(hex(id(otherpart))),
                        _attributes={
                            'lhead': f'cluster_{str(hex(id(othernode)))}',
                            'label': str(input)
                        })


    graph.view(tempfile.mktemp('.gv'))

def walkTree(root: PTreeNode):
    to_visit = [root]
    dset = set()

    while len(to_visit) > 0:
        cur_node = to_visit.pop()

        for partition in cur_node.partitions.values():
            if partition.is_leaf():
                print('leaf', partition)
                dset.add(cur_node.prev_input)
            for other_node in partition.edges.values():
                to_visit.append(other_node)

    return dset

# BFS, check origin state on finding partition with single state
def walkTree2(root: PTreeNode, states: List[MealyState]):
    to_visit = [root]
    dset = set()

    # Keep track of which states we have found a sequence for already
    states_found = []

    while len(to_visit) > 0:
        cur_node = to_visit.pop(0)

        for partition in cur_node.partitions.values():
            if partition.is_leaf():
                # Where did we come from?
                cur_state = partition.states[0]
                path = cur_node.prev_input

                # Check what state we get in from all other states
                tmp = [(state, _trace(state, path)) for state in states]

                og_state = None
                for initial_state, later_state in tmp:
                    if later_state == cur_state and initial_state not in states_found:
                        og_state = initial_state
                        continue

                # If we found a sequence for all states, we can quit
                if set(states_found) == set(states):
                    return dset

                if og_state not in states_found:
                    dset.add(path)
                    states_found.append(og_state)


            for other_node in partition.edges.values():
                to_visit.append(other_node)

    return dset

def _trace(initial: MealyState, path):
    cur_state = initial
    for a in path:
        next_state, output = cur_state.next(a)
        cur_state = next_state
    return cur_state

if __name__ == '__main__':
    # Set up an example mealy machine
    # s1 = MealyState('1')
    # s2 = MealyState('2')
    # s3 = MealyState('3')
    # # s4 = MealyState('4')
    #
    # s1.add_edge('a', 'nice', s2)
    # s1.add_edge('b', 'B', s1)
    # s2.add_edge('a', 'nice', s3)
    # s2.add_edge('b', 'back', s1)
    # s3.add_edge('a', 'A', s3)
    # s3.add_edge('b', 'back', s1)
    # # s4.add_edge('a', 'loop', s4)
    # # s4.add_edge('b', 'loop', s4)
    #
    # mm = MealyMachine(s1)

    # # Set up an example mealy machine
    s1 = MealyState('1')
    s2 = MealyState('2')
    s3 = MealyState('3')
    s4 = MealyState('4')
    s5 = MealyState('5')

    s1.add_edge('a', 'nice', s2)
    s1.add_edge('b', 'nice', s3)

    s2.add_edge('a', 'nice!', s4)
    s2.add_edge('b', 'back', s1)

    s3.add_edge('a', 'nice', s4)
    s3.add_edge('b', 'back', s1)

    s4.add_edge('a', 'nice', s5)
    s4.add_edge('b', 'nice', s5)

    s5.add_edge('a', 'loop', s5)
    s5.add_edge('b', 'loop', s5)

    # s1.add_edge('a', 'a', s2)
    # s1.add_edge('b', 'b', s3)
    #
    # s2.add_edge('a', 'a', s4)
    # s2.add_edge('b', 'b', s4)
    #
    # s3.add_edge('a', 'a', s5)
    # s3.add_edge('b', 'b', s5)
    #
    # s4.add_edge('a', 'nice!', s4)
    # s4.add_edge('b', 'nice!', s4)
    #
    # s5.add_edge('a', 'loop', s5)
    # s5.add_edge('b', 'loop', s5)


    mm = MealyMachine(s1)

    dset = get_distinguishing_set(mm)

    #dset = walkTree2(tree, mm.get_states())

    print(dset)

    states = [s1, s2, s3, s4, s5]
    for state in states:
        mm = MealyMachine(state)
        print(state)
        for dseq in dset:
            print([mm.process_input(x) for x in dseq][-1])
            mm.reset()

    #drawTree(tree)

import tempfile
from collections import deque
from queue import Queue

from graphviz import Digraph

from equivalencecheckers.equivalencechecker import EquivalenceChecker
from suls.dfa import DFA, State
from itertools import product, chain, combinations, permutations
from functools import reduce
from equivalencecheckers.bruteforce import BFEquivalenceChecker
from learners.learner import Learner
from suls.sul import SUL

from teachers.teacher import Teacher
from typing import Set, Tuple, Optional, Iterable
from tabulate import tabulate
#
#
# class DTreeNode:
#     def __init__(self, isLeaf, suffix=None, state=None, temporary=False):
#         self.suffix = suffix
#         self.state = state
#         self.isLeaf = isLeaf
#         self.isTemporary = temporary
#
#         # Child connections
#         self._true = None
#         self._false = None
#
#         self.parent: DTreeNode = None
#
#     def add(self, value, node):
#         if value:
#             self.addTrue(node)
#         else:
#             self.addFalse(node)
#
#     def addTrue(self, node):
#         self._true = node
#         node.parent = self
#
#     def addFalse(self, node):
#         self._false = node
#         node.parent = self
#
#     def replace(self, new):
#         assert self.isLeaf, "You sure you want to split a non-leaf node?"
#         if self.parent._true == self:
#             self.parent._true = new
#         else:
#             self.parent._false = new
#         new.parent = self.parent
#         self.parent = None
#
#     def is_positive(self):
#         return self.parent._true == self
#
#     def getAncestors(self):
#         ancestors = []
#         parent = self.parent
#         while parent is not None:
#             ancestors.append(parent)
#             parent = parent.parent
#         return ancestors
#
#     def __str__(self):
#         return f'[DTreeNode: ({self.state if self.isLeaf else self.suffix}), T: {self._true}, F: {self._false}'
#
#
# class DTree:
#     def __init__(self):
#         # Dict keeping track of nodes so we can do easy lookups
#         self.nodes = {}
#
#         self.root = self.createInner(tuple())
#
#     def createLeaf(self, state):
#         node = DTreeNode(True, state=state)
#         self.nodes[state] = node
#         return node
#
#     def createInner(self, suffix, temporary=False):
#         node = DTreeNode(False, suffix=suffix, temporary=temporary)
#         self.nodes[suffix] = node
#         return node
#
#     # Retrieves all leaf nodes that are on the "True" subtree of their parent
#     def getAccepting(self):
#         return list(filter(lambda x: x.isLeaf and x.parent._true == x, self.nodes.values()))
#
#     def getRejecting(self):
#         return list(filter(lambda x: x.isLeaf and x.parent._false == x, self.nodes.values()))
#
#     # Gets the leaf node holding the given state
#     def getLeaf(self, state):
#         return list(filter(lambda x: x.isLeaf and x.state == state, self.nodes.values()))[0]
#
#     # Gets all nodes that are potentially block root nodes
#     def getBlockRoots(self):
#         roots = list(filter(lambda x: x.isTemporary
#                             and not x.isLeaf
#                             and x.parent is not None
#                             and not x.parent.isTemporary,
#                             self.nodes.values()))
#         return roots
#
#     def getFinalizedDiscriminators(self):
#         return list(filter(lambda x: not x.isTemporary and not x.isLeaf, self.nodes.values()))
#
#     def getLowestCommonAncestor(self, n1, n2):
#         n1_ancestors = n1.getAncestors()
#         n2_ancestors = n2.getAncestors()
#
#         for i in range(1, min(len(n1_ancestors), len(n2_ancestors)) + 1):
#             n1_s = set(n1_ancestors[0:i])
#             n2_s = set(n2_ancestors[0:i])
#             intersection = n1_s.intersection(n2_s)
#
#             if len(intersection) > 0:
#                 assert len(intersection) == 1
#                 return intersection.pop()
#
#     def render_graph(self, filename=None, format='pdf'):
#         if filename is None:
#             filename = tempfile.mktemp('.gv')
#
#         g = Digraph('G', filename=filename)
#         # g.attr(rankdir='LR')
#
#         # Draw nodes
#         for node in self.nodes.values():
#             if not node.isLeaf:
#                 name = "".join(node.suffix) if len(node.suffix) > 0 else 'ε'
#                 if node.isTemporary:
#                     g.node(name, style='dotted')
#                 else:
#                     g.node(name)
#                 # Debug parent connections
#                 # if node.parent is not None:
#                 #     pname = "".join(node.parent.suffix) if len(node.parent.suffix) > 0 else 'ε'
#                 #     g.edge(name, pname, label='P')
#             else:
#                 g.node(node.state.name, shape='square')
#                 # Debug parent connections
#                 # if node.parent is not None:
#                 #     pname = "".join(node.parent.suffix) if len(node.parent.suffix) > 0 else 'ε'
#                 #     g.edge(node.state.name, pname, label='P')
#
#         # Draw edges
#         for node in self.nodes.values():
#             if node.isLeaf:
#                 continue
#             name = "".join(node.suffix) if len(node.suffix) > 0 else 'ε'
#             if node._true is not None:
#                 target = node._true.state.name if node._true.isLeaf else "".join(node._true.suffix)
#                 g.edge(name, target)#, label='T')
#             if node._false is not None:
#                 target = node._false.state.name if node._false.isLeaf else "".join(node._false.suffix)
#                 g.edge(name, target, style='dotted') #, label='F'
#
#         g.render(format=format, view=True)
#
#
# # A block is a maximal subtree of the discrimination tree
# # containing only temporary nodes
# class Block:
#     def __init__(self, root: DTreeNode):
#         self.root = root
#
#         self.innernodes = [self.root]
#         self.leafnodes = []
#         # BFS to gather temp inner and leaf nodes in subtree
#         to_visit = [self.root]
#         while len(to_visit) > 0:
#             cur = to_visit.pop()
#             for child in [cur._true, cur._false]:
#                 if child.isTemporary and not child.isLeaf and child not in self.innernodes:
#                     self.innernodes.append(child)
#                     to_visit.append(child)
#                 elif child.isLeaf:
#                     self.leafnodes.append(child)
#
#     def __str__(self):
#         return f"Block [Root: {self.root.suffix}, Nodes: {[y.suffix for y in filter(lambda x: x is not self.root, self.innernodes)]}]"
#
#     def split(self, final_discriminators, alphabet):
#         # Grab the root and find a replacement by prepending a character from the alphabet
#         # to an existing finalized discriminator
#
#         # Find the shortest one that works
#         # A discriminator works if it splits at least two states in the block
#         best_len = None
#         #for cur_disc in potential_discriminators:
#

from learners.TTTabstractlearner import DTreeNode, DTree, Block, TTTAbstractLearner

# Implements the TTT algorithm
class TTTDFALearner(TTTAbstractLearner):
    def __init__(self, teacher: Teacher):
        # Access sequences S + state bookkeeping
        self.S = {tuple(): State("s0")}

        super().__init__(teacher)

        # Add initial state to discrimination tree
        #initial_state = self.S[tuple()]
        #initial_state_output = self.query(tuple())
        #self.DTree.root.add(initial_state_output, self.DTree.createLeaf(initial_state))

    def sift(self, sequence):
        cur_dtree_node = self.DTree.root
        prev_dtree_node = None

        while not cur_dtree_node is None and not cur_dtree_node.isLeaf:
            # Figure out which branch we should follow
            seq = sequence + cur_dtree_node.suffix
            response = self.query(seq)
            prev_dtree_node = cur_dtree_node
            if response in cur_dtree_node.children:
                cur_dtree_node = cur_dtree_node.children[response]
            else:
                cur_dtree_node = None

        # If we end up on an empty node, we can add a new leaf pointing to the
        # state accessed by the given sequence
        if cur_dtree_node is None:
            new_acc_seq = sequence
            new_state = State(f's{len(self.S)}')
            new_dtree_node = self.DTree.createLeaf(new_state)
            self.S[new_acc_seq] = new_state
            prev_dtree_node.add(response, new_dtree_node)
            cur_dtree_node = new_dtree_node

        assert cur_dtree_node is not None, "Oof this shouldn't happen"
        assert cur_dtree_node.isLeaf, "This should always be a leaf node"
        assert cur_dtree_node.state is not None, "Leaf nodes should always represent a state"

        return cur_dtree_node.state

    def construct_hypothesis(self):
        # Keep track of the initial state
        initial_state = self.S[()]

        # Keep track of the amount of states, so we can sift again if
        # the sifting process created a new state
        n = len(list(self.S.items()))
        items_added = True

        # Todo: figure out a neater way to handle missing states during sifting than to just redo the whole thing
        while items_added:
            # Add transitions
            for access_seq, cur_state in list(self.S.items()):
                for a in self.A:
                    next_state = self.sift(access_seq + a)
                    output = self.query(access_seq + a)
                    cur_state.add_edge(a[0], next_state, override=True)

            # Check if no new state was added
            n2 = len((self.S.items()))

            items_added = n != n2
            # print("items added", items_added)

            n = n2

        # Find accepting states
        accepting_states = [state for access_seq, state in self.S.items() if self.query(access_seq)]

        return DFA(initial_state, accepting_states)


    # Decomposes the given counterexample, and updates the hypothesis
    # and discrimination tree accordingly
    def process_counterexample(self, counterexample):

        u, a, v = self.decompose(counterexample)

        # This state q_old needs to be split:
        q_old_state = self.get_state_from_sequence(u + a)
        q_old_acc_seq = self.get_access_sequence_from_state(q_old_state)

        # Store new state and access sequence
        q_new_acc_seq = self.get_access_sequence(u) + a
        q_new_state = State(f's{len(self.S)}')

        assert q_new_acc_seq not in self.S

        self.S[q_new_acc_seq] = q_new_state

        ### update the DTree:
        # find the leaf corresponding to the state q_old
        q_old_leaf = self.DTree.getLeaf(q_old_state)
        # and create a new inner node,
        new_inner = self.DTree.createInner(v, temporary=True)

        # replace the old leaf node with the new inner node
        q_old_leaf.replace(new_inner)

        # check what branch the children should go
        response_q_old = self.query(q_old_acc_seq + v)
        response_q_new = self.query(q_new_acc_seq + v)
        # response_q_old = self.query(u + v)
        # response_q_new = self.query(q_new_acc_seq + v)
        assert response_q_new != response_q_old, "uh oh this should never happen"

        # prepare leaf node for the new state
        q_new_leaf = self.DTree.createLeaf(q_new_state)

        # Add the children to the corresponding branch of the new inner node
        new_inner.add(response_q_new, q_new_leaf)
        new_inner.add(response_q_old, q_old_leaf)

        print("splitty boi", q_old_state.name, q_new_state.name)

class FakeEQChecker(EquivalenceChecker):

    def __init__(self, sul):
        super().__init__(sul)
        self.count = 0

    def test_equivalence(self, test_sul: SUL) -> Tuple[bool, Optional[Iterable]]:
        if self.count == 0:
            self.count += 1
            return False, ('b', 'b', 'b', 'a', 'a', 'a', 'b', 'b')
        else:
            return True, None


from suls.re_machine import RegexMachine

if __name__ == "__main__":
    # Matches the example run in the TTT paper
    sm = RegexMachine('b*(ab*ab*ab*ab*)*ab*ab*ab*')

    eqc = FakeEQChecker(sm)
    teacher = Teacher(sm, eqc)
    learner = TTTDFALearner(teacher)

    # Get the learners hypothesis
    hyp = learner.construct_hypothesis()
    # hyp.render_graph(tempfile.mktemp('.gv'))

    done, hyp = learner.refine_hypothesis(hyp)
    # hyp.render_graph(tempfile.mktemp('.gv'))

    hyp = learner.stabilize_hypothesis(hyp)
    # hyp.render_graph(tempfile.mktemp('.gv'))

    learner.finalize_discriminators()

    hyp = learner.construct_hypothesis()
    hyp.render_graph()
    learner.DTree.render_graph(tempfile.mktemp('.gv'))

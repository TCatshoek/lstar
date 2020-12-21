import tempfile
from collections import deque
from queue import Queue

from graphviz import Digraph

from equivalencecheckers.equivalencechecker import EquivalenceChecker
from itertools import product, chain, combinations, permutations
from functools import reduce
from equivalencecheckers.bruteforce import BFEquivalenceChecker
from learners.learner import Learner
from suls.sul import SUL

from teachers.teacher import Teacher
from typing import Set, Tuple, Optional, Iterable, Callable, List
from tabulate import tabulate

import util.statstracker as stats

from math import ceil, floor

class DTreeNode:
    def __init__(self, isLeaf, dTree, suffix=None, state=None, temporary=False, isRoot=False, id=None):
        self.suffix = suffix
        self.state = state
        self.isLeaf = isLeaf
        self.isTemporary = temporary

        # Child connections
        self.children = {}

        # Parent node
        self.parent: DTreeNode = None

        # The key in the parents children dict pointing to this node
        self.parentLabel = None

        # Keep track of the DTree we belong to and if we're the root node
        self.dTree = dTree
        self.isRoot = isRoot

        if id is None:
            self.id = dTree.getID()
        else:
            self.id = id

    def add(self, value, node):
        self.children[value] = node
        node.parentLabel = value
        node.parent = self

    def replace(self, new):
        assert self.isLeaf, "You sure you want to split a non-leaf node?"

        # Swap out the root in the DTree if necessary
        if self.isRoot:
            self.dTree.root = new
            new.isRoot = True
            self.isRoot = False
        else:
            # Swap out this nodes place in the DTree for the new one
            self.parent.children[self.parentLabel] = new
            new.parent = self.parent
            self.parent = None

    def getAncestors(self):
        ancestors = []
        parent = self.parent
        while parent is not None:
            ancestors.append(parent)
            parent = parent.parent
        return ancestors

    def clone(self):

        new_self = DTreeNode(
            self.isLeaf, self.dTree, self.suffix,
            self.state, self.isTemporary, self.isRoot,
            id=self.id
        )

        # These will be overwritten unless the cloned node is the root of the block
        # new_self.parent = self.parent
        # new_self.parentLabel = self.parentLabel

        for output, child in self.children.items():
            new_child = child.clone()
            new_child.parentLabel = output
            new_child.parent = new_self

            new_self.children[output] = new_child

        # if new_self.parent is None and not new_self.isRoot:
        #     print("is this the root?", self.id)

        return new_self

    def __str__(self):
        return f'[DTreeNode: ({self.state if self.isLeaf else self.suffix})]'


class DTree:
    def __init__(self, initial_state):
        # Dict keeping track of nodes so we can do easy lookups
        # self.nodes = {}
        self.nodes = []

        # Incremental "ID" counter to give ids to nodes
        self.idcounter = 0

        self.root = self.createLeaf(initial_state)
        self.root.isRoot = True

    def getID(self):
        id_ = self.idcounter
        self.idcounter += 1
        return id_

    # After discriminator finalization the reachable nodes may have changed
    # So we need to figure out which ones are still in the tree
    # And assign new IDs to copied nodes
    def refresh_nodes(self):
        to_visit = [self.root]
        visited = []
        seen_IDs = set()

        while len(to_visit) > 0:
            cur_node = to_visit.pop()
            visited.append(cur_node)

            if cur_node.id in seen_IDs:
                cur_node.id = self.getID()
            seen_IDs.add(cur_node.id)

            if not cur_node.isLeaf:
                for next_node in cur_node.children.values():
                    if next_node is not None:
                        to_visit.append(next_node)

        self.nodes = visited

    def createLeaf(self, state):
        node = DTreeNode(True, self, state=state)
        self.nodes.append(node)
        return node

    def createInner(self, suffix, temporary=False):
        node = DTreeNode(False, self, suffix=suffix, temporary=temporary)
        self.nodes.append(node)
        return node

    # Gets the leaf node holding the given state
    def getLeaf(self, state):
        return list(filter(lambda x: x.isLeaf and x.state == state, self.nodes))[0]

    def getLeaves(self):
        return list(filter(lambda x: x.isLeaf, self.nodes))

    # Gets all nodes that are potentially block root nodes
    def getBlockRoots(self):
        roots = list(filter(lambda x: (x.isTemporary
                                       # and not x.isLeaf
                                       and x.parent is not None
                                       and not x.parent.isTemporary)
                                       or (x.isTemporary and x.isRoot)
                                       or (x.isLeaf and not x.parent is None and not x.parent.isTemporary),
                            self.nodes))
        return roots

    def getFinalizedDiscriminators(self):
        return list(filter(lambda x: not x.isTemporary and not x.isLeaf, self.nodes))

    def getLowestCommonAncestor(self, n1, n2):
        n1_ancestors = n1.getAncestors()
        n2_ancestors = n2.getAncestors()

        for i in range(1, max(len(n1_ancestors), len(n2_ancestors)) + 1):
            n1_s = set(n1_ancestors[0:i])
            n2_s = set(n2_ancestors[0:i])
            intersection = n1_s.intersection(n2_s)

            if len(intersection) > 0:
                assert len(intersection) == 1
                return intersection.pop()

    def render_graph(self, filename=None, format='pdf', draw_parent=False):
        if filename is None:
            filename = tempfile.mktemp('.gv')
        g = Digraph('G', filename=filename)
        # g.attr(rankdir='LR')

        # Draw nodes
        for node in self.nodes:
            if not node.isLeaf:
                name = " ".join(node.suffix) if len(node.suffix) > 0 else 'ε'
                name += f" ID:{node.id}"
                if node.isTemporary:
                    g.node(str(id(node)), label=name, style='dotted')
                else:
                    g.node(str(id(node)), label=name)

            else:
                name = node.state.name
                name += f" ID:{node.id}"
                g.node(str(id(node)), label=name, shape='square')

            #Debug parent connections
            if draw_parent and node.parent is not None:
                g.edge(str(id(node)), str(id(node.parent)), label=f'P:{node.parentLabel}')

        # Draw edges
        for node in self.nodes:
            if node.isLeaf:
                continue
            # name = " ".join(node.suffix) if len(node.suffix) > 0 else 'ε'

            for action, next_node in node.children.items():
                # target = next_node.state.name if next_node.isLeaf else " ".join(next_node.suffix)
                g.edge(str(id(node)), str(id(next_node)), label=str(action))
            # if node._true is not None:
            #     target = node._true.state.name if node._true.isLeaf else "".join(node._true.suffix)
            #     g.edge(name, target, label='T')
            # if node._false is not None:
            #     target = node._false.state.name if node._false.isLeaf else "".join(node._false.suffix)
            #     g.edge(name, target, label='F', style='dotted')

        g.render(format=format, view=True)


# A block is a maximal subtree of the discrimination tree
# containing only temporary nodes
class Block:
    def __init__(self, root: DTreeNode):
        self.root: DTreeNode = root

        self.innernodes: List[DTreeNode] = []
        self.leafnodes: List[DTreeNode] = []

        if self.root.isLeaf:
            self.leafnodes.append(self.root)
        else:
            self.innernodes.append(self.root)

        # Keep track of the marks put on nodes by mark and propagate
        self.marks = None

        # BFS to gather temp inner and leaf nodes in subtree
        to_visit = [self.root]
        while len(to_visit) > 0:
            cur = to_visit.pop()
            for child in cur.children.values():
                if child.isTemporary and not child.isLeaf and child not in self.innernodes:
                    self.innernodes.append(child)
                    to_visit.append(child)
                elif child.isLeaf:
                    self.leafnodes.append(child)

    def __str__(self):
        return f"Block [Root: {self.root.suffix}, Nodes: {[y.suffix for y in filter(lambda x: x is not self.root, self.innernodes)]}]"

    def split(self):
        assert self.marks is not None, "Cannot split a non-marked block"

        # We need a subtree for all marks the root has
        root_marks = self.marks[self.root.id]

        subtrees = {}
        for mark in root_marks:
            subtrees[mark] = self.extract_subtree(mark)

        return subtrees

    # Extracts the subtree of all the nodes in the block that are marked with the given output
    def extract_subtree(self, mark):
        print("Extracting subtree for mark", mark)
        # Clone the block
        root = self.root.clone()

        # Strip out all nodes that don't have the mark we want
        to_visit = [root]
        to_collapse = []
        while len(to_visit) > 0:

            cur_node = to_visit.pop()

            # Remove unwanted children (hi dad)
            for out, child in list(cur_node.children.items()):
                child_marks = self.marks[child.id]
                if mark not in child_marks:
                    del cur_node.children[out]
                    child.parent = None
                else:
                    if not child.isLeaf:
                        to_visit.append(child)

            # If an inner node only has one child, we should collapse it
            if len(cur_node.children) == 1 and not cur_node.isLeaf:
                to_collapse.append(cur_node)

        #Collapse nodes that only have one child:
        for cur_node in to_collapse:
            print('collapsing', cur_node.id)
            assert not cur_node.isLeaf

            assert len(list(cur_node.children.items())) == 1

            out, child = list(cur_node.children.items())[0]
            parent = cur_node.parent

            if parent is None:
                assert cur_node is root  # Just checking assumptions
                root = child
                root.parent = None
            else:
                assert cur_node is not root
                parent.children[cur_node.parentLabel] = child
                child.parent = parent
                child.parentLabel = cur_node.parentLabel

            cur_node.children[out] = None
            cur_node.parent = None

        print('root parent is', root.parent.id if root.parent else None)
        return root


    def mark_and_propagate(self, splitter):
        self.marks = {}

        # Get leaf output of splitter
        leaf_outputs = {}
        for leaf in self.leafnodes:
            cur_node = leaf.state
            output = None
            for input in splitter:
                cur_node, output = cur_node.next(input)
            leaf_outputs[leaf] = output

        # Propagate the leaf outputs towards the root of the block
        for leaf, leaf_output in leaf_outputs.items():

            # Collect ancestors up til block root
            to_mark = [leaf]
            cur_node = leaf
            while cur_node is not self.root:
                cur_node = cur_node.parent
                to_mark.append(cur_node)

            # Mark them
            for node in to_mark:
                if node.id in self.marks:
                    self.marks[node.id].add(leaf_output)
                else:
                    self.marks[node.id] = {leaf_output}

        print(self.marks)


    # Checks if this block has a leaf node containing the given state
    def has_leaf(self, state):
        for leafnode in self.leafnodes:
            if leafnode.state == state:
                return True
        return False

    # Get the leaf containing the given state if available, else none
    def get_leaf(self, state):
        for leafnode in self.leafnodes:
            if leafnode.state == state:
                return leafnode
        return None

    # # Finalizes the root of this block and returns a list of 'sub-blocks' (children as root)
    # def finalize_root(self, final_discriminator):
    #     self.root.isTemporary = False
    #     self.root.suffix = final_discriminator
    #     return [Block(child) for child in self.root.children.values()]


from abc import ABC, abstractmethod


# Implements the TTT algorithm
class TTTAbstractLearner(Learner, ABC):
    def __init__(self, teacher: Teacher):
        super().__init__(teacher)
        #
        # # Access sequences S + state bookkeeping
        # self.S = {tuple(): State("s0")}

        # Discrimination tree
        self.DTree = DTree(self.S[tuple()])

        # Query cache
        self.T = {}

        # Alphabet A
        self.A = set([(x,) for x in teacher.get_alphabet()])

        # Add initial state to discrimination tree
        # initial_state = self.S[tuple()]
        # initial_output = self.query(tuple())
        # self.DTree.root.add(initial_output, self.DTree.createLeaf(initial_state))

    # As sifting can create new nodes, we require the concrete learners to implement this method to create the right
    # kind of states
    @abstractmethod
    def sift(self, sequence):
        pass
        # cur_dtree_node = self.DTree.root
        # prev_dtree_node = None
        #
        # while not cur_dtree_node is None and not cur_dtree_node.isLeaf:
        #     # Figure out which branch we should follow
        #     seq = sequence + cur_dtree_node.suffix
        #     response = self.query(seq)
        #     prev_dtree_node = cur_dtree_node
        #     if response in cur_dtree_node.children:
        #         cur_dtree_node = cur_dtree_node.children[response]
        #     else:
        #         cur_dtree_node = None
        #
        # # If we end up on an empty node, we can add a new leaf pointing to the
        # # state accessed by the given sequence
        # if cur_dtree_node is None:
        #     new_acc_seq = sequence
        #     new_state = State(f's{len(self.S)}')
        #     new_dtree_node = self.DTree.createLeaf(new_state)
        #     self.S[new_acc_seq] = new_state
        #     prev_dtree_node.add(response, new_dtree_node)
        #     cur_dtree_node = new_dtree_node
        #
        # assert cur_dtree_node is not None, "Oof this shouldn't happen"
        # assert cur_dtree_node.isLeaf, "This should always be a leaf node"
        # assert cur_dtree_node.state is not None, "Leaf nodes should always represent a state"
        #
        # return cur_dtree_node.state

    @abstractmethod
    def construct_hypothesis(self):
        pass
        # # Keep track of the initial state
        # initial_state = self.S[()]
        #
        # # Keep track of the amount of states, so we can sift again if
        # # the sifting process created a new state
        # n = len(list(self.S.items()))
        # items_added = True
        #
        # # Todo: figure out a neater way to handle missing states during sifting than to just redo the whole thing
        # while items_added:
        #     # Add transitions
        #     for access_seq, cur_state in list(self.S.items()):
        #         for a in self.A:
        #             next_state = self.sift(access_seq + a)
        #             output = self.query(access_seq + a)
        #             cur_state.add_edge(a[0], output, next_state, override=True)
        #
        #     # Check if no new state was added
        #     n2 = len((self.S.items()))
        #
        #     items_added = n != n2
        #     # print("items added", items_added)
        #
        #     n = n2
        #
        # # Find accepting states
        # # accepting_states = [state for access_seq, state in self.S.items() if self.query(access_seq)]
        #
        # return MealyMachine(initial_state)

    def refine_hypothesis(self, hyp):
        # Attempt to find a counterexample:
        equivalent, counterexample = self.teacher.equivalence_query(hyp)

        if equivalent:
            return True, hyp

        self.process_counterexample(counterexample)

        # self.DTree.render_graph()

        # Todo: neatly update the hypothesis instead of rebuilding it from scratch
        return False, self.construct_hypothesis()

    # TO DEBUG
    # def check_dtree(self):
    #     all_states = self.S.values()
    #     reachable_states = []
    #
    #     # Walk the DTREE to check what states are not broken
    #     to_visit = [self.DTree.root]
    #     visited = []
    #
    #     while len(to_visit) > 0:

    # Decomposes the given counterexample, and updates the hypothesis
    # and discrimination tree accordingly
    @abstractmethod
    def process_counterexample(self, counterexample):
        pass
        # u, a, v = self.decompose(counterexample)
        #
        # # This state q_old needs to be split:
        # q_old_state = self.get_state_from_sequence(u + a)
        # q_old_acc_seq = self.get_access_sequence_from_state(q_old_state)
        #
        # # Store new state and access sequence
        # q_new_acc_seq = self.get_access_sequence(u) + a
        # q_new_state = State(f's{len(self.S)}')
        #
        # assert q_new_acc_seq not in self.S
        #
        # self.S[q_new_acc_seq] = q_new_state
        #
        # ### update the DTree:
        # # find the leaf corresponding to the state q_old
        # q_old_leaf = self.DTree.getLeaf(q_old_state)
        # # and create a new inner node,
        # new_inner = self.DTree.createInner(v, temporary=True)
        #
        # # replace the old leaf node with the new inner node
        # q_old_leaf.replace(new_inner)
        #
        # # check what branch the children should go
        # response_q_old = self.query(q_old_acc_seq + v)
        # response_q_new = self.query(q_new_acc_seq + v)
        # # response_q_old = self.query(u + v)
        # # response_q_new = self.query(q_new_acc_seq + v)
        # assert response_q_new != response_q_old, "uh oh this should never happen"
        #
        # # prepare leaf node for the new state
        # q_new_leaf = self.DTree.createLeaf(q_new_state)
        #
        # # Add the children to the corresponding branch of the new inner node
        # new_inner.add(response_q_new, q_new_leaf)
        # new_inner.add(response_q_old, q_old_leaf)
        #
        # print("splitty boi", q_old_state.name, q_new_state.name)
        # #
        # # if response_q_new == True:
        # #     new_inner.addTrue(q_new_leaf)
        # #     new_inner.addFalse(q_old_leaf)
        # # else:
        # #     new_inner.addTrue(q_old_leaf)
        # #     new_inner.addFalse(q_new_leaf)

    def decompose(self, sequence):
        if len(sequence) == 1:
            return tuple(), sequence, tuple()

        for i in range(len(sequence)):
            u = sequence[:i]
            a = (sequence[i],)
            v = sequence[i + 1:]

            # print('u', u)
            # print('a', a)
            # print('v', v)

            q1 = self.query(self.get_access_sequence(u) + a + v)
            q2 = self.query(self.get_access_sequence(u + a) + v)

            if q1 != q2:
                print('decomposition:')
                print(u)
                print(a)
                print(v)
                return u, a, v

        assert False, f'Failed to decompose counterexample: {sequence}'

    def decompose_broken(self, sequence):
        if len(sequence) == 1:
            return tuple(), sequence, tuple()

        if len(sequence) == 2:
            return self.decompose_slow(sequence)

        # L = 0
        # R = len(sequence) - 1
        #
        # while L != R:
        #     m = ceil((L + R) / 2)
        #
        #     u = sequence[:m]
        #     a = (sequence[m],)
        #     v = sequence[m + 1:]
        #
        #     q1 = self.query(self.get_access_sequence(u) + a + v)
        #     q2 = self.query(self.get_access_sequence(u + a) + v)
        #
        #     if q1 == q2:
        #         L = m
        #     else:
        #         R = m - 1
        #
        #     assert L <= R,  f'Failed to decompose counterexample: {sequence}'

        L = 0
        R = len(sequence)

        # def A(m):
        #     u = sequence[:m]
        #     a = (sequence[m],)
        #     v = sequence[m + 1:]
        #
        #     q1 = self.query(self.get_access_sequence(u) + a + v)
        #     q2 = self.query(self.get_access_sequence(u + a) + v)
        #
        #     return q1 == q2
        def pi(w, i):
            return self.get_access_sequence(w[0:i]) + w[i:]

        hyp = self.construct_hypothesis()
        def A(i):
            return 1 if self.query(pi(sequence, i)) == hyp.process_input(sequence) else 0

        while R - L > 1:

            m = floor((L + R) / 2)

            if A(m) == 0:
                L = m
            else:
                R = m

            assert L <= R, f'Failed to decompose counterexample: {sequence}'

        m = L
        u = sequence[:m]
        a = (sequence[m],)
        v = sequence[m + 1:]

        print('decomposition:')
        print(u)
        print(a)
        print(v)

        q1 = self.query(self.get_access_sequence(u) + a + v)
        q2 = self.query(self.get_access_sequence(u + a) + v)

        if q1 == q2:
            print('q1', q1, 'q2', q2)


        # print("slow decomposition")
        # if (u, a, v) != self.decompose_slow(sequence):
        #     L = 0
        #     R = len(sequence) - 1
        #
        #     while R != L:  # R - L > 1:
        #
        #         m = floor((L + R) / 2)
        #         # m = (R - L) // 2 + L
        #
        #         q1, q2 = run_split(m)
        #         # q3, q4 = run_split(m + 1)
        #
        #         if q1 == q2:  # and q3 != q4:
        #             L = m + 1
        #         else:
        #             R = m
        #
        #         assert L <= R, f'Failed to decompose counterexample: {sequence}'

        return u, a, v

    def get_access_sequence(self, sequence):
        # find what state we end up in by following the sequence
        state = self.get_state_from_sequence(sequence)

        return self.get_access_sequence_from_state(state)

    def get_state_from_sequence(self, sequence):
        state = self.S[()]
        for action in sequence:
            state = state.next_state(action)
        return state

    def get_access_sequence_from_state(self, state):
        for acc_seq, s in self.S.items():
            if s == state:
                return acc_seq

        assert False
        # LOOL BFS IS WRONG BOI wait is it tho?
        # BFS to find state
        visited = set()
        to_visit = [(tuple(), self.S[()])]

        while len(to_visit) > 0:
            cur_seq, cur_state = to_visit.pop()
            visited.add(cur_state)

            # Did we find the state yet?
            if cur_state == state:
                return cur_seq

            # If not keep searching
            for a in self.A:
                next_state = cur_state.next_state(a[0])
                if next_state not in visited:
                    to_visit.append((cur_seq + a, cur_state.next_state(a[0])))

    def stabilize_hypothesis(self, hyp):
        # To stabilize the hypothesis, we check if it matches the information in the discrimination tree
        # accepting = self.DTree.getAccepting()
        # rejecting = self.DTree.getRejecting()
        # leaves = [(True, x) for x in accepting] + [(False, x) for x in rejecting]

        stable = False
        while not stable:
            stable, counterexample = self.find_internal_counterexample(hyp)
            # print("Stable:", stable, "Counterexample:", counterexample)
            if stable:
                break

            self.process_counterexample(counterexample)

            hyp = self.construct_hypothesis()

        # hyp.render_graph(tempfile.mktemp('.gv'))
        return hyp

    def find_internal_counterexample(self, hyp):
        for acc_seq, state in self.S.items():
            # find this state in the DTree
            leaf: DTreeNode = self.DTree.getLeaf(state)
            # leaf: DTreeNode = self.DTree.nodes[state]

            # leaf "output"
            leaf_output = leaf.parentLabel

            # what is the distinguishing sequence?
            dist_seq = tuple() if leaf.isRoot else leaf.parent.suffix

            # hypothesis output
            hyp.reset()
            hyp_output = hyp.process_input(acc_seq + dist_seq)

            if hyp_output != leaf_output:
                print("Internal counterexample:", acc_seq, dist_seq, hyp_output, leaf.state.name, leaf_output)
                return False, acc_seq + dist_seq

        return True, None

    def finalize_discriminators(self):
        print('Start discriminator finalization')
        could_still_finalize = True

        while could_still_finalize:
            could_still_finalize = False

            # Gather blocks to finalize (maximal subtrees of temporary discriminators)
            blocks = deque()
            for block in [Block(root) for root in self.DTree.getBlockRoots() if not root.isLeaf]:
                blocks.append(block)

            while len(blocks) > 0:
                cur_block: Block = blocks.pop()

                # If it's a leaf, we're done here
                if cur_block.root.isLeaf:
                    continue

                # Trivial case (suffix is already length 1, just mark the root as finalized):
                if len(cur_block.root.suffix) == 1:
                    cur_block.root.isTemporary = False
                    blocks.extend([Block(child) for child in cur_block.root.children.values()])
                    could_still_finalize = True
                    continue

                # Attempt to find a splitter
                splitter = None

                # Gather all current blocks for lookup purposes
                cur_blocks = [Block(root) for root in self.DTree.getBlockRoots()]

                # See if two states in the block can be separated output-wise or state-wise
                for (x, y) in combinations(cur_block.leafnodes, r=2):
                    for a in self.A:
                        x_next, x_output = x.state.next(a[0])
                        y_next, y_output = y.state.next(a[0])

                        # Output wise?
                        if x_output != y_output:
                            splitter = a
                            print(f"Output wise ({x.state.name}, {y.state.name}) -> ({x_output}, {y_output})")
                            break

                        #State wise?
                        x_blk, x_leaf = None, None
                        y_blk, y_leaf = None, None
                        for blk in cur_blocks:
                            if blk.has_leaf(x_next):
                                x_blk = blk
                            if blk.has_leaf(y_next):
                                y_blk = blk
                            if x_blk is not None and y_blk is not None:# and x_blk != y_blk:
                                break

                        if x_blk is not None and y_blk is not None and x_blk != y_blk:

                            x_leaf = x_blk.get_leaf(x_next)
                            y_leaf = y_blk.get_leaf(y_next)

                            lca = self.DTree.getLowestCommonAncestor(x_leaf, y_leaf)

                            splitter = a + lca.suffix
                            print(f"State wise ({x.state.name}, {y.state.name}) -> ({x_next.name}, {y_next.name})")
                            break

                    if splitter is not None:
                        break

                if splitter is None:
                    continue

                print("Splitter found!", splitter, "for block root ID:", cur_block.root.id)

                # now that we have a splitter, we can perform a split! yay!
                # first, we need to mark the block
                cur_block.mark_and_propagate(splitter)

                # now, we can extract subtrees
                subtrees = cur_block.split()

                # yeet the new info in the block root and mark it as final!
                cur_block.root.isTemporary = False
                cur_block.root.suffix = splitter
                cur_block.root.children = subtrees

                for connection, child in cur_block.root.children.items():
                    child.parent = cur_block.root
                    child.parentLabel = connection

                # refresh the DTree so it can update it's bookkeeping
                self.DTree.refresh_nodes()

                self.allstatesunique()

                # "Close transitions"
                # Need to do this so the hypothesis stays in sync with the DTree
                self.construct_hypothesis()

                could_still_finalize = True


    def does_split(self, S_inv, discriminator, n1, n2):
        s1_acc_seq = S_inv[n1.state]
        s2_acc_seq = S_inv[n2.state]

        n1_out = self.query(s1_acc_seq + discriminator)
        n2_out = self.query(s2_acc_seq + discriminator)

        return n1_out != n2_out, n1_out, n2_out

    # Membership query
    def query(self, query):
        #return self.teacher.member_query(query)
        # print("Query:", query)
        if query in self.T.keys():
            # print("Returning cached")
            return self.T[query]
        else:
            accepted = self.teacher.member_query(query)
            self.T[query] = accepted
            return accepted

    # Utility method to convert a tuple to a comma separated list
    def _tostr(self, actionlist):
        if len(actionlist) == 0:
            return 'λ'
        else:
            return reduce(lambda x, y: str(x) + ',' + str(y), actionlist)

    # Utility method to construct a tuple from a comma separated list
    def _rebuildquery(self, strquery):
        return tuple(filter(lambda x: x != 'λ', strquery.split(',')))

    # Debug help
    def allstatesunique(self):
        state_names = set()
        for s in self.S.values():
            state_names.add(s)

        assert len(self.S) == len(state_names), "S not unique"

        leaf_states = []
        for leaf in self.DTree.getLeaves():
            leaf_states.append(leaf.state.name)

        assert len(leaf_states) == len(set(leaf_states)), f'Duplicate leaf :( {set([x for x in leaf_states if leaf_states.count(x) > 1])}'

    def step(self):

        self.allstatesunique()

        hyp = self.construct_hypothesis()

        # hyp.render_graph('ttt_hyp_initial', format='png')
        # self.DTree.render_graph('ttt_dtree_initial', format='png')

        self.allstatesunique()

        done, hyp = self.refine_hypothesis(hyp)

        # hyp.render_graph('ttt_hyp_step2', format='png')
        # self.DTree.render_graph('ttt_dtree_step2', format='png')

        self.allstatesunique()

        hyp = self.stabilize_hypothesis(hyp)

        # hyp.render_graph('ttt_hyp_step3', format='png')
        # self.DTree.render_graph('ttt_dtree_step3', format='png')

        self.allstatesunique()

        #self.DTree.render_graph('ttt_dtree_before')
        #self.finalize_discriminators()
        #self.DTree.render_graph('ttt_dtree_after')
        # self.DTree.render_graph('ttt_dtree_finalized', format='png')

        print("Done:", done)
        if done:
            return done, hyp

        return done, hyp

    def run(self, show_intermediate=False, render_options=None,
            on_hypothesis=None):
        done = False
        hyp = None

        while not done:
            done, hyp = self.step()

            stats.count_hypothesis_stats(hyp)

            if on_hypothesis is not None:
                on_hypothesis(hyp)

            if show_intermediate and not done:
                hyp.render_graph(render_options=render_options)

        return hyp

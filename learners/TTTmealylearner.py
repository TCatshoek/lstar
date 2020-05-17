import tempfile
from queue import Queue

from graphviz import Digraph

from equivalencecheckers.equivalencechecker import EquivalenceChecker
from suls.mealymachine import MealyMachine, MealyState as State
from itertools import product, chain, combinations, permutations
from functools import reduce
from equivalencecheckers.bruteforce import BFEquivalenceChecker
from learners.learner import Learner
from suls.sul import SUL

from teachers.teacher import Teacher
from typing import Set, Tuple, Optional, Iterable, Callable
from tabulate import tabulate


class DTreeNode:
    def __init__(self, isLeaf, dTree, suffix=None, state=None, temporary=False, isRoot=False):
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

    def __str__(self):
        return f'[DTreeNode: ({self.state if self.isLeaf else self.suffix})]'


class DTree:
    def __init__(self, initial_state):
        # Dict keeping track of nodes so we can do easy lookups
        #self.nodes = {}
        self.nodes = []

        self.root = self.createLeaf(initial_state)
        self.root.isRoot = True

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

    # Gets all nodes that are potentially block root nodes
    def getBlockRoots(self):
        roots = list(filter(lambda x: x.isTemporary
                                      and not x.isLeaf
                                      and x.parent is not None
                                      and not x.parent.isTemporary,
                            self.nodes))
        return roots

    def getFinalizedDiscriminators(self):
        return list(filter(lambda x: not x.isTemporary and not x.isLeaf, self.nodes))

    def getLowestCommonAncestor(self, n1, n2):
        n1_ancestors = n1.getAncestors()
        n2_ancestors = n2.getAncestors()

        for i in range(1, min(len(n1_ancestors), len(n2_ancestors)) + 1):
            n1_s = set(n1_ancestors[0:i])
            n2_s = set(n2_ancestors[0:i])
            intersection = n1_s.intersection(n2_s)

            if len(intersection) > 0:
                assert len(intersection) == 1
                return intersection.pop()

    def render_graph(self, filename=None):
        if filename is None:
            filename = tempfile.mktemp('.gv')
        g = Digraph('G', filename=filename)
        # g.attr(rankdir='LR')

        # Draw nodes
        for node in self.nodes:
            if not node.isLeaf:
                name = " ".join(node.suffix) if len(node.suffix) > 0 else 'ε'
                if node.isTemporary:
                    g.node(str(id(node)), label=name, style='dotted')
                else:
                    g.node(str(id(node)), label=name)

            else:
                g.node(str(id(node)), label=node.state.name, shape='square')
            # Debug parent connections
            if node.parent is not None:
                g.edge(str(id(node)), str(id(node.parent)), label='P')

        # Draw edges
        for node in self.nodes:
            if node.isLeaf:
                continue
            #name = " ".join(node.suffix) if len(node.suffix) > 0 else 'ε'

            for action, next_node in node.children.items():
                #target = next_node.state.name if next_node.isLeaf else " ".join(next_node.suffix)
                g.edge(str(id(node)), str(id(next_node)), label=str(action))
            # if node._true is not None:
            #     target = node._true.state.name if node._true.isLeaf else "".join(node._true.suffix)
            #     g.edge(name, target, label='T')
            # if node._false is not None:
            #     target = node._false.state.name if node._false.isLeaf else "".join(node._false.suffix)
            #     g.edge(name, target, label='F', style='dotted')

        g.view()


# A block is a maximal subtree of the discrimination tree
# containing only temporary nodes
class Block:
    def __init__(self, root: DTreeNode):
        self.root = root

        self.innernodes = [self.root]
        self.leafnodes = []
        # BFS to gather temp inner and leaf nodes in subtree
        to_visit = [self.root]
        while len(to_visit) > 0:
            cur = to_visit.pop()
            for child in [cur._true, cur._false]:
                if child.isTemporary and not child.isLeaf and child not in self.innernodes:
                    self.innernodes.append(child)
                    to_visit.append(child)
                elif child.isLeaf:
                    self.leafnodes.append(child)

    def __str__(self):
        return f"Block [Root: {self.root.suffix}, Nodes: {[y.suffix for y in filter(lambda x: x is not self.root, self.innernodes)]}]"

    def split(self, final_discriminators, alphabet):
        # Grab the root and find a replacement by prepending a character from the alphabet
        # to an existing finalized discriminator

        # Find the shortest one that works
        # A discriminator works if it splits at least two states in the block
        best_len = None
        # for cur_disc in potential_discriminators:


# Implements the TTT algorithm
class TTTMealyLearner(Learner):
    def __init__(self, teacher: Teacher):
        super().__init__(teacher)

        # Access sequences S + state bookkeeping
        self.S = {tuple(): State("s0")}

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
                    cur_state.add_edge(a[0], output, next_state, override=True)

            # Check if no new state was added
            n2 = len((self.S.items()))

            items_added = n != n2
            # print("items added", items_added)

            n = n2

        # Find accepting states
        accepting_states = [state for access_seq, state in self.S.items() if self.query(access_seq)]

        return MealyMachine(initial_state)

    def refine_hypothesis(self, hyp):
        # Attempt to find a counterexample:
        equivalent, counterexample = self.teacher.equivalence_query(hyp)

        if equivalent:
            return True, hyp

        self.process_counterexample(counterexample)

        #self.DTree.render_graph()

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
    def process_counterexample(self, counterexample):
        u, a, v = self.decompose(counterexample)

        # This state q_old needs to be split:
        q_old_state = self.get_state_from_sequence(u + a)
        q_old_acc_seq = self.get_access_sequence_from_state(q_old_state)

        # Store new state and access sequence
        q_new_acc_seq = self.get_access_sequence(u) + a
        q_new_state = State(f's{len(self.S)}')
        self.S[q_new_acc_seq] = q_new_state

        ### update the DTree:
        # find the leaf corresponding to the state q_old
        q_old_leaf = self.DTree.getLeaf(q_old_state)
        # and create a new inner node,
        new_inner = self.DTree.createInner(v, temporary=True)

        # replace the old leaf node with the new inner node
        q_old_leaf.replace(new_inner)

        # check what branch the children should go
        #TODO: Is this fucked??
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
        #
        # if response_q_new == True:
        #     new_inner.addTrue(q_new_leaf)
        #     new_inner.addFalse(q_old_leaf)
        # else:
        #     new_inner.addTrue(q_old_leaf)
        #     new_inner.addFalse(q_new_leaf)

    def decompose(self, sequence):
        if len(sequence) == 1:
            return tuple(), sequence, tuple()

        for i in range(len(sequence)):
            u = sequence[:i]
            a = (sequence[i],)
            v = sequence[i + 1:]

            print('u', u)
            print('a', a)
            print('v', v)

            q1 = self.query(self.get_access_sequence(u) + a + v)
            q2 = self.query(self.get_access_sequence(u + a) + v)

            print('q1:', q1)
            print('q2:', q2)
            print()
            if q1 != q2:
                return u, a, v

        # TODO FIX INTERNAL COUNTEREXAMPLES THEY MESS EVERYTHING UP
        assert False, 'Failed to decompose counterexample'

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
        # LOOL BFS IS WRONG BOI
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

    def stabilize_hypothesis(self, hyp: MealyMachine):
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
            #leaf: DTreeNode = self.DTree.nodes[state]

            # leaf "output"
            leaf_output = leaf.parentLabel

            # what is the distinguishing sequence?
            dist_seq = leaf.parent.suffix

            # hypothesis output
            hyp.reset()
            hyp_output = hyp.process_input(acc_seq + dist_seq)

            if hyp_output != leaf_output:
                #print("Internal counterexample:", acc_seq + dist_seq, hyp_output, leaf_output)
                return False, acc_seq + dist_seq

        return True, None

    def finalize_discriminators(self):
        # Gather blocks (maximal subtrees of temporary discriminators)
        blocks = Queue()
        for block in [Block(root) for root in self.DTree.getBlockRoots()]:
            blocks.put(block)

        # Gather current final discriminators
        final_discriminators = [x.suffix for x in self.DTree.getFinalizedDiscriminators()]

        # Build index to find access sequences of states
        S_inv = {}
        for k, v in self.S.items():
            S_inv[v] = k

        while not blocks.empty():
            best_len = None
            best_disc = None
            discriminated_nodes = None

            # keep track of all pairs of nodes' lowest common discriminator
            # to aid in rebuilding the tree after replacing the root
            lcdiscs = {}

            cur_block: Block = blocks.get()
            cur_leaves = cur_block.leafnodes

            leaf_combinations = permutations(cur_leaves, r=2)

            # Find the best new discriminator (currently just the shortest correct one):
            for prefix, final_discriminator in product(self.A, final_discriminators):
                new_discriminator = prefix + final_discriminator

                for n1, n2 in leaf_combinations:

                    # also keep track of the lcds
                    lcdiscs[(n1, n2)] = self.DTree.getLowestCommonAncestor(n1, n2)

                    does_split, n1_out, n2_out = self.does_split(S_inv, new_discriminator, n1, n2)
                    if does_split:
                        if best_len is None or len(new_discriminator) < best_len:
                            best_len = len(new_discriminator)
                            best_disc = new_discriminator
                            discriminated_nodes = (n1, n2)

            # Prepare splitting the block by
            cur_block.root.suffix = best_disc
            cur_block.root.isTemporary = False

        # At the root of a block, replace the root discriminator with a new final discriminator
        # which is made by taking an existing final discriminator and prepending a character
        # from the alphabet
        pass

    def does_split(self, S_inv, discriminator, n1, n2):
        s1_acc_seq = S_inv[n1.state]
        s2_acc_seq = S_inv[n2.state]

        n1_out = self.query(s1_acc_seq + discriminator)
        n2_out = self.query(s2_acc_seq + discriminator)

        return n1_out != n2_out, n1_out, n2_out

    # Membership query
    def query(self, query):
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

    def step(self):
        hyp = self.construct_hypothesis()

        # hyp.render_graph()
        # self.DTree.render_graph()

        done, hyp = self.refine_hypothesis(hyp)

        # hyp.render_graph()
        # self.DTree.render_graph()

        print("Done:", done)
        if done:
            return done, hyp

        hyp = self.stabilize_hypothesis(hyp)

        # hyp.render_graph()
        # self.DTree.render_graph()

        # TODO
        # hyp = self.finalize_discriminators()

        return done, hyp

    def run(self, show_intermediate=False, render_options=None, on_hypothesis: Callable[[MealyMachine], None] = None) -> MealyMachine:
        done = False
        hyp = None

        while not done:
            done, hyp = self.step()

            if on_hypothesis is not None:
                on_hypothesis(hyp)

            if show_intermediate and not done:
                hyp.render_graph(render_options=render_options)

        return hyp


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
    s1 = State('1')
    s2 = State('2')
    s3 = State('3')

    s1.add_edge('a', 'nice', s2)
    s1.add_edge('b', 'B', s1)
    s2.add_edge('a', 'nice', s3)
    s2.add_edge('b', 'back lol', s1)
    s3.add_edge('a', 'A', s3)
    s3.add_edge('b', 'B', s1)

    mm = MealyMachine(s1)
    mm.render_graph()

    eqc = BFEquivalenceChecker(mm)

    teacher = Teacher(mm, eqc)

    learner = TTTMealyLearner(teacher)

    done = False
    while not done:
        # Get the learners hypothesis
        hyp = learner.construct_hypothesis()
        # hyp.render_graph(tempfile.mktemp('.gv'))

        done, hyp = learner.refine_hypothesis(hyp)
        print("Done:", done)
        # hyp.render_graph(tempfile.mktemp('.gv'))
        #
        hyp = learner.stabilize_hypothesis(hyp)
        hyp.render_graph(tempfile.mktemp('.gv'))
    #
    # hyp = learner.finalize_discriminators()
    #
    learner.DTree.render_graph(tempfile.mktemp('.gv'))

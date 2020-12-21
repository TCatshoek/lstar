
# Need this to fix types
from __future__ import annotations

import tempfile
import threading
from typing import Union, Iterable, Dict, Tuple
from suls.sul import SUL

from graphviz import Digraph

import random
from itertools import product

class MealyState:
    def __init__(self, name: str, edges: Dict[str, Tuple[MealyState, str]] = None):
        if edges is None:
            edges = {}

        self.name = name
        self.edges = edges

    def __str__(self):
        return f'[MealyState: {self.name}, edges: {[f"{a}/{o}:{n.name}" for a, (n, o) in self.edges.items()]}]'

    def add_edge(self, action: str, output: str, other_state: MealyState, override=False):
        if override:
            self.edges[action] = (other_state, output)
        else:
            if action not in self.edges.keys():
                self.edges[action] = (other_state, output)
            else:
                raise Exception(f'{action} already defined in state {self.name}')

    def next(self, action) -> Tuple[MealyState, str]:
        if action in self.edges.keys():
            return self.edges.get(action)
        else:
            raise Exception(f'Invalid action {action} from state {self.name}')

    def next_state(self, action) -> MealyState:
        if action in self.edges.keys():
            return self.edges.get(action)[0]
        else:
            raise Exception(f'Invalid action {action} from state {self.name}')


# A statemachine can represent a system under learning
class MealyMachine(SUL):
    def __init__(self, initial_state: MealyState):
        self.initial_state = initial_state
        self.state: MealyState = initial_state

    def __str__(self):
        states = self.get_states()

        #Hacky backslash thing
        tab = '\t'
        nl = '\n'
        return f'[MealyMachine: \n { nl.join([f"{tab}{str(state)}" for state in states]) } ' \
               f'\n\n\t[Initial state: {self.initial_state.name}]' \
               f'\n]'

    # Performs a bfs to gather all reachable states
    def get_states(self):
        to_visit = [self.initial_state]
        visited = []

        while len(to_visit) > 0:
            cur_state = to_visit.pop()
            if cur_state not in visited:
                visited.append(cur_state)

            for action, (other_state, output) in cur_state.edges.items():
                if other_state not in visited and other_state not in to_visit:
                    to_visit.append(other_state)

        return visited

    # Traverses all states and collects all possible actions (i.e. the alphabet of the language)
    def get_alphabet(self):
        states = self.get_states()
        actions = set()

        for state in states:
            actions = actions.union(set(state.edges.keys()))

        #print(actions)

        return actions

    # Runs the given inputs on the state machine
    def process_input(self, inputs):
        last_output = None

        if not isinstance(inputs, Iterable):
            inputs = [inputs]

        for input in inputs:
            try:
                nextstate, output = self.state.next(input)
                #print(f'({self.state.name}) ={input}=> ({nextstate.name})')
                self.state = nextstate
                last_output = output
            except Exception as e:
                #print(e)
                return "invalid_input"

        return last_output

    def reset(self):
        self.state = self.initial_state

    def render_graph(self, filename=None, format='pdf', render_options=None):

        def render(filename, render_options):
            if filename is None:
                filename = tempfile.mktemp('.gv')
            if render_options is None:
                render_options = {}

            # Extract color options if present
            node_color = {}
            if 'node_attributes' in render_options:
                for state, attributes in render_options['node_attributes'].items():
                    if 'color' in attributes:
                        node_color[state] = attributes['color']

            g = Digraph('G', filename=filename)
            g.attr(rankdir='LR')

            # Collect nodes and edges
            to_visit = [self.initial_state]
            visited = []

            # Hacky way to draw start arrow pointing to first node
            g.attr('node', shape='none')
            g.node('startz', label='', _attributes={'height': '0', 'width': '0'})

            # Draw initial state
            g.attr('node', shape='circle')

            if self.initial_state in node_color:
                g.node(self.initial_state.name, color=node_color[self.initial_state], style='filled')
            else:
                g.node(self.initial_state.name)

            g.edge('startz', self.initial_state.name)

            while len(to_visit) > 0:
                cur_state = to_visit.pop()
                visited.append(cur_state)

                g.attr('node', shape='circle')
                for action, (other_state, output) in cur_state.edges.items():
                    # Draw other states, but only once
                    if other_state not in visited and other_state not in to_visit:
                        to_visit.append(other_state)
                        if other_state in node_color:
                            g.node(other_state.name, color=node_color[other_state], style='filled')
                        else:
                            g.node(other_state.name)


                    # Draw edges too
                    ignore_self_edges = []
                    ignore_edges = []

                    if 'ignore_self_edges' in render_options:
                        ignore_self_edges = render_options['ignore_self_edges']
                    if 'ignore_edges' in render_options:
                        ignore_edges = render_options['ignore_edges']

                    if (not (any([output.startswith(x) for x in ignore_self_edges]) and other_state == cur_state)) \
                            and not(any([output.startswith(x) for x in ignore_edges])):
                        g.edge(cur_state.name, other_state.name, label=f'{action}/{output}')

            if format != None:
                g.render(format=format, view=True)
            else:
                g.save()


        renderthread = threading.Thread(target=render, args=(filename, render_options))
        renderthread.start()


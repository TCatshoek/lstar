# Need this to fix types
from __future__ import annotations
from typing import Union, Iterable
from suls.sul import SUL

class State:
    def __init__(self, name: str, edges=None):
        if edges is None:
            edges = {}

        self.name = name
        self.edges = edges

    def __str__(self):
        return f'[State: {self.name}, edges: {[f"{a}:{n.name}" for a, n in self.edges.items()]}]'

    def add_edge(self, action: str, other_state: State):
        if action not in self.edges.keys():
            self.edges[action] = other_state
        else:
            raise Exception(f'{action} already defined in state {self.name}')

    def next(self, action):
        if action in self.edges.keys():
            return self.edges.get(action)
        else:
            raise Exception(f'Invalid action {action} from state {self.name}')


# A statemachine can represent a system under learning
class StateMachine(SUL):
    def __init__(self, initial_state: State, accepting_states: Union[State, Iterable[State]]):
        self.initial_state = initial_state
        self.state = initial_state

        if not isinstance(accepting_states, Iterable):
            accepting_states = [accepting_states]
        self.accepting_states = accepting_states

    def __str__(self):
        to_visit = [self.initial_state]
        visited = []

        while len(to_visit) > 0:
            cur_state = to_visit.pop()
            if cur_state not in visited:
                visited.append(cur_state)

            for action, other_state in cur_state.edges.items():
                if other_state not in visited:
                    to_visit.append(other_state)

        #Hacky backslash thing
        tab = '\t'
        nl = '\n'
        return f'[StateMachine: \n { nl.join([f"{tab}{str(state)}" for state in visited]) } ' \
               f'\n\n\t[Initial state: {self.initial_state.name}]' \
               f'\n\t[Accepting states: {[s.name for s in self.accepting_states]}]' \
               f'\n]'

    # Traverses all states and collects all possible actions (i.e. the alphabet of the language)
    def get_alphabet(self):
        actions = []
        to_visit = [self.initial_state]
        visited = []

        while len(to_visit) > 0:
            cur_state = to_visit.pop()
            visited.append(cur_state)

            for action, other_state in cur_state.edges.items():
                actions.append(action)
                if other_state not in visited:
                    to_visit.append(other_state)

        return set(actions)

    # Runs the given inputs on the state machine
    def process_input(self, inputs):
        if not isinstance(inputs, Iterable):
            inputs = [inputs]

        for input in inputs:
            try:
                nextstate = self.state.next(input)
                #print(f'({self.state.name}) ={input}=> ({nextstate.name})')
                self.state = nextstate
            except Exception as e:
                #print(e)
                return False

        return self.state in self.accepting_states

    def reset(self):
        self.state = self.initial_state
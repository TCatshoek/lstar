from collections.abc import Iterable

class State:
    def __init__(self, name, edges=None):
        if edges is None:
            edges = {}

        self.name = name
        self.edges = edges

    def add_edge(self, action, other_state):
        if action not in self.edges.keys():
            self.edges[action] = other_state
        else:
            raise Exception(f'{action} already defined in state {self.name}')

    def next(self, action):
        if action in self.edges.keys():
            return self.edges.get(action)
        else:
            raise Exception(f'Invalid action {action} from state {self.name}')

class StateMachine:
    def __init__(self, initial_state):
        self.state = initial_state

    def process_input(self, inputs):
        if not isinstance(inputs, Iterable):
            inputs = [inputs]

        for input in inputs:
            nextstate = self.state.next(input)
            print(f'({self.state.name}) ={input}=> ({nextstate.name})')
            self.state = nextstate

s1 = State(1)
s2 = State(2)
s1.add_edge('to2', s2)
s2.add_edge('to1', s1)

sm = StateMachine(s1)

try:
    sm.process_input(['to2', 'to1', 'to2', 'to2'])
except Exception as e:
    print(e)
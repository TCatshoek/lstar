from suls.mealymachine import MealyMachine, MealyState


# Saves the given mealy machine to the specified path, in mcrl2 format
# this uses alternating semantics, e.g. every transition introduces an extra state
# which emits the output from the original mealy machine:
# (s1) --a/1--> (s2) becomes (s1) --a--> (o1) --1--> (s2)
def mealy2mcrl2(fsm: MealyMachine, path):

    states = fsm.get_states()

    # Collect the actions performed to put into the act section of the mcrl2 file
    acts = set()

    # Collect the lines to go in the proc section of the mcrl2 file
    proc_lines = []

    # We also need the initial state, for the init line in the mcrl2 file
    init_line = f'init {fsm.initial_state.name};'

    for state in states:
        # Build the line for this state
        state_line = f'{state.name} = '
        first = True

        intermediate_lines = []

        for action, (next_state, output) in state.edges.items():
            # Keep track of actions
            acts.add(action)
            acts.add(output)

            # Transitions to intermediate state
            intermediate_state_name = f'o_{state.name}_{output}'
            state_line += f'{" + " if not first else ""}{action}.{intermediate_state_name}'

            # Transitions from intermediate state to actual next state
            intermediate_lines.append(f'\t{intermediate_state_name} = {output}.{next_state.name};')

            first = False

        if len(state.edges) == 0:
            state_line += 'delta'

        state_line += ';'

        proc_lines.append(state_line)
        proc_lines += intermediate_lines

    with open(path, 'w') as file:
        # Act
        file.write(f'act {", ".join([str(x) for x in acts])};\n\n')

        # Proc
        file.write('proc ')
        for line in proc_lines:
            file.write(f'{line}\n')

        file.write('\n')

        # Init
        file.write(init_line)

def mealy2mcrl2nointermediate(fsm: MealyMachine, path):

    states = fsm.get_states()

    # Collect the actions performed to put into the act section of the mcrl2 file
    acts = set()

    # Collect the lines to go in the proc section of the mcrl2 file
    proc_lines = []

    # We also need the initial state, for the init line in the mcrl2 file
    init_line = f'init {fsm.initial_state.name};'

    for state in states:
        # Build the line for this state
        state_line = f'{state.name} = '
        first = True

        for action, (next_state, output) in state.edges.items():
            # Keep track of actions
            acts.add(action)
            acts.add(output)

            state_line += f'{" + " if not first else ""}{action}.{output}.{next_state.name}'

            first = False

        if len(state.edges) == 0:
            state_line += 'delta'

        state_line += ';'

        proc_lines.append(state_line)

    with open(path, 'w') as file:
        # Act
        file.write(f'act {", ".join([str(x) for x in acts])};\n\n')

        # Proc
        file.write('proc ')
        for line in proc_lines:
            file.write(f'{line}\n')

        file.write('\n')

        # Init
        file.write(init_line)


if __name__ == "__main__":
    s1 = MealyState('s1')
    s2 = MealyState('s2')
    s3 = MealyState('s3')

    s1.add_edge('a', 'nice', s2)
    s1.add_edge('b', 'B', s1)
    s2.add_edge('a', 'nice', s3)
    s2.add_edge('b', 'back_lol', s1)
    s3.add_edge('a', 'A', s3)
    s3.add_edge('b', 'B', s1)

    mm = MealyMachine(s1)

    mealy2mcrl2nointermediate(mm, 'test.mcrl2')


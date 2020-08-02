import random

from suls.mealymachine import MealyState, MealyMachine
from util.distinguishingset import get_dset_outputs, check_distinguishing_set
from util.minsepseq import get_distinguishing_set

def MakeRandomMealyMachine(n_states, A_in, A_out):
    states = [MealyState(f's{x + 1}') for x in range(n_states)]

    def get_reachable(start_state, states):
        to_visit = [start_state]
        visited = []

        while len(to_visit) > 0:
            cur_state = to_visit.pop()
            if cur_state not in visited:
                visited.append(cur_state)

            for action, (other_state, output) in cur_state.edges.items():
                if other_state not in visited and other_state not in to_visit:
                    to_visit.append(other_state)

        return visited, list(set(states).difference(set(visited)))

    def fix_missing(states):
        for state in states:
            for a in A_in:
                if a not in state.edges.keys():
                    state.add_edge(a, "error", state)


    reached, unreached = get_reachable(states[0], states)
    while len(unreached) > 0:
        x = random.choice(reached)
        y = random.choice(unreached)
        a = random.choice(A_in)
        o = random.choice(A_out)

        x.add_edge(a, o, y, override=True)

        reached, unreached = get_reachable(states[0], states)

    fix_missing(states)

    return MealyMachine(states[0])

def minimize(mm: MealyMachine):
    dset = get_distinguishing_set(mm)
    dset_outputs = get_dset_outputs(mm, dset)

    # Find non-unique states:
    state_map = {}
    for state, outputs in dset_outputs.items():
            if outputs not in state_map:
                state_map[outputs] = [state]
            else:
                state_map[outputs].append(state)

    for outputs, states in state_map.items():
        if len(states) > 1:
            og_state = states[0]
            rest_states = states[1:]

            states = mm.get_states()
            for state in states:
                for action, (other_state, output) in state.edges.items():
                    if other_state in rest_states:
                        state.edges[action] = og_state, output

    return mm

if __name__ == "__main__":
    A = ['a', 'b', 'c']
    O = ['1', '2', '3']
    mm = MakeRandomMealyMachine(200, A, O)
    mm.render_graph()

    dset = get_distinguishing_set(mm)
    check_distinguishing_set(mm, dset)

    mm = minimize(mm)
    dset = get_distinguishing_set(mm)
    check_distinguishing_set(mm, dset)
    mm.render_graph()



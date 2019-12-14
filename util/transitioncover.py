import tempfile
from collections import deque
from suls.mealymachine import MealyMachine, MealyState
from pathlib import Path

def get_state_cover_set(fsm):
    alphabet = fsm.get_alphabet()
    states = fsm.get_states()
    initial_state = fsm.initial_state

    paths = []
    to_visit = deque([((), initial_state)])
    visited = []

    while len(to_visit) > 0:

        if set(states) == set(visited):
            break

        cur_path, cur_state = to_visit.popleft()
        visited.append(cur_state)
        paths.append(cur_path)

        for a in alphabet:
            next_state = cur_state.next_state(a)
            if next_state not in visited:
                if len(to_visit) > 0:
                    if next_state not in list(zip(*to_visit))[1]:
                        to_visit.append((cur_path + (a,), next_state))
                else:
                    to_visit.append((cur_path + (a,), next_state))

    return set(paths)

def get_non_crashing_cover_set(fsm: MealyMachine):
    scs = get_state_cover_set(fsm)
    non_crashing = set()
    for seq in scs:
        fsm.reset()
        output = fsm.process_input(seq)
        if (output is not None) and ("error" not in output):
            non_crashing.add(seq)
    return non_crashing

# Saves a cover set to separate files for feeding to afl
def save_cover_set(cs, path):
    p = Path(path)
    assert p.is_dir(), f"{path} is not a directory"

    for idx, seq in enumerate(cs):
        q = p / f'{idx}.txt'
        with q.open('w') as f:
            for a in seq:
                f.write(f'{a} ')
            f.write('0')



# Do we need state cover or transition cover??
# TODO
def get_transition_cover_set(fsm):
    pass
    states = fsm.get_states()
    alphabet = fsm.get_alphabet()

if __name__ == "__main__":
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

    mm = MealyMachine(s1)

    mm.render_graph(tempfile.mktemp('.gv'))

    print(get_state_cover_set(mm))
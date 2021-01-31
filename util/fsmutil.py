from suls.mealymachine import MealyMachine
from util.transitioncover import get_state_cover_set

def get_error_access_sequences(fsm: MealyMachine):
    acc_seqs = get_state_cover_set(fsm)
    assert len(fsm.get_states()) == len(acc_seqs)

    error_acc_seqs = set()

    for acc_seq in acc_seqs:
        fsm.reset()
        fsm.process_input(acc_seq)

        # If there is a self transition with error output, this is an error state
        cur_state = fsm.state
        for action, (next_state, output) in cur_state.edges.items():
            if next_state == cur_state and 'error' in output:
                error_acc_seqs.add((acc_seq, output))
                continue

    return error_acc_seqs

def get_states_w_acc_seq(fsm: MealyMachine):
    to_visit = [(tuple(), fsm.initial_state)]
    visited = []
    acc_seqs = []

    while len(to_visit) > 0:
        cur_acc_seq, cur_state = to_visit.pop(0)

        if cur_state not in visited:
            visited.append(cur_state)
            acc_seqs.append(cur_acc_seq)

        for action, (other_state, output) in cur_state.edges.items():
            states_to_visit = list(zip(*to_visit))[1] if len(to_visit) > 0 else []
            if other_state not in visited and other_state not in states_to_visit:
                to_visit.append((cur_acc_seq + (action,), other_state))

    return visited, acc_seqs

def get_states_with_acc_sequences(hypothesis: MealyMachine):
    to_visit = [(tuple(), hypothesis.initial_state)]
    visited = []

    while len(to_visit) > 0:
        cur_sequence, cur_state = to_visit.pop()

        visited_states = list(zip(*visited))[1] if len(visited) > 1 else []

        if cur_state not in visited_states:
            visited.append((cur_sequence, cur_state))

        for action, (other_state, output) in cur_state.edges.items():
            to_visit_states = list(zip(*to_visit))[1] if len(to_visit) > 1 else []
            if other_state not in visited_states and other_state not in to_visit_states:
                to_visit.append((cur_sequence + (action,), other_state))

    return visited

def split_on_acc_seq_len(acc_seqs_and_states, length):
    shorter = list(filter(lambda x: len(x[0]) <= length, acc_seqs_and_states))
    longer = list(filter(lambda x: len(x[0]) > length, acc_seqs_and_states))
    return shorter, longer


def remove_connections_to(states_to_remove, hypothesis):
    states = hypothesis.get_states()
    for state in states:
        edges_to_remove = []
        for action, (other_state, output) in state.edges.items():
            if other_state in states_to_remove:
                edges_to_remove.append(action)
        for action in edges_to_remove:
            del state.edges[action]

    return hypothesis

def shorten_hyp(hyp, max_len):
    acc_seqs_w_states = get_states_with_acc_sequences(hyp)
    shorter, longer = split_on_acc_seq_len(acc_seqs_w_states, max_len)
    longer_states = list(zip(*longer))[1]
    remove_connections_to(longer_states, hyp)

if __name__ == '__main__':
    path = '/home/tom/projects/lstar/experiments/learningfuzzing/hypotheses/afl_plain/Problem12/2020-08-04_14:14:58/Problem12_hyp_264_1859s.dot'
    from util.savehypothesis import loadhypothesis

    fsm = loadhypothesis(path)

    states, acc_seqs = get_states_w_acc_seq(fsm)

    # err_acc_seqs = get_error_access_sequences(fsm)

    for x in acc_seqs:
        print(x)

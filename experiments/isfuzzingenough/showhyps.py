from suls.mealymachine import MealyMachine
from util.savehypothesis import loadhypothesis

fuzz_hyp = "/home/tom/projects/lstar/experiments/isfuzzingenough/hypotheses/Problem12/2020-11-30_13:25:12/Problem12_hyp_21_424s.dot"
wmethod_hyp = "/home/tom/projects/lstar/experiments/isfuzzingenough/hypotheses/Problem12_wmethod/2020-11-30_16:53:58/Problem12_hyp_180_338s.dot"

w = loadhypothesis(wmethod_hyp)

f = loadhypothesis(fuzz_hyp)

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


def tag_nodes(acc_seq_and_states, acc_seqs_to_tag, attribute):
    attributes = {}
    for acc_seq, state in acc_seq_and_states:
        if acc_seq in acc_seqs_to_tag:
                attributes[state] = attribute
    return attributes

maxlen = 10
shorten_hyp(w, maxlen)
shorten_hyp(f, maxlen)

special_path = [tuple(['7'] * i) for i in range(maxlen)]

w.render_graph(
    filename="wmethodgraph",
    format="png",
    render_options={
        'ignore_self_edges': ['error', 'invalid'],
        'node_attributes': tag_nodes(
            get_states_with_acc_sequences(w),
            special_path,
            {'color': '#d5e8d4'}
        )
    }
)
f.render_graph(
    filename="fuzzgraph",
    format="png",
    render_options={
        'ignore_self_edges': ['error', 'invalid'],
        'node_attributes': tag_nodes(
            get_states_with_acc_sequences(f),
            special_path,
            {'color': '#d5e8d4'}
        )
    }
)

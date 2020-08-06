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

if __name__ == '__main__':
    path = '/home/tom/projects/lstar/experiments/learningfuzzing/hypotheses/afl_plain/Problem12/2020-08-04_14:14:58/Problem12_hyp_264_1859s.dot'
    from util.savehypothesis import loadhypothesis

    fsm = loadhypothesis(path)

    err_acc_seqs = get_error_access_sequences(fsm)

    for x in err_acc_seqs:
        print(x)

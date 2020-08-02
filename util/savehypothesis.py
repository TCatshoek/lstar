from pathlib import Path
from graphviz import Digraph
from datetime import datetime
from util.dotloader import load_mealy_dot, hyp_mealy_parser
# Returns a handler function to save hypotheses in the given directory
def savehypothesis(save_dir, save_prefix):
    # Ensure save directory exists
    Path(save_dir).mkdir(parents=True, exist_ok=True)

    # Add containing directory labeled with time
    cur_dir_name = datetime.now().strftime('%Y-%m-%d_%H:%M:%S')
    cur_dir = Path(save_dir).joinpath(cur_dir_name)
    cur_dir.mkdir()

    def save(hyp):
        # Count files so we can number ours
        file_count = len(list(Path(cur_dir).glob("*.dot"))) + 1

        # Gather states
        states = hyp.get_states()
        initial_state = hyp.initial_state

        file_name = f'{save_prefix}_hyp_{file_count + 1}_{len(states)}s.dot'

        g = Digraph('G', filename=Path(cur_dir).joinpath(file_name))
        g.attr(rankdir='LR')

        # Hacky way to draw start arrow pointing to first node
        # g.attr('node', shape='none')
        g.node('__start0', label='', _attributes={'height': '0', 'width': '0', 'shape': 'none'})

        for state in states:
            g.node(f'{state.name}')

        for state in states:
            for action, (next_state, output) in state.edges.items():
                g.edge(state.name, next_state.name, label=f'{action}/{output}')

        g.edge('__start0', f'{initial_state.name}')

        g.save()

    return save

# Convenience function to also load the saved hypotheses back into mealy machines
def loadhypothesis(path):
    return load_mealy_dot(path, hyp_mealy_parser)

if __name__ == "__main__":
    loadhypothesis(
        '/home/tom/projects/lstar/experiments/learningfuzzing/hypotheses/Problem1/2020-08-01_15:03:32/Problem1_hyp_1_3s.dot')
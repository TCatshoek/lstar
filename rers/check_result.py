import re

from suls.mealymachine import MealyMachine, MealyState


def parse_csv(path):
    reachable = set()
    unreachable = set()

    with open(path, 'r') as file:
        while (line := file.readline()) and line is not None:
            #print('line', line)
            try:
                state, is_reachable = line.strip().split(',')
                is_reachable = is_reachable.strip()
                state = state.strip()
            except ValueError:
                line = line.strip('\n')
                state, is_reachable = line.strip().split('\t')

            if is_reachable == "true":
                reachable.add(int(state))
            else:
                unreachable.add(int(state))

    return reachable, unreachable

def get_reached_error_states(fsm: MealyMachine):
    reached = set()
    states = fsm.get_states()
    for state in states:
        outputs = list(zip(*state.edges.values()))[1]
        for output in outputs:
            if (match := re.search('error_([0-9]*)', output)) is not None:
                reached.add(int(match.group(1)))
    return reached

def check_result(fsm: MealyMachine, solution_path):
    reachable, unreachable = parse_csv(solution_path)
    reached = get_reached_error_states(fsm)

    if len(reachable.difference(reached)) > 0:
        print("Not reached", reachable - reached)
        print("Falsely reached", reached - reachable)
        return False
    else:
        print("Reached everything!")
        return True

if __name__ == '__main__':
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

    s5.add_edge('a', 'error_10', s5)
    s5.add_edge('b', 'error_10', s5)

    mm = MealyMachine(s1)

    print(get_reached_error_states(mm))


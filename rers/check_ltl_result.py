
def parse_answers(path):
    with open(path, 'r') as f:
        answers = [x.split(',')[1].strip() for x in f.readlines()]
    return answers

def check_result(ltl_results, solutions_path):
    solutions = parse_answers(solutions_path)
    answers = [x[1] for x in ltl_results]

    assert len(solutions) == len(answers)

    correct = 0
    incorrect = 0
    for i in range(len(solutions)):
        if solutions[i] == answers[i]:
            correct += 1
        else:
            incorrect += 1
            print(f'Rule #{i} incorrect. Answer: {answers[i]}, Solution: {solutions[i]}')

    print(f"Score: {correct}/{correct + incorrect}")

    return correct, correct + incorrect
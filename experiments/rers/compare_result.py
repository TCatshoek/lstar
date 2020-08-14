from rers.check_ltl_result import compare_results

p1 = "/home/tom/projects/lstar/experiments/rers/results/SeqLtlRers2019/Problem7.csv"
p2 = "/home/tom/projects/lstar/rers/SeqLtlRers2019/Problem7/constraints-solution-Problem7.txt"

compare_results(p1, p2)

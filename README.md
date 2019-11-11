# lstar

My implementation of the L* algorithm by Dana Angluin. Also contains a modified version that learns mealy machines instead of DFAs.

Currently the only available equivalence checkers are bruteforce, and random walk. W-method is on the todo list.

#### Installation
Dependencies `pip install graphviz tabulate`

Please make sure the `dot` executable is in your path.
#### Simple example
```python
# Set up a SUT using regex
sm = RegexMachine('(bb)*(aa)*(bb)*')

# We are using the brute force equivalence checker
eqc = BFEquivalenceChecker(sm, max_depth=15)

# Set up the teacher, with the system under learning and the equivalence checker
teacher = Teacher(sm, eqc)

# Set up the learner who only talks to the teacher
learner = DFALearner(teacher)

# Get the learners hypothesis
hyp = learner.run()

# Draw the learned dfa
hyp.render_graph('dfa.gv')
```
For the regular expression `(bb)*(aa)*(bb)*` the following dfa is learned:
![simple dfa](https://i.imgur.com/vlqQcCH.png)
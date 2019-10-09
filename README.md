# lstar

My implementation of the L* algorithm by Dana Angluin.

Example run on a very simple state machine can be found in `main.py`

The only equivalence checker currently implemented just bruteforces it's way through all possible input combinations and is probably too slow for any real world problems.

####Installation
The only dependency right now is graphviz `pip install graphviz`

Please make sure the `dot` executable is in your path.
####Simple example
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
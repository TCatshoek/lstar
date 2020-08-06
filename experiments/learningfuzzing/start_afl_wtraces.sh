#!/bin/bash

SESSION_NAME=afl_plain
PROBLEM_SET=TrainingSeqReachRers2019
HORIZON=15
DIR=/home/tom/projects/lstar/experiments/learningfuzzing

./prepare_training.sh

tmux new-session -d -s $SESSION_NAME

att() {
	[ -n "${TMUX:-}" ] &&
	tmux switch-client -t "=$SESSION_NAME" ||
	tmux attach-session -t "=$SESSION_NAME"
}

# start the learners
for PROBLEM in Problem11 Problem12 Problem13
do
	tmux new-window -d -t "=$SESSION_NAME" -n $PROBLEM -c $DIR
	tmux send-keys -t "=$SESSION_NAME:=$PROBLEM" "python ./run_experiment_afl_wtraces.py $PROBLEM_SET $PROBLEM --horizon $HORIZON" Enter
done

# start the fuzzers
for d in "$PROBLEM_SET"/*/
do
	tmux new-window -d -t "=$SESSION_NAME" -n ${d%/} -c $DIR/$d
	tmux send-keys -t "=$SESSION_NAME:=${d%/}" "afl-fuzz -i input -o output -M $(basename ${d%/}) ./$(basename ${d%/})" Enter
done

att

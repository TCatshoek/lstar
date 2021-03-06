#!/bin/bash

tmux new-session -d -s libfuzzer

att() {
        [ -n "${TMUX:-}" ] &&
        tmux switch-client -t '=libfuzzer' ||
        tmux attach-session -t '=libfuzzer'
}

BASE_DIR=/home/tom/afl/thesis_benchmark/libFuzzer/TrainingSeqReachRers2019/

for d in */
do
        tmux new-window -d -t '=libfuzzer' -n ${d%/} -c "$BASE_DIR"$d
        tmux send-keys -t "=libfuzzer:=${d%/}" "./${d%/}_fuzz corpus -dict=./dict" Enter
done

att


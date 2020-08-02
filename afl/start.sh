#!/bin/bash

tmux new-session -d -s afl

att() {
	[ -n "${TMUX:-}" ] &&
	tmux switch-client -t '=afl' ||
	tmux attach-session -t '=afl'
}


for d in */
do
	tmux new-window -d -t '=afl' -n ${d%/} -c $d
	tmux send-keys -t "=afl:${d%/}" "cd afl/$d" Enter
	tmux send-keys -t "=afl:=${d%/}" "afl-fuzz -i input -o output ~/rers2020/SeqReachabilityRers2020/${d}${d%/}" Enter
done

att

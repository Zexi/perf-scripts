#!/bin/bash

help() {
    echo "usage: $0 <session name> <command> <start|stop|restart>"
    exit 1
}

start_tmux() {
    local sn="$1"
    local cmd="$2"
    local swn="auto_run"
    tmux new-session -d -s "$sn" -n "$swn"
    tmux send-keys -t "$sn" "$cmd" C-m
}

stop_tmux() {
    local sn="$1"
    tmux has-session -t "$sn" &> /dev/null
    if [ $? -eq 0 ]; then
        tmux kill-session -t "$sn"
    fi
}

if [ $# -le 2 ]; then
    help
else
    SESSIONNAME="$1"
    CMD="$2"
    ACT="$3"
fi

case "$ACT" in
    start)
        start_tmux $SESSIONNAME $CMD
        ;;
    stop)
        stop_tmux $SESSIONNAME
        ;;
    restart)
        stop_tmux $SESSIONNAME
        start_tmux $SESSIONNAME $CMD
        ;;
    *)
        help
esac

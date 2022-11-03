#!/bin/bash

graceful_exit() {
    # include this line: trap graceful_exit TERM INT HUP
    local timeout=${1:-${GRACEFUL_EXIT_TIMEOUT:-4}}
    local list=""
    for c in $(ps -o pid= --ppid $$); do
        # request children shutdown
        kill -0 ${c} 2>/dev/null && kill -TERM ${c} && list="$list $c" || true
    done
    if [ -n "$list" ]; then
        # schedule hard kill after timeout
        (sleep ${timeout}; kill -9 ${list} 2>/dev/null || true) &
        local killer=${!}
        wait ${list} 2>/dev/null || true
        # children exited gracefully - cancel timer
        sleep 0.5 && kill -9 ${killer} 2>/dev/null && list="" || true
    fi

    [ -z "$list" ] && exit 0 || exit 1
}

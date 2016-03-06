#!/bin/sh

read_env_vars()
{
	[ -f "$TMP/env.yaml" ] || return 0

	local key
	local val

	while read key val
	do
		[ "${key%[a-zA-Z0-9_]:}" != "$key" ] || continue
		key=${key%:}
		export "$key=$val"
	done < $TMP/env.yaml

	return 0
}

wakeup_pre_test()
{
	mkdir $TMP/wakeup_pre_test-once 2>/dev/null || return

	$SRC/monitors/event/wakeup pre-test
	sleep 1
	date '+%s' > $TMP/start_time
}

check_exit_code()
{   
    local exit_code=$1
    [ "$exit_code" = 0  ] && return

    echo "${program}.exit_code.$exit_code: 1"   >> $RESULT_ROOT/last_state
    echo "exit_fail: 1"             >> $RESULT_ROOT/last_state
    exit "$exit_code"
}

run_monitor()
{
    "$@"
}

run_setup()
{
    local program=${1##*/}
    [ "$program" = 'wrapper' ] && program=$2
    "$@"
    check_exit_code $?
    read_env_vars
}

run_test()
{
    local program=${1##*/}
    [ "$program" = 'wrapper' ] && program=$2
    wakeup_pre_test
    "$@"
    check_exit_code $?
}

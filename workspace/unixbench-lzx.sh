#!/bin/sh

export_top_env()
{
	export testcase='unixbench'
	export category='benchmark'
	export enqueue_time='2016-03-04 19:20:27 +0800'

	[ -n "$SRC" ] ||
	export SRC=/lkp/${user:-lkp}/src
}

run_job()
{
	echo $$ > $TMP/run-job.pid

	. $SRC/lib/job.sh
	. $SRC/lib/env.sh

	export_top_env

	run_test $SRC/tests/wrapper unixbench
}

extract_stats()
{
	$SRC/stats/wrapper unixbench

	$SRC/stats/wrapper time unixbench.time
	$SRC/stats/wrapper time
	$SRC/stats/wrapper dmesg
	$SRC/stats/wrapper kmsg
	$SRC/stats/wrapper stderr
	$SRC/stats/wrapper last_state
}

"$@"

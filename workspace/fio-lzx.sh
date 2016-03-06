#!/bin/sh

export_top_env()
{
	export testcase='fio-vm'
	export category='benchmark'
	export enqueue_time='2016-03-04 19:11:04 +0800'

	[ -n "$SRC" ] ||
	export SRC=/lkp/${user:-lkp}/src
}

run_job()
{
	echo $$ > $TMP/run-job.pid

	. $SRC/lib/job.sh
	. $SRC/lib/env.sh

	export_top_env

	export ioengine='psync'
	export bs='4k'
	export size='100%'
	run_test $SRC/tests/wrapper fio
	unset ioengine
	unset bs
	unset size
}

extract_stats()
{
	$SRC/stats/wrapper time fio.time
	$SRC/stats/wrapper time
	$SRC/stats/wrapper dmesg
	$SRC/stats/wrapper kmsg
	$SRC/stats/wrapper stderr
	$SRC/stats/wrapper last_state
}

"$@"

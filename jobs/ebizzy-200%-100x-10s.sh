#!/bin/sh

export_top_env()
{
	export testcase='ebizzy'
	export enqueue_time='2016-03-03 21:00:25 +0800'

#	[ -n "$SRC" ] ||
#	export SRC=/lkp/${user:-lkp}/src
}

run_job()
{
	echo $$ > $TMP/run-job.pid

	. $SRC/lib/job.sh
	. $SRC/lib/env.sh

	export_top_env

	default_monitors()
	{
		export wait='pre-test'

		run_monitor $SRC/monitors/wrapper uptime
		run_monitor $SRC/monitors/wrapper iostat
		run_monitor $SRC/monitors/wrapper vmstat
		run_monitor $SRC/monitors/wrapper numa-numastat
		run_monitor $SRC/monitors/wrapper numa-vmstat
		run_monitor $SRC/monitors/wrapper numa-meminfo
		run_monitor $SRC/monitors/wrapper proc-vmstat
		export interval=10
		run_monitor $SRC/monitors/wrapper proc-stat
		unset interval

		run_monitor $SRC/monitors/wrapper meminfo
		run_monitor $SRC/monitors/wrapper slabinfo
		run_monitor $SRC/monitors/wrapper interrupts
		run_monitor $SRC/monitors/wrapper lock_stat
		run_monitor $SRC/monitors/wrapper latency_stats
		run_monitor $SRC/monitors/wrapper softirqs
		run_monitor $SRC/monitors/wrapper bdi_dev_mapping
		run_monitor $SRC/monitors/wrapper diskstats
		run_monitor $SRC/monitors/wrapper nfsstat
		run_monitor $SRC/monitors/wrapper cpuidle
		run_monitor $SRC/monitors/wrapper cpufreq-stats
		run_monitor $SRC/monitors/wrapper turbostat
		run_monitor $SRC/monitors/wrapper pmeter
		export interval=60
		run_monitor $SRC/monitors/wrapper sched_debug
		unset interval
	}
	#default_monitors &

	run_setup $SRC/setup/nr_threads '200%'

	run_setup $SRC/setup/iterations '1x'

	export duration='10s'
	run_test $SRC/tests/wrapper ebizzy
	unset duration

	wait
}

extract_stats()
{
	$SRC/stats/wrapper uptime
	$SRC/stats/wrapper iostat
	$SRC/stats/wrapper vmstat
	$SRC/stats/wrapper numa-numastat
	$SRC/stats/wrapper numa-vmstat
	$SRC/stats/wrapper numa-meminfo
	$SRC/stats/wrapper proc-vmstat
	$SRC/stats/wrapper meminfo
	$SRC/stats/wrapper slabinfo
	$SRC/stats/wrapper interrupts
	$SRC/stats/wrapper lock_stat
	$SRC/stats/wrapper latency_stats
	$SRC/stats/wrapper softirqs
	$SRC/stats/wrapper diskstats
	$SRC/stats/wrapper nfsstat
	$SRC/stats/wrapper cpuidle
	$SRC/stats/wrapper turbostat
	$SRC/stats/wrapper sched_debug
	$SRC/stats/wrapper ebizzy

	$SRC/stats/wrapper time ebizzy.time
	$SRC/stats/wrapper time
	$SRC/stats/wrapper kmsg
	$SRC/stats/wrapper dmesg
	$SRC/stats/wrapper stderr
	$SRC/stats/wrapper last_state
}

"$@"

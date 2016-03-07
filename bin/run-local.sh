#!/bin/bash

[ -n "$SRC" ] || export SRC=$(dirname $(dirname $(readlink -e -v $0)))
export TMP=/tmp/perf-test/tmp
export PATH=$PATH:$SRC/bin
export BENCHMARK_ROOT=/tmp/perf-test/benchmarks

usage()
{
    cat <<EOF
Usage: $0 [-o RESULT_ROOT] JOB_SCRIPT

options:
    -o RESULT_ROOT          dir for storing all test results
EOF
    exit 1
}

while getopts "o:" opt
do
    case $opt in
    o ) opt_result_root="$OPTARG" ;;
    ? ) usage ;;
    esac
done

shift $(($OPTIND-1))
job_script=$1
[ -n "$job_script" ] || usage
job_script=$(readlink -e -v $job_script)

if [ ${job_script#*.} = 'yaml' ]; then
    job_script_basename=$(basename $job_script)
    convert_job_path="$SRC/workspace/${job_script_basename%.*}.sh"
    $SRC/sbin/job2sh -j $job_script > $convert_job_path
    if [ $? -eq 0 ]; then
        chmod a+x $convert_job_path
        job_script=$convert_job_path
    else
        echo "Convert $job_script to $convert_job_path Failed."
        exit 1
    fi
fi

if [ -z $opt_result_root ]; then
    opt_result_root="/tmp/result/$(basename $job_script)"
    RESULT_ROOT=$opt_result_root
    mkdir -p -m 02775 $RESULT_ROOT
else
    mkdir -p -m 02775 $opt_result_root
    export RESULT_ROOT=$(readlink -e -v $opt_result_root)
fi

export RESULT_ROOT
export TMP_RESULT_ROOT=$RESULT_ROOT
rm -rf $TMP
mkdir $TMP



$job_script run_job
$SRC/bin/post-run
#$SRC/monitors/event/wakeup job-finished


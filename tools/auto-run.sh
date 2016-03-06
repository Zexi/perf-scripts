#!/bin/bash

if [ $(id -u) != 0 ]; then
    echo "This script must be run as root" 1>&2
    exit 1
fi

script_name=$(basename $0)

[ -n "$SRC" ] || export SRC=$(dirname $(dirname $(readlink -e -v $0)))

$SRC/bin/install.sh $SRC/jobs/fio-lzx.yaml
$SRC/bin/run-local.sh $SRC/workspace/fio-lzx.sh

$SRC/bin/install.sh $SRC/jobs/unixbench.yaml
$SRC/bin/run-local.sh $SRC/workspace/unixbench-lzx.sh

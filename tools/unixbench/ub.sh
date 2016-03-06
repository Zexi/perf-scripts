#!/bin/bash

if [ $(id -u) != 0 ]; then
    echo "Please run $0 as root."
    exit 1
fi

source ../../lib/git.sh

git_clone_update https://github.com/kdlucas/byte-unixbench.git
yum install -y gcc gcc-c++ make libX11-devel mesa-libGL-devel libXext-devel perl-Time-HiRes

cd byte-unixbench/UnixBench/
make
./Run | tee ../../UnixBench-`hostname`.txt


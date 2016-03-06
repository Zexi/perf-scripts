#!/bin/bash

yum install -y fio
fio --filename=/dev/vdc --direct=1 --rw=read --ioengine=psync --size=100% --bs=1024k --runtime=30 --group_reporting --name=read | tee io-`hostname`-throughput-read.txt
fio --filename=/dev/vdc --direct=1 --rw=write --ioengine=psync --size=100% --bs=1024k --runtime=30 --group_reporting --name=write | tee io-`hostname`-throughput-write.txt
fio --filename=/dev/vdc --direct=1 --ioengine=libaio --iodepth=32 --thread --numjobs=1 --rw=randread --bs=4k --size=100% --runtime=30s --group_reporting --name=randread | tee io-`hostname`-random-read.txt
fio --filename=/dev/vdc --direct=1 --ioengine=libaio --iodepth=32 --thread --numjobs=1 --rw=randwrite --bs=4k --size=100% --runtime=30s --group_reporting --name=randwrite | tee io-`hostname`-random-write.txt


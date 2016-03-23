# Introduction

[perf-scripts](https://github.com/Zexi/perf-scripts) is used to auto test Linux performance, which include install and run benchmarks, collect the results, compare testcase results with testboxs and display the difference in web.

Benchmarks include: fio, sysbench, mbw, superpi, etc.

The main test processes and methods are reference from [lkp-tests](https://github.com/fengguang/lkp-tests), and I simplified a lot of steps because the aim is to compare different testbox(such as vm and docker) performance results now.

# Prerequisites

As for now, I only test it in Centos7, the next step is to support other linux distrobution (such as: ubuntu, fedora, archlinux).

Otherwise, scripts are written by python 2.7 and bash, you should get the environment of python 2.7 to run.

# Getting started

* Clone the repository:

```sh
	$ git clone https://github.com/Zexi/perf-scripts
	$ cd perf-scripts
```

* Install packages for one job

```sh
	# chose one job to run, for example: jobs/sysbench.yaml
	$ ls jobs
	./bin/pst install jobs/sysbench.yaml
```

* Run one atomic job

```sh
	$ ./bin/pst split -j jobs/sysbench.yaml -o .
	# output is:
	# jobs/sysbench.yaml => ./sysbench-cpu.yaml	# sysbench cpu_max_prime test
	# jobs/sysbench.yaml => ./sysbench-oltp.yaml	# sysbench mysql test

	$ ./bin/pst run -j ./sysbench-cpu.yaml		# run sysbench cpu_max_prime test
```

* Check results

```sh
	# result path form: testcase/params/testbox/rootfs/commit/start_time
	# for example: sysbench cpu max prime test results
	$ ls /results/sysbench/cpu/vbox-centos/centos/3.10.0-327.10.1.el7.x86_64/2016-03-23-22:10:19
	job.sh    reproduce.sh  sysbench.json  sysbench.time.json  time.json
	job.yaml  sysbench      sysbench.time  time

	# you can check each of those files, e.g. the 'sysbench' file include outputs from sysben benchmark
	# the 'sysbench.json' file include extracted part of concern:
	$ cat /results/sysbench/cpu/vbox-centos/centos/3.10.0-327.10.1.el7.x86_64/2016-03-23-22:10:19/sysbench.json
	{
		"sysbench.cpu_time": [
		26.2671
		]
	}
```

# Auto-run and web display

I have written a simple auto run scprit(**bin/auto-run.py**) and web interface(**server/server.py**) based on tornado,
 **auto-run.py** will run a group specified jobs during the specified time interval and upload each job test results to server.
**server.py** will use rrdtool to collect testcase result data and gerate pictures.

* bin/auto-run.py and etc/auto-run.yaml

```sh
	# etc/auto-run.yaml specify time interval, server info, group of jobs
	$ cat etc/autorun_conf.yaml
	runtime: 300			# run jobs per 5 mins

	server:
	  hostname: 172.30.26.228	# server IP
	  port: 8080			# port
	  res: results			# post request url

	jobs:				# specify group of test jobs
	  - sysbench			# before run the group of jobs, remember use **bin/pst install jobs/xxx.yaml**
	  - superpi
	  - ping
	  - mbw

	# run auto-run.py
	$ bin/auto-run.py
```

**bin/auto-run.py** will read the **etc/auto-run.yaml** config items, then run group of jobs and upload results to server.

* server.py collects results and display

The situation of mine is running server.py in a remote server, then choose two testboxs to auto run a group of jobs and upload each results to server.
You can run server in localhost，remember change the IP:127.0.0.1 in  **etc/auto-run.yaml**, the default server port is 8080.

```sh
	# run server.py
	$ ./server/server.py
```

Afterwards, **bin/auto-run.py** will auto run a group of jobs and upload results to server, then open http://$server_ip:$port in browser you can see different testcase picture.

Server display screenshot show below：
![Result Img](http://chuantu.biz/t2/33/1458762529x1035372911.png)

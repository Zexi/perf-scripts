#!/usr/bin/env python

import os
import sys
import subprocess

SRC = '/perf-scripts'
LIB_PATH = SRC + '/lib'
sys.path.insert(0, LIB_PATH)
import common

conf_file = SRC + '/etc/autorun_conf.yaml'
conf_dict = common.load_conf(conf_file)
conf_dict['runtime'] = int(os.getenv('RUNTIME', 300))
conf_dict['server']['hostname'] = os.getenv('SERVER_IP', '127.0.0.1')
conf_dict['server']['port'] = os.getenv('SERVER_PORT', 8080)
conf_dict['server']['res'] = os.getenv('SERVER_RES', 'results')

jobs_env = os.getenv('TBOX_JOBS', '').split(';')
jobs_env = [x for x in jobs_env if x]

jobs = conf_dict['jobs']

jobs = list(set(jobs + jobs_env))
conf_dict['jobs'] = jobs

print "--------------------------------"
print "Jobs been run: %s" % jobs
print "--------------------------------"
common.unify_localtime()
common.save_yaml(conf_file, conf_dict)
subprocess.call("/perf-scripts/bin/auto-install.py", shell=True)
subprocess.call("service mysql start", shell=True)
subprocess.call("/perf-scripts/bin/auto-run.py", shell=True)

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
conf_dict['runtime'] = os.getenv('RUNTIME', 300)
conf_dict['server']['hostname'] = os.getenv('SERVER_IP', '127.0.0.1')
conf_dict['server']['port'] = os.getenv('SERVER_PORT', 8080)
conf_dict['server']['res'] = os.getenv('SERVER_RES', 'results')
jobs_env = os.getenv('TBOX_JOBS', '').split(';')
jobs = conf_dict['jobs']

jobs = set(jobs + jobs_env)

print "--------------------------------"
print "Jobs been run: %s" % jobs
print "--------------------------------"
common.save_yaml(conf_file, conf_dict)
subprocess.call("/perf-scripts/bin/auto-install.py", shell=True)
subprocess.call("/perf-scripts/bin/auto-run.py", shell=True)

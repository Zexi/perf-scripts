#!/usr/bin/env python

import os
import sys
import subprocess

SRC = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), os.pardir))
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
if 'sysbench' in jobs:
    # install mysql and configure it
    cmds = []
    cmds.append('echo "mysql-server-5.6 mysql-server/root_password password pass" | debconf-set-selections')
    cmds.append('echo "mysql-server-5.6 mysql-server/root_password_again password pass" | debconf-set-selections')
    cmds.append('apt-get -y install mysql-server-5.6')
    cmds.append('mysql -u root -ppass -e "create database test"')
    for cmd in cmds:
        subprocess.check_call(cmd, shell=True)

common.unify_localtime()
common.save_yaml(conf_file, conf_dict)
subprocess.call(SRC + "/bin/auto-install.py", shell=True)
